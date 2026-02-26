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

## 📦 必要なライブラリ

- pandas
- numpy
- matplotlib

### インストール方法

```bash
pip install pandas numpy matplotlib
```

---

## 🚀 exe 化の手順

```bash
pip install pyinstaller
pyinstaller --onefile --console quiz_genre.py
```

---

## 📁 出力ファイル構成

```
output/
│-- result.csv          ← 最終的に最も良い並び順
│-- score.txt           ← スコア詳細（何世代目か含む）
│-- score_graph.png     ← 世代ごとのスコア推移グラフ
│-- heatmap.png         ← ジャンルの並びを可視化したヒートマップ
```

---

## 📥 入力 CSV の仕様

- 列構造は自由
- **「ジャンル」を含む列名が必須**
- 文字コードは自動判定（UTF-8 / UTF-8 BOM / Shift-JIS）

---

## 🧪 サンプル CSV（sample.csv）

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

# 🧠 GA の評価指標

total は **0 以上** で、  
**理想状態に近づくほど 0 に近づく** ように設計されています。

```text
total =
    penalty_consecutive * penalty_weight
  + close_penalty * close_weight
  + (max_distance - distance_score) * distance_weight
```

---

# 🔍 各指標の意味

### penalty（連続ペナルティ）

同じジャンルが連続した回数。

### close_penalty（近距離ペナルティ）

close_range（例：5問）以内に同じジャンルが出た回数。

### distance（距離スコア）

同じジャンル同士がどれだけ離れているかの総和。  
大きいほど良い。

---

# 🥇 total が同じ場合の比較ロジック

優先順位：

1. total（小さいほど良い）
2. penalty（小さいほど良い）
3. close_penalty（小さいほど良い）
4. distance（大きいほど良い）

---

# 🧬 GA アルゴリズムの強化点（最新版）

このツールには以下の GA 強化が実装されています：

### PMX（部分写像交叉）

順列最適化に適した交叉方式で、親の構造を保ちながら新しい並びを生成します。

### 強化突然変異（3 種類）

- swap（入れ替え）
- scramble（区間シャッフル）
- inversion（区間反転）

### エリート保存（elitism）

各世代の上位個体をそのまま次世代へコピーし、良い解が失われないようにします。

### 多様性維持

- 重複個体の排除
- 個体数が減った場合はランダム個体を追加

これにより、局所解にハマりにくく、より安定した進化が可能になります。

---

# 🎨 heatmap.png の見方

最終的な並び順のジャンルを色で表現した図です。

- 横方向：問題の並び順
- 色：ジャンル
- 色がバラバラ → 良い並び
- 同じ色が固まる → ペナルティの原因

---

# 📈 score_graph.png の見方

世代ごとの total スコアの推移を表します。

- 縦軸：total（小さいほど良い）
- 横軸：世代数
- 下がるほど改善
- 中盤〜後半で横ばい → 収束

---

# 🔧 調整可能なパラメータ

| パラメータ          | 説明                       | デフォルト |
| ------------------- | -------------------------- | ---------- |
| `--close-range`     | 何問以内に同ジャンル禁止か | 5          |
| `--penalty-weight`  | 連続ペナルティの重み       | 1000       |
| `--close-weight`    | 近距離ペナルティの重み     | 500        |
| `--distance-weight` | 距離スコアの重み           | 0.1        |
| `--mutation-rate`   | 突然変異率                 | 0.1        |
| `--elite-ratio`     | エリート保存の割合         | 0.1        |

---

# 🔢 世代数の目安

```text
必要世代数 ≒ 問題数 × log(ジャンル数 + 1)
```

例：問題数 100、ジャンル数 10 → 約 240 世代  
→ **200〜300 世代でほぼ最適解に到達**

---

# 🖥 実行方法

## 基本

```bash
python quiz_genre.py input.csv
```

## 世代数を指定

```bash
python quiz_genre.py input.csv 300
```

## 3問以内に同ジャンル禁止

```bash
python quiz_genre.py input.csv 300 --close-range 3
```

## ペナルティを強化

```bash
python quiz_genre.py input.csv 300 --penalty-weight 2000 --close-weight 800
```

## 距離スコアを重視

```bash
python quiz_genre.py input.csv 300 --distance-weight 0.3
```

## 突然変異を強くする

```bash
python quiz_genre.py input.csv 300 --mutation-rate 0.3
```

## エリート保存を強化

```bash
python quiz_genre.py input.csv 300 --elite-ratio 0.2
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

### エラー: 文字コードがUTF-8ではありません

CSV が UTF-8 / UTF-8(BOM) / Shift-JIS のいずれでも読み込めない場合。

### エラー: ジャンル列がありません

列名に「ジャンル」を含む列が存在しない場合。

---

# 🎉 ライセンス

自由に改変・利用できます。
