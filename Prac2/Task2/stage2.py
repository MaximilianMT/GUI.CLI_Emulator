import argparse
import sys
import re
import gzip
from io import BytesIO
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError


def fetch_package_info(repo_url: str, package_name: str, version: str) -> str:
    """
    Получает данные Packages (APT формат) из репозитория Ubuntu или локального файла.
    Поддерживает автоматическую подстановку пути и распаковку .gz.
    """
    try:
        # [ДОБАВЛЕНО] Автоматическое добавление пути к Packages-файлу Ubuntu
        if repo_url.startswith("http"):
            if not repo_url.endswith("Packages") and not repo_url.endswith("Packages.gz"):
                repo_url = repo_url.rstrip("/") + "/dists/jammy/main/binary-amd64/Packages"
                print(f"(Автоматически добавлен путь к Packages: {repo_url})")

            req = Request(repo_url, headers={"User-Agent": "APT-Stage2/1.0"})
            try:
                with urlopen(req) as response:
                    # [ДОБАВЛЕНО] Если обычный Packages не найден — пробуем Packages.gz
                    if response.status == 404:
                        gz_url = repo_url + ".gz"
                        print(f"Packages не найден, пробуем {gz_url}")
                        with urlopen(gz_url) as gz_resp:
                            compressed = gz_resp.read()
                            data = gzip.decompress(compressed).decode("utf-8", errors="ignore")
                            return data

                    # [ДОБАВЛЕНО] Проверка типа контента и автоматическая распаковка
                    data = response.read()
                    content_type = response.getheader("Content-Type", "")
                    if "gzip" in content_type or repo_url.endswith(".gz"):
                        data = gzip.decompress(data)
                    data = data.decode("utf-8", errors="ignore")

            except HTTPError as e:
                if e.code == 404 and not repo_url.endswith(".gz"):
                    # [ДОБАВЛЕНО] Попытка скачать сжатую версию Packages.gz
                    gz_url = repo_url + ".gz"
                    print(f"Packages не найден, пробуем {gz_url}")
                    with urlopen(gz_url) as gz_resp:
                        compressed = gz_resp.read()
                        data = gzip.decompress(compressed).decode("utf-8", errors="ignore")
                        return data
                else:
                    print(f"Ошибка HTTP: {e.code} — {e.reason}")
                    sys.exit(1)
            except URLError as e:
                print(f"Ошибка соединения: {e.reason}")
                sys.exit(1)

        else:
            # [ИЗМЕНЕНО] Чтение локального Packages-файла
            with open(repo_url, "rb") as f:
                raw = f.read()
                if repo_url.endswith(".gz"):
                    raw = gzip.decompress(raw)
                data = raw.decode("utf-8", errors="ignore")

        if not data.strip():
            print("Ошибка: файл Packages пуст или не содержит данных.")
            sys.exit(1)

        return data

    except FileNotFoundError:
        print("Ошибка: указанный локальный файл не найден.")
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка при чтении данных: {e}")
        sys.exit(1)


def parse_dependencies(package_data: str, package_name: str, version: str):
    """
    Извлекает зависимости пакета из данных формата APT.
    """
    # [ИЗМЕНЕНО] Шаблон поиска пакета (APT формат)
    pattern = rf"Package:\s*{re.escape(package_name)}\s*\nVersion:\s*{re.escape(version)}(.*?)(?:\nPackage:|\Z)"
    match = re.search(pattern, package_data, re.DOTALL)

    if not match:
        print(f"Пакет '{package_name}' версии {version} не найден в Packages.")
        return []

    block = match.group(1)
    dep_match = re.search(r"Depends:\s*(.+)", block)

    if not dep_match:
        print("У пакета нет прямых зависимостей.")
        return []

    deps = dep_match.group(1).split(",")
    # [ДОБАВЛЕНО] Очистка зависимостей от версий (>=, <=)
    deps = [re.sub(r"\s*\(.*?\)", "", d.strip()).split(" ")[0] for d in deps]
    return deps


def validate_args(args):
    """Проверка корректности аргументов"""
    errors = []
    if not re.match(r"^[a-zA-Z0-9._+-]+$", args.package):
        errors.append("Неверное имя пакета (--package). Используйте латиницу, цифры, точки или тире.")
    if not (args.repo.startswith("http://") or args.repo.startswith("https://")
            or args.repo.endswith("Packages") or args.repo.endswith(".gz") or args.repo.endswith(".txt")):
        errors.append("Неверный формат --repo. Укажите URL APT-репозитория (http...) или путь к Packages/Packages.gz.")
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

    # [ДОБАВЛЕНО] Проверка аргументов
    validate_args(args)

    print("=== Сбор данных о зависимостях ===")
    print(f"Пакет: {args.package}")
    print(f"Версия: {args.version}")
    print(f"Источник данных: {args.repo}")

    package_data = fetch_package_info(args.repo, args.package, args.version)
    deps = parse_dependencies(package_data, args.package, args.version)

    if deps:
        print("\nПрямые зависимости (APT формат):")
        for dep in deps:
            print(f" - {dep}")
    else:
        print("\nЗависимости не найдены.")

    print("\nЭтап 2 успешно выполнен")


if __name__ == "__main__":
    main()
