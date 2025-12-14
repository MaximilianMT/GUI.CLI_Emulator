import argparse
import ast
from dataclasses import dataclass

import yaml
from lark import Lark, Transformer
from lark.exceptions import UnexpectedInput


class ConfigError(Exception):
    """Ошибки синтаксиса/семантики учебного конфигурационного языка."""


GRAMMAR = r"""
    start: statement*

    statement: "var" NAME ":=" value

    ?value: number
          | string
          | array
          | constref

    array: "<<" [value ("," value)*] ">>"

    number: HEXNUMBER
          | INT

    string: ESCAPED_STRING

    constref: "!{" NAME "}"

    NAME: /[_a-zA-Z][_a-zA-Z0-9]*/
    HEXNUMBER: /0[xX][0-9a-fA-F]+/

    %import common.INT
    %import common.ESCAPED_STRING
    %import common.WS

    %ignore WS
    %ignore /#[^\n]*/
"""


@dataclass
class ParseContext:
    variables: dict


class ToPython(Transformer):
    """Преобразует дерево разбора в Python-структуры и вычисляет !{name}."""

    def __init__(self, ctx: ParseContext):
        super().__init__()
        self.ctx = ctx

    def INT(self, tok):
        return int(tok)

    def HEXNUMBER(self, tok):
        return int(str(tok), 16)

    def ESCAPED_STRING(self, tok):
        # Lark возвращает строку с кавычками, используем literal_eval для экранирования.
        return ast.literal_eval(str(tok))

    def array(self, items):
        return list(items)

    def number(self, items):
        return items[0]

    def string(self, items):
        return items[0]

    def constref(self, items):
        # items = [NAME] (литералы "!{" и "}" не попадают в items)
        name = str(items[0])
        if name not in self.ctx.variables:
            raise ConfigError(f"Неизвестная константа {name}")
        return self.ctx.variables[name]

    def statement(self, items):
        # items = [NAME, value]
        name = str(items[0])
        value = items[1]
        self.ctx.variables[name] = value
        return name, value

    def start(self, statements):
        result = {}
        for st in statements:
            if st is None:
                continue
            k, v = st
            result[k] = v
        return result


def parse_config(text: str) -> dict:
    ctx = ParseContext(variables={})
    parser = Lark(
        GRAMMAR,
        parser="lalr",
        propagate_positions=True,
        maybe_placeholders=False,
    )
    try:
        tree = parser.parse(text)
        return ToPython(ctx).transform(tree)
    except UnexpectedInput as e:
        # Приведём сообщение к виду "строка:колонка ...".
        line = getattr(e, "line", None)
        column = getattr(e, "column", None)
        where = f" (строка {line}, колонка {column})" if line and column else ""
        raise ConfigError(f"Синтаксическая ошибка{where}: {e}") from e


def main():
    ap = argparse.ArgumentParser(description="Учебный конфигурационный язык → YAML")
    ap.add_argument("--input", "-i", help="Путь к файлу (.txt)", required=True)
    args = ap.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            text = f.read()

        data = parse_config(text)
        print(yaml.dump(data, allow_unicode=True, sort_keys=False))

    except ConfigError as e:
        print(f"[SYNTAX ERROR] {e}")
    except FileNotFoundError:
        print("Файл не найден")
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()
