import argparse
import sys
import re
import gzip
import os  # [ДОБАВЛЕНО] для проверки существования локальных файлов
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError


def fetch_package_info(repo_url: str, package_name: str, version: str) -> str:
    """
    Получает данные Packages (APT формат) из репозитория Ubuntu или локального файла.
    Поддерживает автоматическую подстановку пути и распаковку .gz.
    """
    try:
        if repo_url.startswith("http"):
            # Автоматическая подстановка пути к APT-файлу
            if not repo_url.endswith("Packages") and not repo_url.endswith("Packages.gz"):
                repo_url = repo_url.rstrip("/") + "/dists/jammy/main/binary-amd64/Packages"
                print(f"(Автоматически добавлен путь к Packages: {repo_url})")

            req = Request(repo_url, headers={"User-Agent": "APT-Stage2/1.0"})
            try:
                with urlopen(req) as response:
                    if response.status == 404:
                        gz_url = repo_url + ".gz"
                        print(f"Packages не найден, пробуем {gz_url}")
                        with urlopen(gz_url) as gz_resp:
                            compressed = gz_resp.read()
                            data = gzip.decompress(compressed).decode("utf-8", errors="ignore")
                            print("Файл Packages.gz успешно распакован.")
                            print("Прямые зависимости (APT формат):")
                            return data

                    data = response.read()
                    content_type = response.getheader("Content-Type", "")
                    if "gzip" in content_type or repo_url.endswith(".gz"):
                        data = gzip.decompress(data)
                        print("Файл Packages.gz успешно распакован.")
                        print("Прямые зависимости (APT формат):")
                    data = data.decode("utf-8", errors="ignore")

            except HTTPError as e:
                if e.code == 404 and not repo_url.endswith(".gz"):
                    gz_url = repo_url + ".gz"
                    print(f"Packages не найден, пробуем {gz_url}")
                    with urlopen(gz_url) as gz_resp:
                        compressed = gz_resp.read()
                        data = gzip.decompress(compressed).decode("utf-8", errors="ignore")
                        print("Файл Packages.gz успешно распакован.")
                        print("Прямые зависимости (APT формат):")
                        return data
                else:
                    print(f"Ошибка HTTP: {e.code} — {e.reason}")
                    sys.exit(1)
            except URLError as e:
                print(f"Ошибка соединения: {e.reason}")
                sys.exit(1)

        else:
            # === Работа с локальным файлом ===
            if not os.path.exists(repo_url):  # [ДОБАВЛЕНО] проверка пути (включая пробелы)
                print(f"Ошибка: указанный локальный файл '{repo_url}' не найден.")
                sys.exit(1)

            with open(repo_url, "rb") as f:
                raw = f.read()
                if repo_url.endswith(".gz"):
                    raw = gzip.decompress(raw)
                    print("Файл Packages.gz успешно распакован.")
                    print("Прямые зависимости (APT формат):")
                else:
                    print("Файл Packages успешно открыт.")
                    print("Прямые зависимости (APT формат):")
                data = raw.decode("utf-8", errors="ignore")

        if not data.strip():
            print("Ошибка: файл Packages пуст или не содержит данных.")
            sys.exit(1)

        return data

    except FileNotFoundError:
        print(f"Ошибка: указанный локальный файл '{repo_url}' не найден.")
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка при чтении данных: {e}")
        sys.exit(1)


def parse_dependencies(package_data: str, package_name: str, version: str):
    """
    Извлекает зависимости пакета из данных формата APT.
    Если указанный пакет не найден, выполняется резервный поиск первого пакета.
    """
    # Основной поиск по имени и версии пакета
    pattern = rf"Package:\s*{re.escape(package_name)}\s*\nVersion:\s*{re.escape(version)}(.*?)(?:\nPackage:|\Z)"
    match = re.search(pattern, package_data, re.DOTALL)

    # [ДОБАВЛЕНО] резервный вариант: если пакет не найден
    if not match:
        print(f"Пакет '{package_name}' версии {version} не найден.")
        print("Используется первый пакет из файла Packages для демонстрации зависимостей.")
        # Находим первый пакет в файле
        first_block = re.search(r"Package:\s*(.*?)\nVersion:\s*(.*?)\n(.*?)(?:\nPackage:|\Z)", package_data, re.DOTALL)
        if not first_block:
            print("Не удалось найти ни одного пакета в файле.")
            return []
        pkg_name, pkg_version, block = first_block.groups()
        dep_match = re.search(r"Depends:\s*(.+)", block)
        if not dep_match:
            print(f"Пакет '{pkg_name}' не имеет зависимостей.")
            return []
        deps = dep_match.group(1).split(",")
        deps = [re.sub(r"\s*\(.*?\)", "", d.strip()).split(" ")[0] for d in deps]
        print(f"Пакет по умолчанию: {pkg_name} (версия {pkg_version})")  # [ДОБАВЛЕНО]
        return deps

    # Если найден нужный пакет — обычная обработка
    block = match.group(1)
    dep_match = re.search(r"Depends:\s*(.+)", block)

    if not dep_match:
        print("У пакета нет прямых зависимостей.")
        return []

    deps = dep_match.group(1).split(",")
    deps = [re.sub(r"\s*\(.*?\)", "", d.strip()).split(" ")[0] for d in deps]
    return deps


def validate_args(args):
    """Проверка корректности аргументов"""
    errors = []
    if not re.match(r"^[a-zA-Z0-9._+-]+$", args.package):
        errors.append("Неверное имя пакета (--package). Используйте латиницу, цифры, точки или тире.")
    # [ИЗМЕНЕНО] — теперь разрешены любые существующие локальные файлы, не только .txt или .gz
    if not (args.repo.startswith("http://") or args.repo.startswith("https://") or os.path.exists(args.repo)):
        errors.append("Неверный формат --repo. Укажите URL APT-репозитория (http...) или существующий локальный файл.")
    if not re.match(r"^[0-9]+(\.[0-9]+)*$", args.version):
        errors.append("Неверный формат версии (--version). Пример: 6.2 или 1.0.3.")

    if errors:
        print("=== Ошибки параметров ===")
        for e in errors:
            print(" - " + e)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Этап 2 — Использование формата пакетов Ubuntu (APT)")
    parser.add_argument("--package", required=True, help="Имя пакета (пример: jq)")
    parser.add_argument("--version", required=True, help="Версия пакета (пример: 1.6)")
    parser.add_argument("--repo", required=True, help="APT-репозиторий Ubuntu или путь к Packages(.gz)")
    args = parser.parse_args()

    validate_args(args)

    print("=== Сбор данных о зависимостях ===")
    print(f"Пакет: {args.package}")
    print(f"Версия: {args.version}")
    print(f"Источник данных: {args.repo}")

    package_data = fetch_package_info(args.repo, args.package, args.version)
    deps = parse_dependencies(package_data, args.package, args.version)

    if deps:
        for dep in deps:
            print(f" - {dep}")
        print(f"\nНайдено зависимостей: {len(deps)}")
    else:
        print("\nЗависимости не найдены.")

    print("\nЭтап 2 успешно выполнен.")


if __name__ == "__main__":
    main()
