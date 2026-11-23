# SparkAI 広告動画リポジトリ

株式会社ReFast のサービス **SparkAI**（中小企業向けの DX 支援・システム構築・AI 人材教育）の、SNS 広告動画をまとめたリポジトリです。
広告の台本、できあがった動画、動画を作り直すためのスクリプトが入っています。

- 何を作るのか、なぜ作るのか → [`docs/PRD.md`](docs/PRD.md)
- Claude Code で作業するときのルール → [`CLAUDE.md`](CLAUDE.md)

最終更新：2026-11-21

---

## 1. この README でできること

読み終わると、次のことができるようになります。

1. どの動画が完成品で、どこにあるかがわかる
2. BGM・効果音・エンドカード・テロップを自分の手で作り直せる
3. テロップの文言やタイミングを直して、動画を書き出し直せる

---

## 2. フォルダ構成

```
SparkAI/
├── README.md              この説明書
├── CLAUDE.md              Claude Code 向けの作業ルール
├── docs/PRD.md            企画・要件（何を、誰に、なぜ）
├── requirements.txt       Python で使うライブラリ
├── package.json           Node.js で使うライブラリ（Playwright）
└── ads/
    ├── sns-ad-story.md    全体のコンセプトと「佐藤さん編」の台本
    ├── storyboard.html    佐藤さん編の絵コンテ（ブラウザで開く）
    ├── young-story.md     若手編「翔太、24歳。」の台本
    ├── young-story-v2.md  若手編の別案「陸、25歳。」の台本
    └── video/
        ├── *.mp4                 できあがった動画
        ├── compose.py            佐藤さん編（30秒）を組み立てる
        ├── make_stills.py        佐藤さん編のカレンダー画像とエンドカード
        ├── make_bgm.py           佐藤さん編の BGM
        ├── compose_craftsman.py  職人編を組み立てる
        ├── young/                翔太編（アニメ版）
        ├── riku/                 陸編（アニメ版・最終版）
        └── video_src/            横型 SparkAI 動画のテロップ（.ass）・BGM・帯画像・ロゴ
```

---

## 3. 動画一覧（どれが完成品か）

縦型は 1080×1920（Reels・TikTok・Shorts 用）、横型は 1920×1080（YouTube・Facebook 用）です。

| ファイル（`ads/video/`） | 内容 | 向き | 長さ | 状態 |
|---|---|---|---|---|
| `refast_riku_final.mp4` | 陸編・最終版（生成映像4本＋テロップ＋効果音＋ロゴ） | 縦 | 61秒 | **完成** |
| `refast_craftsman_telop.mp4` | 職人編（テロップ・声なし・エンドカード） | 縦 | 49秒 | **完成** |
| `refast_ad_30s.mp4` | 佐藤さん編 30秒版（テロップ・BGM・エンドカード） | 縦 | 29秒 | **完成** |
| `ReFast_short.mp4` | ReFast ショート（テロップ・ロゴ） | 縦 | 18秒 | **完成** |
| `refast_riku_anime.mp4` | 陸編・アニメ下書き | 縦 | 60秒 | 下書き |
| `refast_young_anime.mp4` | 翔太編・アニメ下書き | 縦 | 60秒 | 下書き |
| `sparkAI_telop_bgm.mp4` | 独立したい人編（テロップ・BGM） | 横 | 44秒 | **完成** |
| `sparkAI_combined.mp4` | 上の素材をつないだもの（テロップなし） | 横 | 44秒 | 素材 |
| `SparkAI_woman_owner_telop_bgm.mp4` | 女性オーナー編（テロップ・BGM） | 横 | 44秒 | **完成** |
| `SparkAI_woman_owner.mp4` | 上の素材（テロップなし） | 横 | 44秒 | 素材 |
| `SparkAI_security.mp4` | セキュリティ編 | 横 | 39秒 | **完成** |

---

## 4. 準備するもの

### 4-1. ソフト

| ソフト | バージョンの目安 | 確認コマンド |
|---|---|---|
| Python | 3.10 以上 | `python3 --version` |
| ffmpeg / ffprobe | 5 以上（`ass` フィルタ付き） | `ffmpeg -filters \| grep ass` |
| Node.js | 18 以上（アニメを描くときだけ） | `node --version` |

### 4-2. ライブラリ

リポジトリの一番上のフォルダで実行します。

```bash
pip install -r requirements.txt
```

```bash
npm install
```

```bash
npx playwright install chromium
```

- `demucs`（声を消すツール）は大きいので、陸編・最終版を作り直すときだけ必要です。不要なら `requirements.txt` から外してかまいません。
- Playwright のブラウザがすでに入っている環境では、3つ目のコマンドは不要です。

### 4-3. フォント（リポジトリには入っていません）

| フォント | 使う場所 | 入手先 |
|---|---|---|
| Zen Kaku Gothic New（Black / Bold） | 縦型動画のテロップ・エンドカード | Google Fonts |
| Noto Sans CJK JP | 横型動画のテロップ（`video_src/*.ass`） | Google Fonts（Noto Sans JP）または OS のパッケージ |

Zen Kaku Gothic New は、どこか1つのフォルダ（以下 `FONTS`）に次の名前で置いてください。

```
FONTS/ZenKakuGothicNew-Black.ttf
FONTS/ZenKakuGothicNew-Bold.ttf
```

### 4-4. 元の映像素材（リポジトリには入っていません）

AI で生成した元の映像クリップや、SparkAI のロゴ画像は容量の都合でリポジトリに入れていません。作り直すときは、制作担当から受け取ってください。

| 動画 | 必要な素材 |
|---|---|
| 佐藤さん編 | `seg1.mp4` `seg2.mp4` `seg4.mp4` `seg5.mp4` `cal_full.png`、元動画、`fonts/` を1つのフォルダにまとめたもの |
| 職人編 | 元動画、声を消した効果音 WAV |
| 陸編・最終版 | 生成クリップ4本、SparkAI ロゴ PNG（ReFast ロゴは `video_src/refast_logo.png`） |

---

## 5. 作り方

以下、コマンドは `ads/video/` で実行します。作業用ファイルは `work/`、書き出しは `out/` に置く例です（どちらも Git には入りません）。

```bash
cd ads/video
```

```bash
mkdir -p work out
```

### 5-1. 素材がなくてもすぐ試せるもの（動作確認）

BGM を作ってみます。

```bash
python3 make_bgm.py out/bgm_sato.wav
```

**成功の目安：** `wrote out/bgm_sato.wav 28.87s` と表示され、`out/bgm_sato.wav` ができる。

その他の BGM・効果音も同じように作れます。

| コマンド | できるもの |
|---|---|
| `python3 video_src/bgm.py out/bgm.wav` | 独立したい人編の BGM（44.24秒） |
| `python3 video_src/bgm_woman.py out/bgm_woman.wav` | 女性オーナー編の BGM（43.94秒） |
| `python3 video_src/bgm_security.py out/bgm_security.wav` | セキュリティ編の BGM（39.3秒） |
| `python3 young/make_audio.py out/young_audio.wav` | 翔太編の BGM＋効果音（60秒） |
| `python3 riku/make_audio.py out/riku_audio.wav` | 陸編の BGM＋効果音（60.5秒） |

### 5-2. エンドカード（フォントが必要）

```bash
python3 riku/make_endcard.py FONTS out/endcard_riku.png
```

**成功の目安：** 紺色の背景に「人が足りないなら、人を伸ばせばいい。」「SparkAI」「無料相談 30分」が入った 1080×1920 の PNG ができる。

### 5-3. アニメ版（翔太編・陸編）

`scenes.html` の絵をブラウザで1コマずつ描いて、動画にします。

1. アニメ本体（音なし）を書き出す

   ```bash
   node riku/render.js video FONTS/ZenKakuGothicNew-Black.ttf work/riku_anim.mp4
   ```

2. 音を作る

   ```bash
   python3 riku/make_audio.py work/riku_audio.wav
   ```

3. エンドカードを作る

   ```bash
   python3 riku/make_endcard.py FONTS work/riku_endcard.png
   ```

4. テロップ・音・エンドカードを合成する

   ```bash
   python3 riku/compose_riku.py work/riku_anim.mp4 work/riku_audio.wav work/riku_endcard.png FONTS work out/refast_riku_anime.mp4
   ```

**成功の目安：** `out/refast_riku_anime.mp4` ができ、約60秒・1080×1920・音あり・最後にエンドカードが入っている。

翔太編は、`riku/` を `young/`、`compose_riku.py` を `compose_young.py` に読みかえれば同じ手順です。

特定の秒の絵だけを確認したいときは、次のように静止画を書き出します。

```bash
node riku/render.js stills FONTS/ZenKakuGothicNew-Black.ttf work/check 3 15.7 45
```

### 5-4. 陸編・最終版（生成クリップ4本から）

```bash
python3 riku/compose_final.py clip1.mp4 clip2.mp4 clip3.mp4 clip4.mp4 sparkai_logo.png video_src/refast_logo.png FONTS work out/refast_riku_final.mp4
```

中でやっていること：

1. クリップ2の、スマホが宙に浮いて見える部分（4.05〜5.8秒）を切り取る
2. Demucs で人の声を消し、効果音だけ残す（CPU だと数分かかります）
3. 4本をクロスフェードでつなぎ、テロップを焼き込み、ロゴ入りエンドカードを付ける

### 5-5. 職人編

```bash
python3 compose_craftsman.py 元動画.mp4 効果音.wav FONTS endcard.png work out/refast_craftsman_telop.mp4
```

### 5-6. 佐藤さん編（30秒）

`S` は、4-4 の素材と `fonts/` をまとめたフォルダです。

```bash
python3 make_stills.py S
```

```bash
python3 compose.py S 元動画.mp4 out/refast_ad_30s.mp4
```

```bash
python3 make_bgm.py work/bgm.wav
```

---

## 6. よくある直し方

| やりたいこと | 直すファイル | 直す場所 |
|---|---|---|
| 縦型動画のテロップの文言・秒数 | `compose*.py`、`riku/compose_final.py` など | ファイル上部の `T = [...]`（開始秒、終了秒、行のリスト） |
| 横型動画のテロップ | `video_src/telop*.ass` | `Dialogue:` の行（時刻と文言） |
| エンドカードの文言・色 | `make_stills.py`、`*/make_endcard.py` | `ct(...)` / `center_text(...)` の行、色は `NAVY` `AMBER` など |
| BGM の曲調 | `make_bgm.py`、`*/make_audio.py`、`video_src/bgm*.py` | コード進行・`BPM`・効果音を鳴らす秒数 |
| アニメの絵や動き | `young/scenes.html`、`riku/scenes.html` | `renderAt(t)` の中のシーンごとの描画 |

テロップの秒数を変えたときは、BGM の盛り上がりの位置（各音声スクリプト冒頭の説明に秒数が書いてあります）とずれていないかも確認してください。

---

## 7. うまくいかないとき

| 症状 | 原因と対処 |
|---|---|
| `No such filter: 'ass'` | ffmpeg に libass が入っていません。libass 付きの ffmpeg を入れ直してください。 |
| テロップが豆腐（□）になる・別の字体になる | フォントの置き場所かファイル名が違います。4-3 の名前どおりか確認してください。 |
| `OSError: cannot open resource` | `make_endcard.py` などに渡した `FONTS` のパスが違います。 |
| `ModuleNotFoundError: No module named 'demucs'` | `pip install demucs` を実行してください（陸編・最終版のときだけ必要）。 |
| `Executable doesn't exist`（Playwright） | `npx playwright install chromium` を実行してください。 |
| 動画が途中で切れる・音とずれる | 元素材の長さが想定と違います。`ffprobe` で長さを確認し、スクリプト内の秒数を合わせてください。 |

これでも解決しないときは、実行したコマンドとエラー全文を添えて、リポジトリの管理者に連絡してください。

---

## 8. 注意事項

- 台本中の数値（「残業 月40時間 → 5時間」「配車 2時間→10分」など）は**イメージ**です。公開前に実データへ差し替えるか、「※イメージです」を必ず表示してください。
- BGM・効果音はすべてスクリプトで合成したオリジナルで、著作権の心配はありません。
- 映像素材や人物は AI 生成です。実在の人物・企業に似ていないか、公開前に確認してください。
