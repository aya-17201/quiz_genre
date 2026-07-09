import argparse
import os
import random
import sys
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# =========================================
#  CSV 読み込み（文字コード自動判定つき）
# =========================================
def load_csv(path):
    encodings = ["utf-8-sig", "utf-8", "cp932", "shift_jis"]
    df = None
    last_error = None

    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc)
            print(f"文字コード: {enc}")
            break
        except Exception as e:
            last_error = e

    if df is None:
        print("エラー: 対応していない文字コードです")
        if last_error is not None:
            print(f"詳細: {last_error}")
        sys.exit(1)

    if df.empty:
        print("エラー: CSV にデータがありません")
        sys.exit(1)

    # ジャンル列の検出
    genre_col = None
    for col in df.columns:
        if "ジャンル" in str(col) or "genre" in str(col).lower():
            genre_col = col
            break

    if genre_col is None:
        print("エラー: ジャンル列が見つかりません")
        sys.exit(1)

    # ジャンル欠損対策
    if df[genre_col].isna().any():
        print("エラー: ジャンル列に空欄があります")
        sys.exit(1)
    df[genre_col] = df[genre_col].astype(str)

    # ID が無い場合に自動付与。ID が重複する場合も内部用 ID を付与する。
    if "ID" not in df.columns or df["ID"].duplicated().any() or df["ID"].isna().any():
        if "ID" in df.columns:
            print("警告: ID が重複または空欄のため、内部 ID を自動付与します")
        df["ID"] = range(1, len(df) + 1)

    return df.to_dict(orient="records"), genre_col


# =========================================
#  評価関数（total は 0 以上）
# =========================================
eval_cache = {}


def clear_eval_cache_if_needed(max_size=200000):
    """長時間実行時のメモリ肥大化を抑える。"""
    if len(eval_cache) > max_size:
        eval_cache.clear()


def pairwise_distance_sum(pos_list):
    """同一ジャンルの出現位置について、全ペア間距離の総和を返す。"""
    total = 0
    prefix = 0
    for i, pos in enumerate(pos_list):
        total += i * pos - prefix
        prefix += pos
    return total


def evaluate(sequence, genre_col,
             close_range=5,
             penalty_weight=1000,
             close_weight=500,
             distance_weight=0.1):
    key = (
        tuple(item["ID"] for item in sequence),
        genre_col,
        int(close_range),
        float(penalty_weight),
        float(close_weight),
        float(distance_weight),
    )

    if key in eval_cache:
        return eval_cache[key]

    genres = [item[genre_col] for item in sequence]
    n = len(genres)

    # 1. 同ジャンル連続
    penalty = sum(genres[i] == genres[i + 1] for i in range(n - 1))

    # 2. close_range 問以内の同ジャンル
    # 例: close_range=5 の場合、現在位置から 5 問先までを確認する。
    close_penalty = 0
    search_range = max(0, int(close_range))
    for i in range(n):
        for j in range(i + 1, min(i + search_range + 1, n)):
            if genres[i] == genres[j]:
                close_penalty += 1

    # 3. 距離スコア（同一ジャンル同士の全ペア距離の総和）
    positions = defaultdict(list)
    for idx, g in enumerate(genres):
        positions[g].append(idx)

    distance = 0
    for pos_list in positions.values():
        if len(pos_list) > 1:
            distance += pairwise_distance_sum(pos_list)

    # 4. 最大距離の近似値。
    # total が負にならないように distance_term は 0 以上に丸める。
    max_distance = n * (n - 1) / 2
    distance_term = max(max_distance - distance, 0)

    total = (
        penalty * penalty_weight +
        close_penalty * close_weight +
        distance_term * distance_weight
    )

    result = {
        "penalty": int(penalty),
        "close_penalty": int(close_penalty),
        "distance": float(distance),
        "total": float(total),
    }

    eval_cache[key] = result
    clear_eval_cache_if_needed()
    return result


# =========================================
#  個体比較（total 同値時の優先順位つき）
# =========================================
def score_key(indiv, genre_col, eval_conf):
    e = evaluate(indiv, genre_col, **eval_conf)
    return (e["total"], e["penalty"], e["close_penalty"], -e["distance"])


def is_better(a, b, genre_col, eval_conf):
    return score_key(a, genre_col, eval_conf) < score_key(b, genre_col, eval_conf)


# =========================================
#  GA 基本操作
# =========================================
def init_population(data, size=50):
    return [random.sample(data, len(data)) for _ in range(size)]


def tournament_selection(pop, genre_col, eval_conf, k=3):
    k = min(k, len(pop))
    candidates = random.sample(pop, k)
    return min(candidates, key=lambda indiv: score_key(indiv, genre_col, eval_conf))


# ---------- PMX 交叉（ID ベース） ----------
def pmx_crossover_ids(parent1_ids, parent2_ids):
    size = len(parent1_ids)

    if size < 2:
        return parent1_ids[:]

    a, b = sorted(random.sample(range(size), 2))
    # b を含めない区間だと 1 要素だけになることがあるため、Python のスライス用に +1 する。
    b += 1

    child = [None] * size
    child[a:b] = parent1_ids[a:b]

    # index を毎回探すと遅いため辞書化
    p2_index = {v: i for i, v in enumerate(parent2_ids)}

    for i in range(a, b):
        val2 = parent2_ids[i]
        if val2 in child:
            continue

        pos = i
        while True:
            val1 = parent1_ids[pos]
            pos = p2_index[val1]
            if child[pos] is None:
                child[pos] = val2
                break

    for i in range(size):
        if child[i] is None:
            child[i] = parent2_ids[i]

    return child


def crossover_pmx(parent1, parent2, id_to_item):
    p1_ids = [item["ID"] for item in parent1]
    p2_ids = [item["ID"] for item in parent2]
    child_ids = pmx_crossover_ids(p1_ids, p2_ids)
    return [id_to_item[i] for i in child_ids]


# ---------- 突然変異（swap / scramble / inversion） ----------
def mutate(indiv, rate=0.1):
    if random.random() >= rate:
        return indiv

    n = len(indiv)
    if n < 2:
        return indiv

    op = random.choice(["swap", "scramble", "inversion"])

    if op == "swap":
        i, j = random.sample(range(n), 2)
        indiv[i], indiv[j] = indiv[j], indiv[i]

    elif op == "scramble":
        i, j = sorted(random.sample(range(n), 2))
        j += 1
        segment = indiv[i:j]
        random.shuffle(segment)
        indiv[i:j] = segment

    elif op == "inversion":
        i, j = sorted(random.sample(range(n), 2))
        j += 1
        indiv[i:j] = reversed(indiv[i:j])

    return indiv


# =========================================
#  出力
# =========================================
def ensure_output_dir():
    os.makedirs("output", exist_ok=True)


def save_latest_results(best, score_dict, gen):
    ensure_output_dir()
    try:
        pd.DataFrame(best).to_csv("output/result.csv", index=False, encoding="utf-8-sig")
    except Exception as e:
        print(f"CSV 保存エラー: {e}")

    try:
        with open("output/score.txt", "w", encoding="utf-8") as f:
            f.write(f"Generation: {gen}\n")
            for k, v in score_dict.items():
                f.write(f"{k}: {v}\n")
    except Exception as e:
        print(f"score.txt 保存エラー: {e}")


def save_heatmap(best, genre_col):
    ensure_output_dir()

    genres = [item[genre_col] for item in best]
    unique = sorted(set(genres))
    mapping = {g: i for i, g in enumerate(unique)}
    arr = np.array([[mapping[g] for g in genres]])

    plt.figure(figsize=(18, 2))
    plt.imshow(arr, cmap="tab20b", aspect="auto")
    cbar = plt.colorbar(ticks=list(mapping.values()))
    cbar.ax.set_yticklabels(unique)
    plt.title("Genre Heatmap")
    plt.xlabel("Question Order")
    plt.yticks([])
    plt.tight_layout()
    plt.savefig("output/heatmap.png", dpi=200)
    plt.close()


# =========================================
#  GA メイン
# =========================================
def genetic_algorithm(data, genre_col, generations=50, pop_size=40,
                      mutation_rate=0.1,
                      close_range=5,
                      penalty_weight=1000,
                      close_weight=500,
                      distance_weight=0.1,
                      elite_ratio=0.1,
                      seed=None):
    ensure_output_dir()

    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    if not data:
        print("エラー: データがありません")
        sys.exit(1)

    pop_size = max(2, int(pop_size))
    generations = max(1, int(generations))
    elite_ratio = min(max(float(elite_ratio), 0.0), 1.0)
    mutation_rate = min(max(float(mutation_rate), 0.0), 1.0)

    eval_conf = dict(
        close_range=close_range,
        penalty_weight=penalty_weight,
        close_weight=close_weight,
        distance_weight=distance_weight,
    )

    population = init_population(data, pop_size)
    id_to_item = {item["ID"]: item for item in data}

    global_best = None
    global_best_score = None
    global_best_gen = 1

    scores = []
    elite_count = max(1, int(pop_size * elite_ratio))

    for gen in range(1, generations + 1):
        scored_pop = [(indiv, evaluate(indiv, genre_col, **eval_conf)) for indiv in population]
        scored_pop.sort(key=lambda x: (x[1]["total"], x[1]["penalty"], x[1]["close_penalty"], -x[1]["distance"]))

        elites = [indiv[:] for indiv, _ in scored_pop[:elite_count]]

        best = elites[0]
        best_score = scored_pop[0][1]
        scores.append(best_score["total"])

        print(f"\n=== Generation {gen} ===")
        print(best_score)

        if global_best is None or is_better(best, global_best, genre_col, eval_conf):
            global_best = best[:]
            global_best_score = best_score.copy()
            global_best_gen = gen

        new_pop = elites[:]

        while len(new_pop) < pop_size:
            p1 = tournament_selection(population, genre_col, eval_conf)
            p2 = tournament_selection(population, genre_col, eval_conf)
            child = crossover_pmx(p1, p2, id_to_item)
            child = mutate(child, rate=mutation_rate)
            new_pop.append(child)

        unique = {}
        for indiv in new_pop:
            key = tuple(item["ID"] for item in indiv)
            if key not in unique:
                unique[key] = indiv
        population = list(unique.values())

        while len(population) < pop_size:
            population.append(random.sample(data, len(data)))

        save_latest_results(best, best_score, gen)

    plt.figure(figsize=(10, 4))
    plt.plot(range(1, len(scores) + 1), scores)
    plt.xlabel("Generation")
    plt.ylabel("Total Score (lower is better)")
    plt.title("Score Transition")
    plt.tight_layout()
    plt.savefig("output/score_graph.png", dpi=200)
    plt.close()

    save_heatmap(global_best, genre_col)

    print(f"\n=== 全世代で最も total が低かった個体（Generation {global_best_gen}） ===")
    print(global_best_score)

    save_latest_results(global_best, global_best_score, global_best_gen)

    return global_best


# =========================================
#  引数パース
# =========================================
def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="ジャンルの偏りが少ないクイズ問題の並び順を GA で探索します。"
    )
    parser.add_argument("input_csv", help="入力 CSV ファイル")
    parser.add_argument("generations", nargs="?", type=int, default=50, help="世代数")
    parser.add_argument("--close-range", type=int, default=5, help="何問以内の同ジャンルを近距離とみなすか")
    parser.add_argument("--penalty-weight", type=float, default=1000, help="連続ペナルティの重み")
    parser.add_argument("--close-weight", type=float, default=500, help="近距離ペナルティの重み")
    parser.add_argument("--distance-weight", type=float, default=0.1, help="距離スコアの重み")
    parser.add_argument("--mutation-rate", type=float, default=0.1, help="突然変異率")
    parser.add_argument("--elite-ratio", type=float, default=0.1, help="エリート保存率")
    parser.add_argument("--pop-size", type=int, default=40, help="個体数")
    parser.add_argument("--seed", type=int, default=None, help="乱数シード")
    args = parser.parse_args(argv)

    params = {
        "close_range": args.close_range,
        "penalty_weight": args.penalty_weight,
        "close_weight": args.close_weight,
        "distance_weight": args.distance_weight,
        "mutation_rate": args.mutation_rate,
        "elite_ratio": args.elite_ratio,
        "pop_size": args.pop_size,
        "seed": args.seed,
    }
    return args.input_csv, args.generations, params


# =========================================
#  メイン
# =========================================
def main():
    input_csv, generations, params = parse_args()

    print(f"世代数: {generations}")
    print("評価パラメータ:", params)

    data, genre_col = load_csv(input_csv)

    genetic_algorithm(
        data,
        genre_col,
        generations=generations,
        pop_size=params["pop_size"],
        mutation_rate=params["mutation_rate"],
        close_range=params["close_range"],
        penalty_weight=params["penalty_weight"],
        close_weight=params["close_weight"],
        distance_weight=params["distance_weight"],
        elite_ratio=params["elite_ratio"],
        seed=params["seed"],
    )

    print("\n=== 完了 ===")
    print("output/result.csv / output/score.txt / output/score_graph.png / output/heatmap.png を出力しました")


if __name__ == "__main__":
    main()
