import pandas as pd
import random
import sys
import os
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import numpy as np

# =========================================
#  CSV 読み込み（文字コード自動判定つき）
# =========================================
def load_csv(path):
    df = None

    # 1. UTF-8
    try:
        df = pd.read_csv(path, encoding="utf-8")
        print("文字コード: UTF-8")
    except UnicodeDecodeError:
        pass

    # 2. UTF-8(BOM)
    if df is None:
        try:
            df = pd.read_csv(path, encoding="utf-8-sig")
            print("文字コード: UTF-8(BOM)")
        except UnicodeDecodeError:
            pass

    # 3. Shift-JIS → UTF-8 に変換
    if df is None:
        try:
            df = pd.read_csv(path, encoding="shift_jis")
            print("文字コード: Shift-JIS → UTF-8 に変換します")
        except UnicodeDecodeError:
            print("エラー: 文字コードがUTF-8ではありません")
            sys.exit(1)

    # ジャンル列の検出
    genre_col = None
    for col in df.columns:
        if "ジャンル" in col:
            genre_col = col
            break

    if genre_col is None:
        print("エラー: ジャンル列がありません")
        sys.exit(1)

    return df.to_dict(orient="records"), genre_col


# =========================================
#  評価関数（total は 0 以上）
# =========================================
eval_cache = {}

def evaluate(sequence, genre_col,
             close_range=5,
             penalty_weight=1000,
             close_weight=500,
             ratio_weight=200,
             distance_weight=0.1):

    key = (
        tuple(item["ID"] for item in sequence),
        close_range,
        penalty_weight,
        close_weight,
        ratio_weight,
        distance_weight,
    )
    if key in eval_cache:
        return eval_cache[key]

    genres = [item[genre_col] for item in sequence]
    n = len(genres)

    # ① 同ジャンル連続
    penalty = sum(1 for i in range(n - 1) if genres[i] == genres[i + 1])

    # ② close_range 以内に同ジャンルがあれば罰
    close_penalty = 0
    for i in range(n):
        for j in range(i + 1, min(i + close_range, n)):
            if genres[i] == genres[j]:
                close_penalty += 1

    # ③ 距離スコア
    positions = defaultdict(list)
    for idx, g in enumerate(genres):
        positions[g].append(idx)

    dist = 0
    for pos_list in positions.values():
        m = len(pos_list)
        if m > 1:
            s = sum(pos_list)
            for i in range(m):
                dist += abs((m - 1 - i) * pos_list[i] - (s - pos_list[i]))

    # ④ ジャンル偏り
    c = Counter(genres)
    ratio = max(c.values()) / n

    # ⑤ 距離の最大値（近似）
    max_distance = n * (n - 1) / 2

    # ★ total（小さいほど良い・0 以上）
    distance_term = max(max_distance - dist, 0)

    total = (
        penalty * penalty_weight +
        close_penalty * close_weight +
        ratio * ratio_weight +
        distance_term * distance_weight
    )

    result = {
        "penalty": penalty,
        "close_penalty": close_penalty,
        "distance": dist,
        "ratio": ratio,
        "total": total,
    }

    eval_cache[key] = result
    return result


# =========================================
#  個体比較（total 同値時の優先順位つき）
# =========================================
def is_better(a, b, genre_col, eval_conf):
    ea = evaluate(a, genre_col, **eval_conf)
    eb = evaluate(b, genre_col, **eval_conf)

    # ① total（小さいほど良い）
    if ea["total"] != eb["total"]:
        return ea["total"] < eb["total"]

    # ② penalty（小さいほど良い）
    if ea["penalty"] != eb["penalty"]:
        return ea["penalty"] < eb["penalty"]

    # ③ close_penalty（小さいほど良い）
    if ea["close_penalty"] != eb["close_penalty"]:
        return ea["close_penalty"] < eb["close_penalty"]

    # ④ ratio（小さいほど良い）
    if ea["ratio"] != eb["ratio"]:
        return ea["ratio"] < eb["ratio"]

    # ⑤ distance（大きいほど良い）
    return ea["distance"] > eb["distance"]


# =========================================
#  GA 基本操作
# =========================================
def init_population(data, size=50):
    return [random.sample(data, len(data)) for _ in range(size)]

def tournament_selection(pop, genre_col, eval_conf, k=3):
    best = None
    for _ in range(k):
        indiv = random.choice(pop)
        if best is None or is_better(indiv, best, genre_col, eval_conf):
            best = indiv
    return best

def crossover(parent1, parent2):
    size = len(parent1)
    a, b = sorted(random.sample(range(size), 2))
    child = [None] * size
    child[a:b] = parent1[a:b]
    fill_items = [item for item in parent2 if item not in child]
    fill_idx = 0
    for i in range(size):
        if child[i] is None:
            child[i] = fill_items[fill_idx]
            fill_idx += 1
    return child

def mutate(indiv, rate=0.1):
    if random.random() < rate:
        i, j = random.sample(range(len(indiv)), 2)
        indiv[i], indiv[j] = indiv[j], indiv[i]
    return indiv


# =========================================
#  出力フォルダ
# =========================================
def ensure_output_dir():
    os.makedirs("output", exist_ok=True)


# =========================================
#  最新結果保存
# =========================================
def save_latest_results(best, score_dict, gen):
    pd.DataFrame(best).to_csv("output/result.csv", index=False)
    with open("output/score.txt", "w", encoding="utf-8") as f:
        f.write(f"Generation: {gen}\n")
        for k, v in score_dict.items():
            f.write(f"{k}: {v}\n")


# =========================================
#  ヒートマップ
# =========================================
def save_heatmap(best, genre_col):
    genres = [item[genre_col] for item in best]
    unique = list(sorted(set(genres)))
    mapping = {g: i for i, g in enumerate(unique)}
    arr = np.array([[mapping[g] for g in genres]])

    plt.figure(figsize=(18, 2))
    plt.imshow(arr, cmap="tab20", aspect="auto")
    plt.colorbar()
    plt.title("Genre Heatmap")
    plt.savefig("output/heatmap.png")
    plt.close()


# =========================================
#  GA メイン
# =========================================
def genetic_algorithm(data, genre_col, generations=50, pop_size=40,
                      mutation_rate=0.1,
                      close_range=5,
                      penalty_weight=1000,
                      close_weight=500,
                      ratio_weight=200,
                      distance_weight=0.1):

    ensure_output_dir()

    eval_conf = dict(
        close_range=close_range,
        penalty_weight=penalty_weight,
        close_weight=close_weight,
        ratio_weight=ratio_weight,
        distance_weight=distance_weight,
    )

    population = init_population(data, pop_size)

    global_best = None
    global_best_gen = 1

    scores = []

    for gen in range(1, generations + 1):
        new_pop = []

        for _ in range(pop_size):
            p1 = tournament_selection(population, genre_col, eval_conf)
            p2 = tournament_selection(population, genre_col, eval_conf)
            child = mutate(crossover(p1, p2), rate=mutation_rate)
            new_pop.append(child)

        population = new_pop

        # ★ best 個体の選択（is_better を使用）
        best = population[0]
        for indiv in population[1:]:
            if is_better(indiv, best, genre_col, eval_conf):
                best = indiv

        score_dict = evaluate(best, genre_col, **eval_conf)
        scores.append(score_dict["total"])

        print(f"\n=== Generation {gen} ===")
        print(score_dict)

        # ★ 全世代ベスト更新
        if global_best is None or is_better(best, global_best, genre_col, eval_conf):
            global_best = best
            global_best_gen = gen

        save_latest_results(best, score_dict, gen)

    # スコア推移グラフ
    plt.plot(scores)
    plt.xlabel("Generation")
    plt.ylabel("Total Score (lower is better, best ≒ 0)")
    plt.title("Score Transition")
    plt.savefig("output/score_graph.png")
    plt.close()

    # ヒートマップ
    save_heatmap(global_best, genre_col)

    print(f"\n=== 全世代で最も total が低かった個体（Generation {global_best_gen}） ===")
    print(evaluate(global_best, genre_col, **eval_conf))

    save_latest_results(global_best, evaluate(global_best, genre_col, **eval_conf), global_best_gen)

    return global_best


# =========================================
#  引数パース
# =========================================
def parse_args(argv):
    if len(argv) < 2:
        print("Usage: python quiz_genre.py input.csv [generations] [options]")
        sys.exit(1)

    input_csv = argv[1]
    idx = 2

    generations = 50
    if idx < len(argv) and argv[idx].isdigit():
        generations = int(argv[idx])
        idx += 1

    params = {
        "close_range": 5,
        "penalty_weight": 1000,
        "close_weight": 500,
        "ratio_weight": 200,
        "distance_weight": 0.1,
        "mutation_rate": 0.1,
    }

    while idx < len(argv):
        arg = argv[idx]
        if arg == "--close-range":
            params["close_range"] = int(argv[idx + 1])
            idx += 2
        elif arg == "--penalty-weight":
            params["penalty_weight"] = float(argv[idx + 1])
            idx += 2
        elif arg == "--close-weight":
            params["close_weight"] = float(argv[idx + 1])
            idx += 2
        elif arg == "--ratio-weight":
            params["ratio_weight"] = float(argv[idx + 1])
            idx += 2
        elif arg == "--distance-weight":
            params["distance_weight"] = float(argv[idx + 1])
            idx += 2
        elif arg == "--mutation-rate":
            params["mutation_rate"] = float(argv[idx + 1])
            idx += 2
        else:
            print(f"不明な引数: {arg}")
            sys.exit(1)

    return input_csv, generations, params


# =========================================
#  メイン
# =========================================
def main():
    input_csv, generations, params = parse_args(sys.argv)

    print(f"世代数: {generations}")
    print("評価パラメータ:", params)

    data, genre_col = load_csv(input_csv)

    genetic_algorithm(
        data,
        genre_col,
        generations=generations,
        pop_size=40,
        mutation_rate=params["mutation_rate"],
        close_range=params["close_range"],
        penalty_weight=params["penalty_weight"],
        close_weight=params["close_weight"],
        ratio_weight=params["ratio_weight"],
        distance_weight=params["distance_weight"],
    )

    print("\n=== 完了 ===")
    print("output/result.csv / output/score.txt / output/score_graph.png / output/heatmap.png を出力しました")


if __name__ == "__main__":
    main()
