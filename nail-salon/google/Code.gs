/**
 * ネイルサロン予約 — Google 側のプログラム(Apps Script)
 *
 * 予約・ネイリスト・出勤日・メニューは、このスクリプトがついている
 * Google スプレッドシートに保存します。
 * お店の方の画面のパスワードは、スプレッドシートの「予約の設定」メニューから決めます。
 */

const TZ = 'Asia/Tokyo';
// 営業時間など(仮の値です。決まったらここを変えます)
const RULES = { open: 10 * 60, close: 19 * 60, step: 30, daysAhead: 30, deadlineHour: 18 };
const TOKEN_SECONDS = 6 * 60 * 60;   // お店の画面にログインしたままでいられる時間(6時間)
const MAX_LOGIN_FAILS = 10;          // パスワードをまちがえられる回数(超えると10分入れません)

const SHEETS = { booking: '予約', staff: 'ネイリスト', work: '出勤日', menu: 'メニュー' };
const HEADERS = {
  booking: ['予約番号', '状態', '日にち', '開始', '終了', '時間(分)', 'ネイリストID', 'ネイリスト',
            'メニューID', 'メニュー', '料金', 'お名前', '電話番号', '予約した日時', '変更・キャンセルした日時'],
  staff: ['ネイリストID', 'お名前'],
  work: ['ネイリストID', '日にち'],
  menu: ['メニューID', '名前', '時間(分)', '料金'],
};
const STATUS = { active: 'ご予約', cancelled: 'キャンセル' };

/* ===== ページを出す ===== */
function doGet() {
  return HtmlService.createHtmlOutputFromFile('index')
    .setTitle('ネイルサロン予約')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

/* ===== スプレッドシートのメニュー ===== */
function onOpen() {
  SpreadsheetApp.getUi().createMenu('予約の設定')
    .addItem('はじめの準備をする', 'menuSetup')
    .addItem('お店の画面のパスワードを決める', 'menuPassword')
    .addToUi();
}
function menuSetup() {
  const ui = SpreadsheetApp.getUi();
  const made = setupSheets_(SpreadsheetApp.getActiveSpreadsheet());
  ui.alert(made
    ? '準備ができました。見本のデータ(作り物の名前と電話番号)を入れてあります。\n次に「お店の画面のパスワードを決める」を押してください。'
    : 'すでに準備はできています。');
}
function menuPassword() {
  const ui = SpreadsheetApp.getUi();
  const r1 = ui.prompt('お店の画面のパスワード', '8文字以上で入れてください。', ui.ButtonSet.OK_CANCEL);
  if (r1.getSelectedButton() !== ui.Button.OK) return;
  const pw = r1.getResponseText();
  if (pw.length < 8) { ui.alert('パスワードは8文字以上にしてください。'); return; }
  const r2 = ui.prompt('確認', 'もう一度、同じパスワードを入れてください。', ui.ButtonSet.OK_CANCEL);
  if (r2.getSelectedButton() !== ui.Button.OK) return;
  if (r2.getResponseText() !== pw) { ui.alert('2回の入力がちがいました。もう一度お願いします。'); return; }
  setPassword_(pw);
  ui.alert('パスワードを決めました。');
}

/* ===== 準備 ===== */
function setupSheets_(spreadsheet) {
  PropertiesService.getScriptProperties().setProperty('SHEET_ID', spreadsheet.getId());
  let made = false;
  Object.keys(SHEETS).forEach(k => {
    if (!spreadsheet.getSheetByName(SHEETS[k])) {
      const sh = spreadsheet.insertSheet(SHEETS[k]);
      sh.getRange(1, 1, 1, HEADERS[k].length).setValues([HEADERS[k]]).setFontWeight('bold');
      sh.setFrozenRows(1);
      made = true;
    }
  });
  if (made) writeSample_();
  return made;
}
function setPassword_(pw) {
  const props = PropertiesService.getScriptProperties();
  const salt = Utilities.getUuid();
  props.setProperty('PW_SALT', salt);
  props.setProperty('PW_HASH', hash_(salt + pw));
}
function hash_(s) {
  return Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, s, Utilities.Charset.UTF_8)
    .map(b => ((b + 256) % 256).toString(16).padStart(2, '0')).join('');
}

/* ===== 日付 ===== */
function realNow_() { return Utilities.formatDate(new Date(), TZ, "yyyy-MM-dd'T'HH:mm"); }
function ymdAdd_(ds, n) {
  const p = ds.split('-').map(Number);
  return new Date(Date.UTC(p[0], p[1] - 1, p[2] + n)).toISOString().slice(0, 10);
}
function weekday_(ds) { const p = ds.split('-').map(Number); return new Date(Date.UTC(p[0], p[1] - 1, p[2])).getUTCDay(); }
function deadline_(date) { return ymdAdd_(date, -1) + 'T' + String(RULES.deadlineHour).padStart(2, '0') + ':00'; }
function hm_(m) { return Math.floor(m / 60) + ':' + String(m % 60).padStart(2, '0'); }
function toMin_(s) { const p = String(s).split(':').map(Number); return p[0] * 60 + (p[1] || 0); }
// お店の方がログインして「動作確認」の日時を決めているときだけ、その日時を使う
function nowFor_(opt) {
  if (opt && opt.debugNow && /^\d{4}-\d\d-\d\dT\d\d:\d\d$/.test(opt.debugNow) && checkToken_(opt.token)) {
    return { now: opt.debugNow, debug: true };
  }
  return { now: realNow_(), debug: false };
}

/* ===== スプレッドシートの読み書き ===== */
function book_() {
  const id = PropertiesService.getScriptProperties().getProperty('SHEET_ID');
  const ss = id ? SpreadsheetApp.openById(id) : SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) throw new Error('NOT_READY');
  return ss;
}
function sheet_(k) {
  const sh = book_().getSheetByName(SHEETS[k]);
  if (!sh) throw new Error('NOT_READY');
  return sh;
}
function rows_(k) {
  const sh = sheet_(k);
  const n = sh.getLastRow() - 1;
  if (n < 1) return [];
  return sh.getRange(2, 1, n, HEADERS[k].length).getDisplayValues()
    .map((r, i) => ({ r: r, row: i + 2 }))
    .filter(x => x.r[0] !== '');
}
// 入力された文字が式として動かないようにする
function safe_(v) { v = String(v); return /^[=+\-@]/.test(v) ? "'" + v : v; }
function writeRows_(k, startRow, values) {
  if (!values.length) return;
  sheet_(k).getRange(startRow, 1, values.length, HEADERS[k].length)
    .setNumberFormat('@').setValues(values.map(r => r.map(safe_)));
}
function rewrite_(k, values) {
  const sh = sheet_(k);
  const n = sh.getLastRow() - 1;
  if (n > 0) sh.getRange(2, 1, n, HEADERS[k].length).clearContent();
  writeRows_(k, 2, values);
}

function loadModel_() {
  const staff = rows_('staff').map(x => ({ id: x.r[0], name: x.r[1], workDays: [] }));
  rows_('work').forEach(x => { const s = staff.find(s => s.id === x.r[0]); if (s && x.r[1]) s.workDays.push(x.r[1]); });
  staff.forEach(s => s.workDays.sort());
  const menus = rows_('menu').map(x => ({ id: x.r[0], name: x.r[1], minutes: Number(x.r[2]) || 60, price: Number(x.r[3]) || 0 }));
  const bookings = rows_('booking').map(x => {
    const r = x.r;
    return {
      row: x.row, id: r[0], status: r[1] === STATUS.cancelled ? 'cancelled' : 'active', date: r[2],
      start: toMin_(r[3]), minutes: Number(r[5]) || 0, staffId: r[6], staffName: r[7], menuId: r[8],
      menuName: r[9], price: Number(r[10]) || 0, name: r[11], phone: r[12], createdAt: r[13], changedAt: r[14],
    };
  });
  return { staff: staff, menus: menus, bookings: bookings };
}
function bookingRow_(b) {
  return [b.id, STATUS[b.status], b.date, hm_(b.start), hm_(b.start + b.minutes), String(b.minutes), b.staffId,
          b.staffName, b.menuId, b.menuName, String(b.price), b.name, b.phone, b.createdAt || '', b.changedAt || ''];
}
function saveBooking_(b) {
  if (b.row) writeRows_('booking', b.row, [bookingRow_(b)]);
  else writeRows_('booking', sheet_('booking').getLastRow() + 1, [bookingRow_(b)]);
}
function saveStaffAndWork_(m) {
  rewrite_('staff', m.staff.map(s => [s.id, s.name]));
  const w = [];
  m.staff.forEach(s => s.workDays.forEach(d => w.push([s.id, d])));
  rewrite_('work', w);
}
function saveMenus_(m) { rewrite_('menu', m.menus.map(x => [x.id, x.name, String(x.minutes), String(x.price)])); }

function withLock_(fn) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try { return fn(); } finally { lock.releaseLock(); }
}

/* ===== 見本のデータ(名前も電話番号もすべて作り物) ===== */
function writeSample_() {
  const today = realNow_().slice(0, 10);
  const staff = [
    { id: 's1', name: '見本 さくら', pattern: [1, 2, 3, 5, 6] },
    { id: 's2', name: '見本 あおい', pattern: [0, 2, 4, 5, 6] },
  ].map(s => {
    const days = [];
    for (let i = 0; i <= 60; i++) { const d = ymdAdd_(today, i); if (s.pattern.indexOf(weekday_(d)) >= 0) days.push(d); }
    return { id: s.id, name: s.name, workDays: days };
  });
  const menus = [
    { id: 'm1', name: 'ワンカラー', minutes: 60, price: 5500 },
    { id: 'm2', name: 'グラデーション', minutes: 90, price: 6600 },
    { id: 'm3', name: 'アート(お好きなデザイン)', minutes: 120, price: 8800 },
    { id: 'm4', name: 'ケア・ジェルオフのみ', minutes: 30, price: 3300 },
  ];
  const m = { staff: staff, menus: menus };
  saveStaffAndWork_(m);
  saveMenus_(m);
  const first = (s, from) => s.workDays.find(d => d >= ymdAdd_(today, from));
  const d1 = first(staff[0], 2), d2 = first(staff[1], 3);
  const created = realNow_();
  const mk = (id, s, mn, date, start, name, phone) => ({
    id: id, status: 'active', date: date, start: start, minutes: mn.minutes, staffId: s.id, staffName: s.name,
    menuId: mn.id, menuName: mn.name, price: mn.price, name: name, phone: phone, createdAt: created, changedAt: '',
  });
  rewrite_('booking', [
    mk('N10001', staff[0], menus[0], d1, 11 * 60, '見本 花子', '09000000000'),
    mk('N10002', staff[0], menus[2], d1, 14 * 60, '見本 次郎', '08000000000'),
    mk('N10003', staff[1], menus[1], d2, 10 * 60 + 30, '見本 桃子', '07000000000'),
  ].map(bookingRow_));
}

/* ===== ルール ===== */
function checkSlot_(m, staffId, date, start, minutes, excludeId, now) {
  const today = now.slice(0, 10);
  if (!/^\d{4}-\d\d-\d\d$/.test(String(date))) throw new Error('INVALID');
  if (date < today || date > ymdAdd_(today, RULES.daysAhead)) throw new Error('OUT_OF_RANGE');
  if (now >= deadline_(date)) throw new Error('CLOSED');
  const s = m.staff.find(x => x.id === staffId);
  if (!s) throw new Error('INVALID');
  if (s.workDays.indexOf(date) < 0) throw new Error('DAY_OFF');
  start = Number(start);
  if (!(start >= RULES.open) || start + minutes > RULES.close || (start - RULES.open) % RULES.step !== 0) throw new Error('SLOT_TAKEN');
  const clash = m.bookings.some(b => b.status === 'active' && b.staffId === staffId && b.date === date && b.id !== excludeId &&
    start < b.start + b.minutes && b.start < start + minutes);
  if (clash) throw new Error('SLOT_TAKEN');
  return s;
}
function normNo_(no) {
  const d = String(no || '').replace(/[０-９]/g, c => String.fromCharCode(c.charCodeAt(0) - 0xFEE0)).replace(/[^0-9]/g, '');
  return 'N' + d;
}
function normPhone_(p) {
  return String(p || '').replace(/[０-９]/g, c => String.fromCharCode(c.charCodeAt(0) - 0xFEE0)).replace(/[^0-9]/g, '');
}
function findBooking_(m, req) {
  const no = normNo_(req && req.no), ph = normPhone_(req && req.phone);
  const b = m.bookings.find(x => x.id === no && x.phone === ph);
  if (!b || !ph) throw new Error('NOT_FOUND');
  return b;
}
function publicBooking_(b) {
  return { id: b.id, status: b.status, date: b.date, start: b.start, minutes: b.minutes, staffId: b.staffId,
           staffName: b.staffName, menuName: b.menuName, price: b.price, name: b.name, phone: b.phone };
}

/* ===== お客様の画面から呼ばれるもの ===== */
function apiPublic(opt) {
  const t = nowFor_(opt);
  const m = loadModel_();
  const today = t.now.slice(0, 10), last = ymdAdd_(today, RULES.daysAhead);
  return {
    now: t.now, debug: t.debug, rules: RULES,
    staff: m.staff.map(s => ({ id: s.id, name: s.name, workDays: s.workDays.filter(d => d >= today && d <= last) })),
    menus: m.menus,
    // ほかのお客様のお名前や電話番号は渡さない
    busy: m.bookings.filter(b => b.status === 'active' && b.date >= today)
      .map(b => ({ staffId: b.staffId, date: b.date, start: b.start, minutes: b.minutes })),
  };
}
function apiCreate(req, opt) {
  return withLock_(() => {
    const now = nowFor_(opt).now;
    const m = loadModel_();
    const menu = m.menus.find(x => x.id === req.menuId);
    if (!menu) throw new Error('INVALID');
    const name = String(req.name || '').trim().slice(0, 50);
    const phone = normPhone_(req.phone);
    if (!name || !/^0\d{9,10}$/.test(phone)) throw new Error('INVALID');
    const s = checkSlot_(m, req.staffId, req.date, req.start, menu.minutes, null, now);
    let id;
    do { id = 'N' + Math.floor(10000 + Math.random() * 90000); } while (m.bookings.some(b => b.id === id));
    const b = { id: id, status: 'active', date: req.date, start: Number(req.start), minutes: menu.minutes,
                staffId: s.id, staffName: s.name, menuId: menu.id, menuName: menu.name, price: menu.price,
                name: name, phone: phone, createdAt: realNow_(), changedAt: '' };
    saveBooking_(b);
    return publicBooking_(b);
  });
}
function apiLookup(req) {
  return publicBooking_(findBooking_(loadModel_(), req));
}
function apiCancel(req, opt) {
  return withLock_(() => {
    const now = nowFor_(opt).now;
    const b = findBooking_(loadModel_(), req);
    if (b.status !== 'active') return publicBooking_(b);
    if (now >= deadline_(b.date)) throw new Error('DEADLINE');
    b.status = 'cancelled'; b.changedAt = realNow_();
    saveBooking_(b);
    return publicBooking_(b);
  });
}
function apiChange(req, opt) {
  return withLock_(() => {
    const now = nowFor_(opt).now;
    const m = loadModel_();
    const b = findBooking_(m, req);
    if (b.status !== 'active' || now >= deadline_(b.date)) throw new Error('DEADLINE');
    checkSlot_(m, b.staffId, req.date, req.start, b.minutes, b.id, now);
    b.date = req.date; b.start = Number(req.start); b.changedAt = realNow_();
    saveBooking_(b);
    return publicBooking_(b);
  });
}

/* ===== お店の方の画面 ===== */
function apiLogin(pw) {
  const props = PropertiesService.getScriptProperties();
  const stored = props.getProperty('PW_HASH');
  if (!stored) throw new Error('NO_PASSWORD');
  const cache = CacheService.getScriptCache();
  const fails = Number(cache.get('loginFails') || 0);
  if (fails >= MAX_LOGIN_FAILS) throw new Error('LOCKED');
  if (hash_(props.getProperty('PW_SALT') + String(pw || '')) !== stored) {
    cache.put('loginFails', String(fails + 1), 600);
    throw new Error('BAD_PASSWORD');
  }
  cache.remove('loginFails');
  const token = Utilities.getUuid();
  cache.put('tok_' + token, '1', TOKEN_SECONDS);
  return token;
}
function apiLogout(token) { if (token) CacheService.getScriptCache().remove('tok_' + token); return true; }
function checkToken_(token) {
  if (!token) return false;
  const cache = CacheService.getScriptCache();
  if (!cache.get('tok_' + token)) return false;
  cache.put('tok_' + token, '1', TOKEN_SECONDS);
  return true;
}
function apiShopData(token, opt) {
  if (!checkToken_(token)) throw new Error('AUTH');
  const t = nowFor_(opt);
  const m = loadModel_();
  m.bookings.forEach(b => { delete b.row; });
  return { now: t.now, debug: t.debug, rules: RULES, staff: m.staff, menus: m.menus, bookings: m.bookings };
}
function apiShop(token, action, p, opt) {
  if (!checkToken_(token)) throw new Error('AUTH');
  p = p || {};
  withLock_(() => {
    const m = loadModel_();
    const cleanName = v => { const s = String(v || '').trim().slice(0, 50); if (!s) throw new Error('INVALID'); return s; };
    const cleanMin = v => { const n = Math.round(Number(v)); if (!(n >= 15 && n <= 480)) throw new Error('INVALID'); return n; };
    const cleanPrice = v => Math.max(0, Math.round(Number(v) || 0));
    if (action === 'saveMenu') {
      const x = m.menus.find(x => x.id === p.id); if (!x) throw new Error('INVALID');
      x.name = cleanName(p.name); x.minutes = cleanMin(p.minutes); x.price = cleanPrice(p.price); saveMenus_(m);
    } else if (action === 'addMenu') {
      m.menus.push({ id: 'm' + Date.now(), name: cleanName(p.name), minutes: cleanMin(p.minutes), price: cleanPrice(p.price) }); saveMenus_(m);
    } else if (action === 'delMenu') {
      m.menus = m.menus.filter(x => x.id !== p.id); saveMenus_(m);
    } else if (action === 'saveStaff') {
      const s = m.staff.find(x => x.id === p.id); if (!s) throw new Error('INVALID');
      s.name = cleanName(p.name); saveStaffAndWork_(m);
    } else if (action === 'addStaff') {
      m.staff.push({ id: 's' + Date.now(), name: cleanName(p.name), workDays: [] }); saveStaffAndWork_(m);
    } else if (action === 'delStaff') {
      if (m.bookings.some(b => b.staffId === p.id && b.status === 'active')) throw new Error('STAFF_HAS_BOOKINGS');
      m.staff = m.staff.filter(x => x.id !== p.id); saveStaffAndWork_(m);
    } else if (action === 'setWork') {
      const s = m.staff.find(x => x.id === p.staffId); if (!s) throw new Error('INVALID');
      const dates = (p.dates || []).filter(d => /^\d{4}-\d\d-\d\d$/.test(d));
      if (p.on) dates.forEach(d => { if (s.workDays.indexOf(d) < 0) s.workDays.push(d); });
      else s.workDays = s.workDays.filter(d => dates.indexOf(d) < 0);
      s.workDays.sort(); saveStaffAndWork_(m);
    } else if (action === 'reset') {
      writeSample_();
    } else {
      throw new Error('INVALID');
    }
  });
  return apiShopData(token, opt);
}
