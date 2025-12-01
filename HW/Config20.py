#!/usr/bin/env python3
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom # Добавили новую библ для красивого вывода XML формата (с табуляцией)


# ИСКЛЮЧЕНИЕ ДЛЯ ОШИБОК
class ParseError(Exception):
    def __init__(self, message, line, col):
        super().__init__(message)
        self.line = line
        self.col = col

# ЛЕКСЕР
class Token:
    def __init__(self, kind, value, line, col):
        self.kind = kind      # тип токена, например "NUMBER", "NAME", "{"
        self.value = value    # строковое значение
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.kind}, {self.value!r}, {self.line}:{self.col})"


class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.length = len(text)

    def _advance(self, n=1):
        for _ in range(n):
            if self.pos >= self.length:
                return
            ch = self.text[self.pos]
            self.pos += 1
            if ch == '\n':
                self.line += 1
                self.col = 1
            else:
                self.col += 1

    def _peek(self, n=0):
        idx = self.pos + n
        if idx >= self.length:
            return ''
        return self.text[idx]

    def tokens(self):
        result = []
        while self.pos < self.length:
            ch = self._peek()

            # пропускаем пробелы и переводы строк
            if ch.isspace():
                self._advance()
                continue

            # однострочный комментарий: -- до конца строки
            if ch == '-' and self._peek(1) == '-':
                while self.pos < self.length and self._peek() != '\n':
                    self._advance()
                continue

            start_line, start_col = self.line, self.col

            # строка [[ ... ]]
            if ch == '[' and self._peek(1) == '[':
                self._advance(2)  # пропускаем [[
                start = self.pos
                # ищем ]]
                while True:
                    if self.pos >= self.length:
                        raise ParseError("незакрытая строка [[...]]", start_line, start_col)
                    if self._peek() == ']' and self._peek(1) == ']':
                        end = self.pos
                        value = self.text[start:end]
                        self._advance(2)  # ]]
                        result.append(Token("STRING", value, start_line, start_col))
                        break
                    else:
                        self._advance()
                continue

            # числа
            if ch.isdigit():
                start = self.pos
                while self._peek().isdigit():
                    self._advance()
                value = self.text[start:self.pos]
                result.append(Token("NUMBER", value, start_line, start_col))
                continue

            # идентификаторы / ключевое слово def
            if ch.isalpha():
                start = self.pos
                while self._peek().isalnum() or self._peek() == '_':
                    self._advance()
                value = self.text[start:self.pos]
                kind = "DEF" if value == "def" else "NAME"
                result.append(Token(kind, value, start_line, start_col))
                continue

            # двусимвольные символы: := и =>
            two = ch + self._peek(1)
            if two == ":=":
                self._advance(2)
                result.append(Token("ASSIGN", ":=", start_line, start_col))
                continue
            if two == "=>":
                self._advance(2)
                result.append(Token("ARROW", "=>", start_line, start_col))
                continue

            # одиночные символы
            single_tokens = "{}(),;."
            if ch in single_tokens:
                self._advance()
                result.append(Token(ch, ch, start_line, start_col))
                continue

            # неизвестный символ
            raise ParseError(f"неизвестный символ {ch!r}", start_line, start_col)

        # маркер конца входа
        result.append(Token("EOF", "", self.line, self.col))
        return result

# ПАРСЕР
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.env = {}  # таблица констант

    def _peek(self):
        return self.tokens[self.pos]

    def _match(self, kind):
        tok = self._peek()
        if tok.kind == kind:
            self.pos += 1
            return tok
        return None

    def _expect(self, kind):
        tok = self._peek()
        if tok.kind != kind:
            raise ParseError(f"ожидалось {kind}, найдено {tok.kind}", tok.line, tok.col)
        self.pos += 1
        return tok

    # program := { const_decl }* value EOF
    def parse_program(self):
        while self._peek().kind == "DEF":
            self.parse_const_decl()
        value = self.parse_value()
        eof = self._expect("EOF")
        return value

    # const_decl := "def" NAME ASSIGN value ";"
    def parse_const_decl(self):
        self._expect("DEF")
        name_tok = self._expect("NAME")
        self._expect("ASSIGN")
        value = self.parse_value()
        self._expect(";")
        if name_tok.value in self.env:
            raise ParseError(f"повторное объявление константы {name_tok.value!r}",
                             name_tok.line, name_tok.col)
        self.env[name_tok.value] = value

    # value := NUMBER | STRING | dict | const_ref
    def parse_value(self):
        tok = self._peek()

        if tok.kind == "NUMBER":
            self.pos += 1
            return int(tok.value)

        if tok.kind == "STRING":
            self.pos += 1
            return tok.value

        if tok.kind == "{":
            return self.parse_dict()

        if tok.kind == ".":   # .(NAME).
            return self.parse_const_ref()

        raise ParseError("ожидалось значение (число, строка, словарь или .(имя).)",
                         tok.line, tok.col)

    # dict := "{" [ entries ] "}"
    # entries := entry ("," entry)* [","]
    # entry := NAME ARROW value
    def parse_dict(self):
        self._expect("{")
        result = {}
        if self._peek().kind != "}":
            while True:
                key_tok = self._expect("NAME")
                self._expect("ARROW")
                val = self.parse_value()
                result[key_tok.value] = val
                if self._match(","):
                    if self._peek().kind == "}":
                        break
                    continue
                else:
                    break
        self._expect("}")
        return result

    # const_ref := "." "(" NAME ")" "."
    def parse_const_ref(self):
        dot1 = self._expect(".")
        self._expect("(")
        name_tok = self._expect("NAME")
        self._expect(")")
        self._expect(".")
        name = name_tok.value
        if name not in self.env:
            raise ParseError(f"неизвестная константа {name!r}", name_tok.line, name_tok.col)
        return self.env[name]

# ПРЕОБРАЗОВАНИЕ В XML
def value_to_xml(value):
    """Преобразует внутреннее представление в XML-элемент."""
    if isinstance(value, int):
        elem = ET.Element("number")
        elem.text = str(value)
        return elem
    if isinstance(value, str):
        elem = ET.Element("string")
        elem.text = value
        return elem
    if isinstance(value, dict):
        elem = ET.Element("dict")
        for key, val in value.items():
            entry = ET.SubElement(elem, "entry", name=key)
            entry.append(value_to_xml(val))
        return elem
    # на всякий случай
    elem = ET.Element("unknown")
    elem.text = repr(value)
    return elem

def translate(text: str) -> str:
    """Основная функция: текст -> красиво отформатированная XML-строка."""
    lexer = Lexer(text)
    tokens = lexer.tokens()
    parser = Parser(tokens)
    value = parser.parse_program()

    root = ET.Element("config")
    root.append(value_to_xml(value))

    # превращаем в строку без отступов
    rough_xml = ET.tostring(root, encoding="unicode")

    # добавляем красивую разбивку и отступы
    parsed = minidom.parseString(rough_xml)
    pretty = parsed.toprettyxml(indent="  ")

    # убираем пустые строки minidom
    pretty = "\n".join([line for line in pretty.split("\n") if line.strip()])

    return pretty

'''
def translate(text: str) -> str: # Старый вывод XML формат в строку
    """Основная функция: текст -> XML-строка."""
    lexer = Lexer(text)
    tokens = lexer.tokens()
    parser = Parser(tokens)
    value = parser.parse_program()

    root = ET.Element("config")
    root.append(value_to_xml(value))
    return ET.tostring(root, encoding="unicode")
'''
# MAIN
def main():
    src = sys.stdin.read()
    if not src.strip():
        return
    try:
        xml = translate(src)
        print(xml)
    except ParseError as e:
        print(f"Syntax error at line {e.line}, column {e.col}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
