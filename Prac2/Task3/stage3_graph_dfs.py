import argparse
import sys

# === Чтение графа из файла ===
def load_graph(file_path: str) -> dict:
    """
    Загружает описание графа зависимостей из файла.
    Формат строк:
    A: B, C
    B: D
    C:
    D:
    """
    graph = {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    package, deps = line.strip().split(":")
                    deps_list = [d.strip() for d in deps.split(",") if d.strip()]
                    graph[package.strip()] = deps_list
        return graph
    except Exception as e:
        print(f"Ошибка при загрузке файла графа: {e}")
        sys.exit(1)


# === DFS с учётом глубины и циклов ===
def dfs(graph, node, visited, depth, max_depth):
    """
    Рекурсивный обход графа в глубину.
    """
    if node in visited:
        print(f"Циклическая зависимость обнаружена: {node}")
        return

    if depth > max_depth:
        return

    visited.add(node)
    print("  " * depth + f"- {node}")

    for neighbor in graph.get(node, []):
        dfs(graph, neighbor, visited.copy(), depth + 1, max_depth)


def main():
    parser = argparse.ArgumentParser(description="Этап 3 — Построение графа зависимостей (вариант 20)")
    parser.add_argument("--repo", required=True, help="Путь к файлу с описанием графа (пример: test_graph.txt)")
    parser.add_argument("--package", required=True, help="Имя исходного пакета (пример: A)")
    parser.add_argument("--depth", type=int, default=3, help="Максимальная глубина анализа зависимостей")
    parser.add_argument("--test", action="store_true", help="Режим тестирования")

    args = parser.parse_args()

    print("=== Построение графа зависимостей ===")
    print(f"Исходный пакет: {args.package}")
    print(f"Файл графа: {args.repo}")
    print(f"Макс. глубина: {args.depth}")
    print(f"Режим теста: {'Да' if args.test else 'Нет'}\n")

    graph = load_graph(args.repo)
    print("Структура графа:")
    for k, v in graph.items():
        print(f"{k} -> {', '.join(v) if v else '(нет зависимостей)'}")
    print("\nОбход в глубину (DFS):")

    dfs(graph, args.package, set(), 0, args.depth)
    print("\nЭтап 3 успешно выполнен")


if __name__ == "__main__":
    main()
