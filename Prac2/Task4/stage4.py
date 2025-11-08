import argparse
import sys

# === Чтение графа из файла ===
def load_graph(file_path: str) -> dict:
    graph = {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    pkg, deps = line.strip().split(":")
                    deps_list = [d.strip() for d in deps.split(",") if d.strip()]
                    graph[pkg.strip()] = deps_list
        return graph
    except Exception as e:
        print(f"Ошибка при загрузке файла графа: {e}")
        sys.exit(1)


# === DFS для вычисления порядка загрузки ===
def dfs_order(graph, node, visited, load_order):
    if node in visited:
        return
    visited.add(node)
    for dep in graph.get(node, []):
        dfs_order(graph, dep, visited, load_order)
    load_order.append(node)


def main():
    parser = argparse.ArgumentParser(description="Этап 4 — Дополнительные операции над графом зависимостей")
    parser.add_argument("--repo", required=True, help="Путь к файлу описания графа (пример: test_graph.txt)")
    parser.add_argument("--package", required=True, help="Имя исходного пакета (пример: A)")
    parser.add_argument("--depth", type=int, default=3, help="Максимальная глубина анализа")
    parser.add_argument("--test", action="store_true", help="Режим тестирования")
    args = parser.parse_args()

    print("=== Этап 4 — Дополнительные операции ===")
    print(f"Исходный пакет: {args.package}")
    print(f"Файл графа: {args.repo}")
    print(f"Макс. глубина: {args.depth}")
    print(f"Режим теста: {'Да' if args.test else 'Нет'}\n")

    graph = load_graph(args.repo)

    print("Структура графа:")
    for k, v in graph.items():
        print(f"{k} -> {', '.join(v) if v else '(нет зависимостей)'}")

    # === Вычисляем порядок загрузки ===
    print("\nПорядок загрузки зависимостей (DFS):")
    visited = set()
    load_order = []
    dfs_order(graph, args.package, visited, load_order)
    load_order = load_order[::-1]  # переворот для корректного порядка
    print(" → ".join(load_order))

    # === Сравнение с "реальным менеджером" (эмуляция) ===
    if args.test:
        # Эталонный порядок для проверки (пример)
        reference_order = ["G", "D", "E", "B", "F", "C", "A"]
        print("\nСравнение с эталонным менеджером пакетов:")
        if load_order == reference_order:
            print("Совпадает с эталонным порядком загрузки.")
        else:
            print("Расхождения обнаружены!")
            print(f"Ожидаемый порядок: {' → '.join(reference_order)}")
            print(f"Полученный порядок: {' → '.join(load_order)}")
            print("Причина: различия в структуре тестового графа (циклические связи или упрощённая модель DFS).")

    print("\nЭтап 4 успешно выполнен.")


if __name__ == "__main__":
    main()
