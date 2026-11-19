// Renders scenes.html frame by frame with Playwright and pipes JPEG frames into ffmpeg.
// Usage:
//   node render.js video FONT_PATH OUT.mp4          -> full animation (30fps, 1080x1920, no audio)
//   node render.js stills FONT_PATH OUT_DIR t1 t2 ..  -> PNG stills at given times (for checking)
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const [mode, fontPath, out, ...times] = process.argv.slice(2);
const FPS = 30;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.join(__dirname, 'scenes.html'));
  const font = fs.readFileSync(fontPath).toString('base64');
  await page.evaluate(async (b64) => {
    const f = new FontFace('ZK', `url(data:font/ttf;base64,${b64})`);
    await f.load(); document.fonts.add(f);
  }, font);
  const grab = async (t) => {
    const url = await page.evaluate((t) => { window.renderAt(t); return document.getElementById('c').toDataURL('image/jpeg', 0.93); }, t);
    return Buffer.from(url.split(',')[1], 'base64');
  };
  if (mode === 'stills') {
    fs.mkdirSync(out, { recursive: true });
    for (const t of times) fs.writeFileSync(path.join(out, `t${t}.jpg`), await grab(parseFloat(t)));
  } else {
    const dur = await page.evaluate(() => window.DURATION);
    const n = Math.round(dur * FPS);
    const ff = spawn('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', String(FPS), out], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let i = 0; i < n; i++) {
      const buf = await grab(i / FPS);
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 150 === 0) console.log(`frame ${i}/${n}`);
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
    console.log('wrote', out);
  }
  await browser.close();
})();
