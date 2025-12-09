import argparse
import re
import yaml


# ОШИБКИ
class ConfigError(Exception):
    pass


# ЛЕКСЕР
TOKEN_REGEX = [
    ("NUMBER", r"0[xX][0-9a-fA-F]+|\d+"),
    ("STRING", r'"[^"]*"'),
    ("LARRAY", r"<<"),
    ("RARRAY", r">>"),
    ("COMMA", r","),
    ("VAR", r"var"),
    ("ASSIGN", r":="),
    ("CONSTREF", r"!\{[A-Za-z_][A-Za-z0-9_]*\}"),
    ("IDENT", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("SKIP", r"[ \t\n]+"),
]


class Lexer:
    def __init__(self, text):
        self.text = text
        self.tokens = []
        self.build()

    def build(self):
        pos = 0
        while pos < len(self.text):
            match = None
            for token_name, pattern in TOKEN_REGEX:
                regex = re.compile(pattern)
                match = regex.match(self.text, pos)

                if match:
                    if token_name != "SKIP":
                        self.tokens.append((token_name, match.group()))
                    pos = match.end()
                    break

            if not match:
                raise ConfigError(f"Неизвестный символ: {self.text[pos]}")

        self.tokens.append(("EOF", None))


# EVALUATOR ( !{имя} )
class Evaluator:
    def __init__(self, variables):
        self.variables = variables

    def get(self, name):
        if name not in self.variables:
            raise ConfigError(f"Неизвестная константа {name}")
        return self.variables[name]


# ПАРСЕР
class ConfigParser:
    def __init__(self):
        self.variables = {}
        self.evaluator = Evaluator(self.variables)

    def parse(self, text):
        self.lexer = list(Lexer(text).tokens)
        self.pos = 0
        result = {}

        while not self._check("EOF"):
            self._parse_statement(result)

        return result

    def _parse_statement(self, result):
        if self._check("VAR"):
            self._consume("VAR")
            name = self._consume("IDENT")[1]
            self._consume("ASSIGN")
            value = self._parse_value()
            self.variables[name] = value
            result[name] = value
        else:
            raise ConfigError(f"Ожидалось var, получено {self._peek()}")

    def _parse_value(self):
        token, value = self._peek()

        if token == "NUMBER":
            self._consume("NUMBER")
            if value.lower().startswith("0x"):
                return int(value, 16)
            return int(value)

        if token == "STRING":
            self._consume("STRING")
            return value.strip('"')

        if token == "LARRAY":
            return self._parse_array()

        if token == "CONSTREF":
            self._consume("CONSTREF")
            name = value[2:-1]
            return self.evaluator.get(name)

        raise ConfigError(f"Недопустимое значение: {value}")

    def _parse_array(self):
        arr = []
        self._consume("LARRAY")

        while not self._check("RARRAY"):
            arr.append(self._parse_value())
            if self._check("COMMA"):
                self._consume("COMMA")

        self._consume("RARRAY")
        return arr

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------

    def _peek(self):
        return self.lexer[self.pos]

    def _check(self, kind):
        return self.lexer[self.pos][0] == kind

    def _consume(self, expected):
        tok = self.lexer[self.pos]
        if tok[0] != expected:
            raise ConfigError(f"Ожидалось {expected}, получено {tok}")
        self.pos += 1
        return tok



# CLI
def main():
    parser = argparse.ArgumentParser(description="Учебный конфигурационный язык → YAML")
    parser.add_argument("--input", "-i", help="Путь к файлу (.txt)", required=True)
    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            text = f.read()

        cp = ConfigParser()
        data = cp.parse(text)

        print(yaml.dump(data, allow_unicode=True))

    except ConfigError as e:
        print(f"[SYNTAX ERROR] {e}")
    except FileNotFoundError:
        print("Файл не найден")
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()
