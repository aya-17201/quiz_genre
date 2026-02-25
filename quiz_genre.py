import pandas as pd
import random
import sys
import os
from collections import defaultdict

# ==========================
#  CSV 読み込み（文字コード自動判定 + ジャンル列検出）
# ==========================
def load_csv(path):
    df = None

    # --- UTF-8 ---
    try:
        df = pd.read_csv(path, encoding="utf-8")
        print("文字コード: UTF-8")
    except UnicodeDecodeError:
        # --- UTF-8(BOM) ---
        try:
            df = pd.read_csv(path, encoding="utf-8-sig")
            print("文字コード: UTF-8(BOM)")
        except UnicodeDecodeError:
            # --- Shift-JIS ---
            try:
                df = pd.read_csv(path, encoding="shift_jis")
                print("文字コード: Shift-JIS → UTF-8 に変換します")
            except UnicodeDecodeError:
                print("エラー: 文字コードがUTF-8ではありません")
                sys.exit(1)

    # --- ジャンル列の自動検出 ---
    genre_col = None
    for col in df.columns:
        if "ジャンル" in col:
            genre_col = col
            break

    if genre_col is None:
        print("エラー: ジャンルがありません")
        sys.exit(1)

    print(f"検出されたジャンル列: {genre_col}")

    records = df.to_dict(orient="records")
    return records, genre_col


# ==========================
#  評価関数（内訳も返す）
# ==========================
def penalty_consecutive(genres):
    return sum(1 for i in range(len(genres)-1) if genres[i] == genres[i+1])


def transition_diversity(genres):
    return len({(genres[i], genres[i+1]) for i in range(len(genres)-1)})


def distance_score(genres):
    positions = defaultdict(list)
    for idx, g in enumerate(genres):
        positions[g].append(idx)

    score = 0
    for g, pos_list in positions.items():
        for i in range(len(pos_list)):
            for j in range(i+1, len(pos_list)):
                score += abs(pos_list[j] - pos_list[i])
    return score


def evaluate(sequence, genre_col):
    genres = [item[genre_col] for item in sequence]

    p = penalty_consecutive(genres)
    t = transition_diversity(genres)
    d = distance_score(genres)
    total = -p + t + d * 0.1

    return {
        "penalty": p,
        "transition": t,
        "distance": d,
        "total": total
    }


# ==========================
#  GA（遺伝的アルゴリズム）
# ==========================
def init_population(data, size=50):
    return [random.sample(data, len(data)) for _ in range(size)]


def tournament_selection(pop, genre_col, k=3):
    best = None
    for _ in range(k):
        indiv = random.choice(pop)
        if best is None or evaluate(indiv, genre_col)["total"] < evaluate(best, genre_col)["total"]:
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


# ==========================
#  出力フォルダ作成
# ==========================
def ensure_output_dirs():
    os.makedirs("output", exist_ok=True)
    os.makedirs("output/logs", exist_ok=True)


# ==========================
#  世代ごとのログ保存
# ==========================
def save_generation_log(gen, best, score_dict):
    gen_dir = f"output/logs/gen_{gen:03}"
    os.makedirs(gen_dir, exist_ok=True)

    # gen_XXX.txt
    log_path = f"{gen_dir}/gen_{gen:03}.txt"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"Generation: {gen}\n")
        f.write(f"Penalty: {score_dict['penalty']}\n")
        f.write(f"Transition: {score_dict['transition']}\n")
        f.write(f"Distance: {score_dict['distance']}\n")
        f.write(f"Total Score: {score_dict['total']}\n\n")
        f.write("Best Individual:\n")
        for row in best:
            f.write(str(row) + "\n")

    # result_gen_XXX.csv
    df_out = pd.DataFrame(best)
    df_out.to_csv(f"{gen_dir}/result_gen_{gen:03}.csv", index=False)

    print(f"[LOG] Gen {gen}: {gen_dir} に保存しました")


# ==========================
#  最新結果保存
# ==========================
def save_latest_results(best, score_dict):
    df_out = pd.DataFrame(best)
    df_out.to_csv("output/result.csv", index=False)

    with open("output/score.txt", "w", encoding="utf-8") as f:
        f.write(f"Penalty: {score_dict['penalty']}\n")
        f.write(f"Transition: {score_dict['transition']}\n")
        f.write(f"Distance: {score_dict['distance']}\n")
        f.write(f"Total Score: {score_dict['total']}\n")


# ==========================
#  GA メイン（毎世代表示）
# ==========================
def genetic_algorithm(data, genre_col, generations=50, pop_size=40):
    ensure_output_dirs()
    population = init_population(data, pop_size)

    for gen in range(1, generations + 1):
        new_pop = []

        for _ in range(pop_size):
            p1 = tournament_selection(population, genre_col)
            p2 = tournament_selection(population, genre_col)
            child = mutate(crossover(p1, p2))
            new_pop.append(child)

        population = new_pop

        best = max(population, key=lambda x: evaluate(x, genre_col)["total"])
        score_dict = evaluate(best, genre_col)

        # ★★★ 毎世代表示 ★★★
        print(f"\n=== Generation {gen} ===")
        print(f"Penalty: {score_dict['penalty']}")
        print(f"Transition: {score_dict['transition']}")
        print(f"Distance: {score_dict['distance']}")
        print(f"Total Score: {score_dict['total']}")

        # 保存
        save_generation_log(gen, best, score_dict)
        save_latest_results(best, score_dict)

    return best


# ==========================
#  メイン処理
# ==========================
def main():
    if len(sys.argv) < 2:
        print("Usage: python quiz_ga.py input.csv [generations]")
        sys.exit(1)

    input_csv = sys.argv[1]
    generations = int(sys.argv[2]) if len(sys.argv) >= 3 else 50

    print(f"世代数: {generations}")

    data, genre_col = load_csv(input_csv)

    best = genetic_algorithm(data, genre_col, generations=generations, pop_size=40)

    print("\n=== 完了 ===")
    print("output/result.csv / output/score.txt / output/logs/ を出力しました")


if __name__ == "__main__":
    main()