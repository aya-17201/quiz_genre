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
    encodings = ["utf-8", "utf-8-sig", "shift_jis"]
    df = None

    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc)
            print(f"文字コード: {enc}")
            break
        except Exception:
            continue

    if df is None:
        print("エラー: 対応していない文字コードです")
        sys.exit(1)

    # ジャンル列の検出
    genre_col = None
    for col in df.columns:
        if "ジャンル" in col or "genre" in col.lower():
            genre_col = col
            break

    if genre_col is None:
        print("エラー: ジャンル列が見つかりません")
        sys.exit(1)

    # ID が無い場合に自動付与
    if "ID" not in df.columns:
        df["ID"] = range(1, len(df) + 1)

    return df.to_dict(orient="records"), genre_col


# =========================================
#  評価関数（ratio なし・total は 0 以上）
# =========================================
eval_cache = {}

def evaluate(sequence, genre_col,
             close_range=5,
             penalty_weight=1000,
             close_weight=500,
             distance_weight=0.1):

    key = (
        tuple(item["ID"] for item in sequence),
        genre_col,
        close_range,
        penalty_weight,
        close_weight,
        distance_weight,
    )

    if key in eval_cache:
        return eval_cache[key]

    genres = [item[genre_col] for item in sequence]
    n = len(genres)

    # ① 同ジャンル連続
    penalty = sum(genres[i] == genres[i + 1] for i in range(n - 1))

    # ② close_range 以内の同ジャンル
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

    # ④ 最大距離（近似）
    max_distance = n * (n - 1) / 2
    distance_term = max(max_distance - dist, 0)

    total = (
        penalty * penalty_weight +
        close_penalty * close_weight +
        distance_term * distance_weight
    )

    result = {
        "penalty": penalty,
        "close_penalty": close_penalty,
        "distance": dist,
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

    if ea["total"] != eb["total"]:
        return ea["total"] < eb["total"]
    if ea["penalty"] != eb["penalty"]:
        return ea["penalty"] < eb["penalty"]
    if ea["close_penalty"] != eb["close_penalty"]:
        return ea["close_penalty"] < eb["close_penalty"]
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


# ---------- PMX 交叉（ID ベース） ----------
def pmx_crossover_ids(parent1_ids, parent2_ids):
    size = len(parent1_ids)
    a, b = sorted(random.sample(range(size), 2))
    child = [None] * size

    # 区間コピー
    child[a:b] = parent1_ids[a:b]

    # マッピング処理
    for i in range(a, b):
        val2 = parent2_ids[i]
        if val2 in child:
            continue
        pos = i
        while True:
            val1 = parent1_ids[pos]
            pos = parent2_ids.index(val1)
            if child[pos] is None:
                child[pos] = val2
                break

    # 残りを parent2 から埋める
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
    op = random.choice(["swap", "scramble", "inversion"])

    if op == "swap":
        i, j = random.sample(range(n), 2)
        indiv[i], indiv[j] = indiv[j], indiv[i]

    elif op == "scramble":
        i, j = sorted(random.sample(range(n), 2))
        segment = indiv[i:j]
        random.shuffle(segment)
        indiv[i:j] = segment

    elif op == "inversion":
        i, j = sorted(random.sample(range(n), 2))
        segment = list(reversed(indiv[i:j]))
        indiv[i:j] = segment

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
    ensure_output_dir()
    try:
        pd.DataFrame(best).to_csv("output/result.csv", index=False)
    except Exception as e:
        print(f"CSV 保存エラー: {e}")

    try:
        with open("output/score.txt", "w", encoding="utf-8") as f:
            f.write(f"Generation: {gen}\n")
            for k, v in score_dict.items():
                f.write(f"{k}: {v}\n")
    except Exception as e:
        print(f"score.txt 保存エラー: {e}")


# =========================================
#  ヒートマップ
# =========================================
def save_heatmap(best, genre_col):
    ensure_output_dir()

    genres = [item[genre_col] for item in best]
    unique = list(sorted(set(genres)))
    mapping = {g: i for i, g in enumerate(unique)}
    arr = np.array([[mapping[g] for g in genres]])

    plt.figure(figsize=(18, 2))
    plt.imshow(arr, cmap="tab20b", aspect="auto")
    plt.colorbar()
    plt.title("Genre Heatmap")
    plt.tight_layout()
    plt.savefig("output/heatmap.png", dpi=200)
    plt.close()


# =========================================
#  GA メイン（PMX + エリート保存 + 多様性維持）
# =========================================
def genetic_algorithm(data, genre_col, generations=50, pop_size=40,
                      mutation_rate=0.1,
                      close_range=5,
                      penalty_weight=1000,
                      close_weight=500,
                      distance_weight=0.1,
                      elite_ratio=0.1):

    ensure_output_dir()

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
        # 個体を評価してソート
        scored_pop = [
            (indiv, evaluate(indiv, genre_col, **eval_conf))
            for indiv in population
        ]
        scored_pop.sort(key=lambda x: x[1]["total"])

        # エリート保存
        elites = [indiv for indiv, _ in scored_pop[:elite_count]]

        best = elites[0]
        best_score = scored_pop[0][1]
        scores.append(best_score["total"])

        print(f"\n=== Generation {gen} ===")
        print(best_score)

        if global_best is None or is_better(best, global_best, genre_col, eval_conf):
            global_best = best
            global_best_score = best_score
            global_best_gen = gen

        new_pop = elites[:]  # エリートをそのまま次世代へ

        # 残りを生成
        while len(new_pop) < pop_size:
            p1 = tournament_selection(population, genre_col, eval_conf)
            p2 = tournament_selection(population, genre_col, eval_conf)
            child = crossover_pmx(p1, p2, id_to_item)
            child = mutate(child, rate=mutation_rate)
            new_pop.append(child)

        # 多様性維持：重複個体の排除
        unique = {}
        for indiv in new_pop:
            key = tuple(item["ID"] for item in indiv)
            if key not in unique:
                unique[key] = indiv
        population = list(unique.values())

        # 個体数が減った場合はランダム個体を追加
        while len(population) < pop_size:
            population.append(random.sample(data, len(data)))

        save_latest_results(best, best_score, gen)

    # スコア推移グラフ
    plt.figure(figsize=(10, 4))
    plt.plot(scores)
    plt.xlabel("Generation")
    plt.ylabel("Total Score (lower is better)")
    plt.title("Score Transition")
    plt.tight_layout()
    plt.savefig("output/score_graph.png", dpi=200)
    plt.close()

    # ヒートマップ
    save_heatmap(global_best, genre_col)

    print(f"\n=== 全世代で最も total が低かった個体（Generation {global_best_gen}） ===")
    print(global_best_score)

    save_latest_results(global_best, global_best_score, global_best_gen)

    return global_best


# =========================================
#  引数パース（ratio なし）
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
        "distance_weight": 0.1,
        "mutation_rate": 0.1,
        "elite_ratio": 0.1,
    }

    def get_value(argv, idx):
        if idx + 1 >= len(argv):
            print(f"エラー: {argv[idx]} の値がありません")
            sys.exit(1)
        return argv[idx + 1]

    while idx < len(argv):
        arg = argv[idx]
        if arg == "--close-range":
            params["close_range"] = int(get_value(argv, idx))
            idx += 2
        elif arg == "--penalty-weight":
            params["penalty_weight"] = float(get_value(argv, idx))
            idx += 2
        elif arg == "--close-weight":
            params["close_weight"] = float(get_value(argv, idx))
            idx += 2
        elif arg == "--distance-weight":
            params["distance_weight"] = float(get_value(argv, idx))
            idx += 2
        elif arg == "--mutation-rate":
            params["mutation_rate"] = float(get_value(argv, idx))
            idx += 2
        elif arg == "--elite-ratio":
            params["elite_ratio"] = float(get_value(argv, idx))
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
        distance_weight=params["distance_weight"],
        elite_ratio=params["elite_ratio"],
    )

    print("\n=== 完了 ===")
    print("output/result.csv / output/score.txt / output/score_graph.png / output/heatmap.png を出力しました")


if __name__ == "__main__":
    main()
