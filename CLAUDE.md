# CLAUDE.md

このリポジトリで作業する Claude Code 向けのルールです。人向けの手順は `README.md`、企画と要件は `docs/PRD.md` を見てください。

## 概要

株式会社ReFast のサービス SparkAI の SNS 広告動画を作るリポジトリ。中身は次の3つ。

- 台本：`ads/*.md`、絵コンテ：`ads/storyboard.html`
- 完成動画：`ads/video/*.mp4`（一覧と状態は `README.md` の3章）
- 動画を作るスクリプト：`ads/video/` 以下の Python・Node.js・HTML

## 会話・文章のルール

- ユーザーとの会話、台本、ドキュメントは**日本語**。専門用語はなるべく使わず、使うときは一言説明を添える。
- コード内のコメントと docstring は英語（既存に合わせる）。
- 社名は「株式会社ReFast」、サービス名は「SparkAI」と表記する（大文字・小文字に注意）。
- 台本の数値は実データではない。テロップに出すときは「※イメージです」を付ける。

## 技術スタック

- Python 3（numpy、Pillow）：BGM・効果音の合成、エンドカード画像、ffmpeg の呼び出し
- ffmpeg / ffprobe（libass 付き）：結合、クロスフェード、テロップの焼き込み
- Node.js + Playwright：`scenes.html` を1コマずつ描いてアニメにする（`render.js`）
- Demucs：生成映像から人の声を消す（`riku/compose_final.py` のみ）

## スクリプトの決まりごと

- どのスクリプトも引数はコマンドラインの位置引数。使い方は各ファイル冒頭の docstring / コメントに書いてある。変えたら docstring も直す。
- テロップは各 `compose*.py` 上部の `T = [(開始秒, 終了秒, [行...], スタイル), ...]` で定義し、そこから `.ass` を生成して焼き込む。横型動画は `video_src/telop*.ass` を直接編集する。
- 共通の値：`FPS = 30`、クロスフェード `X = 0.4〜0.5`、エンドカードへのクロスフェード `X_END = 0.6`、エンドカード長 `END_LEN = 4.5`（陸編最終版は 5.0）。
- 配色：紺 `NAVY (21,32,43)`、琥珀 `AMBER (224,160,74)`、白、`SOFT (178,190,202)`。エンドカードはこの配色とレイアウトを崩さない。
- 音声スクリプト冒頭の docstring に、映像の秒数と曲の展開の対応表がある。テロップや映像の秒数を変えたら、音の秒数も合わせて直す。
- 乱数は `np.random.default_rng(固定シード)`。同じスクリプトから毎回同じ音ができるようにしておく。

## 外部素材（リポジトリにないもの）

フォント（Zen Kaku Gothic New、Noto Sans CJK JP）、AI 生成の元映像、SparkAI のロゴは Git に入っていない。必要なときはユーザーに場所を聞く。勝手に似たものを作って差し替えない。

## 作業のしかた

- 作業用ファイルは `ads/video/work/`、試しの書き出しは `ads/video/out/` に置く（`.gitignore` 済み）。
- 動画を書き出したら、`ffprobe` で長さ・解像度を確認し、`render.js stills` か ffmpeg で数枚の静止画を切り出して、テロップの位置や絵崩れを目で確認してから報告する。
- 完成動画を `ads/video/` に追加・差し替えたら、`README.md` の動画一覧と `docs/PRD.md` の状態の表も更新する。
- mp4 は 1 本 10〜30MB ある。同じ動画の途中版を何本もコミットしない。最終版だけを入れる。
- 既存の完成動画を上書きするときは、事前にユーザーに確認する。

## 動作確認の最小コマンド

素材なしで動くもの（`ads/video/` で実行）：

```bash
python3 make_bgm.py out/bgm_sato.wav
```

`wrote out/bgm_sato.wav 28.87s` と出れば Python 環境は OK。
