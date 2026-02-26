# 📘 クイズ問題並べ替え GA ツール

# 初学者向け 4パターン対応 手順書（簡潔版）

---

# 🧩 最初に知っておくこと（全パターン共通）

## ■ このツールでできること

- クイズ問題の CSV を読み込み
- ジャンルが偏らないように並び替え
- 結果を CSV と画像で出力

## ■ フォルダ構成（共通）

```
project/
 ├ quiz_genre.py
 ├ input.csv
 └ output/   ← 自動で作られる
```

## ■ 入力 CSV の条件

- 列名に **「ジャンル」** を含む列が必須
- 文字コードは **UTF-8 / UTF-8 BOM / Shift-JIS**

---

# 📂 まず最初に：フォルダ移動（cd）の基本

どのパターンでも、実行前に **ツールのあるフォルダへ移動** します。

例：デスクトップの project フォルダに置いた場合

```bash
cd Desktop/project
```

以降の手順では、この操作を「フォルダへ移動」とだけ記載します。

---

# ================================

# ① WinPython を使って Python で実行する

# ================================

WinPython は PC を汚さない初心者向け Python です。

## 1-1. WinPython をインストール

https://qiita.com/mmake/items/8903fea085880db041b6

## 1-2. WinPython Command Prompt を開く

## 1-3. 必要なライブラリをインストール

```bash
pip install pandas numpy matplotlib
```

## 1-4. フォルダへ移動（cd）

## 1-5. 実行

```bash
python quiz_genre.py input.csv
```

---

# ================================

# ② WinPython で exe を作って実行する

# ================================

exe を作るには Python が必要なので  
①の 1-1 → 1-2 → 1-3 を先に行います。

## 2-1. PyInstaller をインストール

```bash
pip install pyinstaller
```

## 2-2. フォルダへ移動（cd）

## 2-3. exe を作る

```bash
pyinstaller --onefile --console quiz_genre.py
```

生成物：

```
dist/
 └ quiz_genre.exe
```

## 2-4. exe を実行

```bash
quiz_genre.exe input.csv
```

---

# ================================

# ③ 自前の Python で実行する

# ================================

## 3-1. Python が入っているか確認

```bash
python --version
```

## 3-2. 必要なライブラリをインストール

```bash
pip install pandas numpy matplotlib
```

## 3-3. フォルダへ移動（cd）

## 3-4. 実行

```bash
python quiz_genre.py input.csv
```

---

# ================================

# ④ 自前の Python で exe を作って実行する

# ================================

## 4-1. PyInstaller をインストール

```bash
pip install pyinstaller
```

## 4-2. フォルダへ移動（cd）

## 4-3. exe を作る

```bash
pyinstaller --onefile --console quiz_genre.py
```

## 4-4. exe を実行

```bash
quiz_genre.exe input.csv
```

---

# 📊 出力ファイルの見方（共通）

| ファイル        | 内容                         |
| --------------- | ---------------------------- |
| result.csv      | 最終的に最も良い並び順       |
| score.txt       | スコアの詳細                 |
| score_graph.png | 世代ごとのスコア推移         |
| heatmap.png     | ジャンルの散らばり（可視化） |

---

# ⚠ トラブルが起きたとき（共通）

## 文字コードエラー

→ CSV を UTF-8 で保存し直す

## ジャンル列が無い

→ 列名に **ジャンル** を含める

---

# 🎉 初学者向けまとめ

- Python が無い → **WinPython が簡単**
- Python がある → **そのまま実行できる**
- exe を作ると **Python が無い PC でも動く**
- 実行前には **1回だけ cd でフォルダ移動**
