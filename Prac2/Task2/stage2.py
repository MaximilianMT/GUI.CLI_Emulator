import argparse
import sys
import re
from urllib.request import urlopen

def fetch_package_info(repo_url: str, package_name: str, version: str) -> str:
    """
    Получает (или имитирует получение) информации о пакете.
    В реальном случае данные берутся из Packages-файла репозитория Ubuntu.
    """
    try:
        # Для учебного примера попробуем считать URL (если он доступен)
        if repo_url.startswith("http"):
            with urlopen(repo_url) as response:
                data = response.read().decode("utf-8")
        else:
            # Если это локальный файл — читаем его содержимое
            with open(repo_url, "r", encoding="utf-8") as f:
                data = f.read()
        return data
    except Exception as e:
        print(f"Ошибка при чтении данных: {e}")
        sys.exit(1)


def parse_dependencies(package_data: str, package_name: str, version: str):
    """
    Извлекает зависимости из текста формата APT.
    """
    # Находим секцию с нужным пакетом и версией
    pattern = rf"Package:\s*{re.escape(package_name)}.*?Version:\s*{re.escape(version)}(.*?)Package:"
    match = re.search(pattern, package_data, re.DOTALL)
    if not match:
        print(f"Пакет '{package_name}' версии {version} не найден.")
        return []

    block = match.group(1)
    dep_match = re.search(r"Depends:\s*(.+)", block)
    if not dep_match:
        return []

    deps = dep_match.group(1).split(",")
    deps = [d.strip().split(" ")[0] for d in deps]
    return deps


def main():
    parser = argparse.ArgumentParser(description="Этап 2 — Сбор данных о зависимостях пакетов (вариант 20)")
    parser.add_argument("--package", required=True, help="Имя пакета (пример: nano)")
    parser.add_argument("--version", required=True, help="Версия пакета (пример: 6.2)")
    parser.add_argument("--repo", required=True, help="URL или путь к тестовому файлу Packages")
    args = parser.parse_args()

    print("=== Сбор данных о зависимостях ===")
    print(f"Пакет: {args.package}")
    print(f"Версия: {args.version}")
    print(f"Источник данных: {args.repo}")

    data = fetch_package_info(args.repo, args.package, args.version)
    deps = parse_dependencies(data, args.package, args.version)

    if deps:
        print("\nПрямые зависимости:")
        for dep in deps:
            print(f" - {dep}")
    else:
        print("\nЗависимости не найдены.")

    print("\nЭтап 2 успешно выполнен")


if __name__ == "__main__":
    main()
