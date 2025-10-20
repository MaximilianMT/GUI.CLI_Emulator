import argparse
import sys
import re

def validate_args(args):
    errors = []

    # Проверяем package
    if not re.match(r"^[a-zA-Z0-9._-]+$", args.package):
        errors.append("Недопустимое имя пакета (--package).")

    # Проверяем repo (должен начинаться с http:// или https://)
    if not (args.repo.startswith("http://") or args.repo.startswith("https://")):
        errors.append("Параметр --repo должен быть ссылкой на APT-репозиторий (http или https).")

    # Проверяем версию (цифры и точки)
    if not re.match(r"^[0-9]+(\.[0-9]+)*$", args.version):
        errors.append("Неверный формат версии (--version). Пример: 1.0 или 6.2")

    # Проверяем глубину (целое число >=1)
    if args.depth < 1:
        errors.append("Глубина (--depth) должна быть больше 0.")

    if errors:
        print("=== Обнаружены ошибки параметров ===")
        for e in errors:
            print(e)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Этап 1 — Минимальный CLI-прототип (вариант 20)")
    parser.add_argument("--package", required=True, help="Имя анализируемого пакета")
    parser.add_argument("--repo", required=True, help="APT-репозиторий Ubuntu (пример: http://ru.archive.ubuntu.com/ubuntu)")
    parser.add_argument("--test", action="store_true", help="Режим тестирования")
    parser.add_argument("--version", required=True, help="Версия пакета (пример: 6.2)")
    parser.add_argument("--depth", type=int, default=1, help="Максимальная глубина анализа")

    args = parser.parse_args()
    validate_args(args)

    print("=== Настройки анализа ===")
    print(f"Имя пакета: {args.package}")
    print(f"APT-репозиторий: {args.repo}")
    print(f"Режим теста: {'Да' if args.test else 'Нет'}")
    print(f"Версия: {args.version}")
    print(f"Глубина анализа: {args.depth}")
    print("\nВсе параметры успешно проверены")



if __name__ == "__main__":
    main()
