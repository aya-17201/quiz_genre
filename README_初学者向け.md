# 📘 クイズ問題並べ替え GA ツール

# 初学者向け 4パターン対応 手順書（cd 操作つき）

---

# 🧩 まず最初に知っておくこと（全パターン共通）

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

- 列名に ジャンル を含む列が必須
- 文字コードは UTF-8 / UTF-8 BOM / Shift-JIS のいずれか

---

# ================================

# ① WinPython を使って Python で実行する

# ================================

WinPython はインストールしても PC を汚さないタイプの Python で、初学者でも扱いやすいです。

---

## 1-1. WinPython をインストールする

手順はこちら  
https://qiita.com/mmake/items/8903fea085880db041b6

---

## 1-2. WinPython Command Prompt を開く

---

## 1-3. 必要なライブラリをインストールする

```bash
pip install pandas numpy matplotlib
```

---

## 1-4. ツールのあるフォルダへ移動する

例 デスクトップの project フォルダに置いた場合

```bash
cd Desktop/project
```

---

## 1-5. ツールを実行する（基本形）

```bash
python quiz_genre.py input.csv
```

---

# ================================

# ② WinPython を使って exe に変換して実行する

# ================================

exe を作るには Python が必要なので  
①の 1-1 → 1-2 → 1-3 を先に行います。

---

## 2-1. PyInstaller をインストールする

```bash
pip install pyinstaller
```

---

## 2-2. ツールのあるフォルダへ移動する

```bash
cd Desktop/project
```

---

## 2-3. exe を作る

```bash
pyinstaller --onefile --console quiz_genre.py
```

生成物

```
dist/
 └ quiz_genre.exe
```

---

## 2-4. exe を実行する（基本形）

```bash
quiz_genre.exe input.csv
```

Python が入っていない PC でも動きます。

---

# ================================

# ③ 自前の Python 環境で Python で実行する

# ================================

あなたの PC にすでに Python が入っている場合はこちら。

---

## 3-1. Python が入っているか確認する

```bash
python --version
```

Python が入っていない場合  
→ ① WinPython を使う方法をおすすめします。

---

## 3-2. 必要なライブラリをインストールする

```bash
pip install pandas numpy matplotlib
```

---

## 3-3. ツールのあるフォルダへ移動する

```bash
cd Desktop/project
```

---

## 3-4. ツールを実行する（基本形）

```bash
python quiz_genre.py input.csv
```

---

# ================================

# ④ 自前の Python 環境で exe に変換して実行する

# ================================

exe を作るには Python が必要なので  
③の 3-1 → 3-2 を先に行います。

---

## 4-1. PyInstaller をインストールする

```bash
pip install pyinstaller
```

---

## 4-2. ツールのあるフォルダへ移動する

```bash
cd Desktop/project
```

---

## 4-3. exe を作る

```bash
pyinstaller --onefile --console quiz_genre.py
```

---

## 4-4. exe を実行する（基本形）

```bash
quiz_genre.exe input.csv
```

---

# ================================

# 📊 出力ファイルの見方（全パターン共通）

# ================================

| ファイル        | 内容                   |
| --------------- | ---------------------- |
| result.csv      | 最終的に最も良い並び順 |
| score.txt       | スコアの詳細           |
| score_graph.png | 世代ごとのスコア推移   |
| heatmap.png     | ジャンルの散らばり     |

---

# ================================

# ⚠ トラブルが起きたとき（全パターン共通）

# ================================

## 文字コードエラー

→ CSV を UTF-8 で保存し直す

## ジャンル列が無い

→ 列名に ジャンル を含める

---

# 🎉 最後に（初学者向けまとめ）

- Python が無い → WinPython を使う方法が簡単
- Python がある → 自前環境で実行できる
- exe を作ると Python が無い PC でも動く
- 実行前には必ず cd でフォルダ移動が必要
