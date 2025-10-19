import argparse
import sys

def parse_args():
    parser = argparse.ArgumentParser(
        description="CLI-приложение для визуализации зависимостей (вариант №20)"
    )
    parser.add_argument("--package", required=True, help="Имя анализируемого пакета")
    parser.add_argument("--repo", required=True, help="URL репозитория или путь к файлу")
    parser.add_argument("--test", action="store_true", help="Режим работы с тестовым репозиторием")
    parser.add_argument("--version", required=True, help="Версия пакета")
    parser.add_argument("--depth", type=int, default=1, help="Максимальная глубина анализа зависимостей")
    return parser.parse_args()

def main():
    try:
        args = parse_args()
        print("=== Настройки анализа ===")
        print(f"Имя пакета: {args.package}")
        print(f"Репозиторий: {args.repo}")
        print(f"Режим теста: {'Да' if args.test else 'Нет'}")
        print(f"Версия: {args.version}")
        print(f"Глубина анализа: {args.depth}")
        print("\nВсе параметры успешно обработаны")
    except Exception as e:
        print(f"\nОшибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
