
# クイズ問題並べ替え GA ツール  
ジャンルのバラつきを最大化するために、進化アルゴリズム（GA）を用いて  
クイズ問題の並び順を最適化するツールです。  
CSV を入力すると、ジャンルが偏らない並び順を自動生成し、  
結果を CSV・スコア・ヒートマップとして出力します。  
(最終更新：2026/2/26)

Python 環境が無い場合は WinPython の使用を推奨します。  
インストール手順はこちら：  
https://qiita.com/mmake/items/8903fea085880db041b6

---

# 📦 必要なライブラリ

このツールは以下の Python ライブラリを使用します：

- pandas  
- numpy  
- matplotlib  

### ✔ インストール方法

```bash
pip install pandas numpy matplotlib
```

---

# 🚀 exe 化の手順

```bash
pip install pyinstaller
pyinstaller --onefile --console quiz_genre.py
```

---

# 📁 出力ファイル構成

```
output/
│-- result.csv          ← 最終的に最も良い並び順
│-- score.txt           ← スコア詳細（何世代目か含む）
│-- score_graph.png     ← 世代ごとのスコア推移グラフ
│-- heatmap.png         ← ジャンルの並びを可視化したヒートマップ
```

---

# 📥 入力 CSV の仕様

- 列構造は自由  
- **「ジャンル」を含む列名が必須**  
- 文字コードは自動判定（UTF-8 / UTF-8 BOM / Shift-JIS）

---

# 🧪 サンプル CSV（sample.csv）

```csv
ID,タイトル,ジャンル,難易度
1,問題001,数学,3
2,問題002,国語,2
3,問題003,英語,4
4,問題004,理科,1
5,問題005,社会,2
6,問題006,数学,5
7,問題007,国語,3
8,問題008,英語,1
9,問題009,理科,4
10,問題010,社会,5
11,問題011,数学,2
12,問題012,国語,4
13,問題013,英語,3
14,問題014,理科,5
15,問題015,社会,1
```

---

# 🧠 GA の評価指標（ユーザー調整可能）

total は **0 以上** で、  
**理想状態に近づくほど 0 に近づく** ように設計されています。

```
total =
    penalty_consecutive * penalty_weight
  + close_penalty * close_weight
  + max_genre_ratio * ratio_weight
  + (max_distance - distance_score) * distance_weight
```

---

# 🔍 各指標の意味

### ✔ penalty（連続ペナルティ）
同じジャンルが連続した回数。

---

### ✔ close_penalty（近距離ペナルティ）
close_range（例：5問）以内に同じジャンルが出た回数。

---

### ✔ distance（距離スコア）
同じジャンル同士がどれだけ離れているかの総和。  
大きいほど良い。

---

### ✔ ratio（ジャンル偏り率）
最も多いジャンルの出現割合。  
偏りが大きいほど ratio が大きくなる。

---

# 🥇 total が同じ場合の比較ロジック

優先順位：

1. total（小さいほど良い）  
2. penalty（小さいほど良い）  
3. close_penalty（小さいほど良い）  
4. ratio（小さいほど良い）  
5. distance（大きいほど良い）  

---

# 🎨 heatmap.png の見方（ジャンルの散らばり可視化）

`heatmap.png` は、  
**最終的な並び順のジャンルを色で表現した図** です。

- 横方向：問題の並び順（左が最初の問題）  
- 色：ジャンル（ジャンルごとに固有の色）  
- 色がバラバラ → 良い並び  
- 同じ色が固まっている → 連続 or 近距離ペナルティの原因  

### ✔ 見るべきポイント

- 同じ色が連続していないか  
- 同じ色が近距離に固まっていないか  
- 全体的に色が均等に散らばっているか  

---

# 📈 score_graph.png の見方（進化の推移）

`score_graph.png` は、  
**世代ごとの total スコアの推移** を表します。

- 縦軸：total（小さいほど良い）  
- 横軸：世代数  
- グラフが下がる → 並びが改善している  
- 200〜300 世代で収束することが多い  

### ✔ 見るべきポイント

- 初期は急激に下がる（GA が改善している証拠）  
- 中盤〜後半で横ばいになる（最適解付近に到達）  
- total が 0 に近づくほど理想的な並び  

---

# 🔧 調整可能なパラメータ

| パラメータ | 説明 | デフォルト |
|-----------|------|------------|
| `--close-range` | 何問以内に同ジャンル禁止か | 5 |
| `--penalty-weight` | 連続ペナルティの重み | 1000 |
| `--close-weight` | 近距離ペナルティの重み | 500 |
| `--ratio-weight` | ジャンル偏りの重み | 200 |
| `--distance-weight` | 距離スコアの重み | 0.1 |
| `--mutation-rate` | 突然変異率 | 0.1 |

---

# 🔢 世代数の指標（計算式つき）

```
必要世代数 ≒ 問題数 × log(ジャンル数 + 1)
```

例：問題数 100、ジャンル数 10 → 約 240 世代  
→ **200〜300 世代でほぼ最適解に到達**

---

# 🖥 実行方法（Python / exe）

## ■ 基本

```bash
python quiz_genre.py input.csv
```

## ■ 世代数を指定

```bash
python quiz_genre.py input.csv 300
```

## ■ 3問以内に同ジャンル禁止にしたい

```bash
python quiz_genre.py input.csv 300 --close-range 3
```

## ■ ペナルティを強化したい

```bash
python quiz_genre.py input.csv 300 --penalty-weight 2000 --close-weight 800
```

## ■ 距離スコアを重視したい

```bash
python quiz_genre.py input.csv 300 --distance-weight 0.3
```

## ■ 偏りを強く罰したい

```bash
python quiz_genre.py input.csv 300 --ratio-weight 500
```

## ■ 突然変異を強くして探索範囲を広げたい

```bash
python quiz_genre.py input.csv 300 --mutation-rate 0.3
```

## ■ exe で実行する場合

```bash
quiz_genre.exe input.csv 300 --close-range 3
```

---

# 📡 フォルダ構成例

```
project/
 ├─ quiz_genre.py
 ├─ sample.csv
 └─ output/
      ├─ result.csv
      ├─ score.txt
      ├─ score_graph.png
      └─ heatmap.png
```

---

# ⚠ エラー仕様

### ❌ エラー: 文字コードがUTF-8ではありません

- CSV が UTF-8 / UTF-8(BOM) / Shift-JIS のいずれでも読み込めない場合に発生します。  
- Excel やメモ帳で UTF-8 に変換して保存し直してください。

---

### ❌ エラー: ジャンル列がありません

- 列名に「ジャンル」を含む列が存在しない場合に発生します。  
- 列名を `ジャンル` などに変更してください。

---

# 🎉 ライセンス

自由に改変・利用できます。
