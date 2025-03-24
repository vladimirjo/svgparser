from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .xmlchar import XmlChar
    from .xmlcharref import XmlCharRef


class XmlChars:
    def __init__(self, *xmlchars: XmlChars | XmlChar | XmlCharRef) -> None:
        self.strchars = ""
        self.xmlchars: list[XmlChar | XmlCharRef] = []
        if xmlchars:
            self.strchars = "".join([char.strchars for char in xmlchars])
            for xmlchar in xmlchars:
                if isinstance(xmlchar, XmlChars):
                    self.xmlchars.extend(xmlchar.xmlchars)
                else:
                    self.xmlchars.append(xmlchar)

    def __repr__(self) -> str:
        return self.strchars

    def __hash__(self):
        return hash(self.strchars)

    def __eq__(self, chars: str | XmlChars | XmlChar | XmlCharRef) -> bool:
        from .xmlchar import XmlChar
        from .xmlcharref import XmlCharRef

        if isinstance(chars, XmlChars | XmlChar | XmlCharRef):
            return self.strchars == chars.strchars
        if isinstance(chars, str):
            return self.strchars == chars
        return False

    def __getitem__(self, index: int | slice) -> XmlChars:
        if isinstance(index, int):
            return XmlChars(self.xmlchars[index])
        return XmlChars(*self.xmlchars[index])

    def __len__(self) -> int:
        return len(self.xmlchars)

    def add_entity_id(self, entity_id: int) -> None:
        for xmlchar in self.xmlchars:
            xmlchar.add_entity_id(entity_id)

    def copy_with_new_entity_id(self, new_entity_id: int) -> XmlChars:
        new_xmlchars: list[XmlChar | XmlCharRef] = [
            xmlchar.copy_with_new_entity_id(new_entity_id) for xmlchar in self.xmlchars
        ]
        return XmlChars(*new_xmlchars)

    def remove(self, start: int, end: int) -> None:
        if start < 0 or start >= len(self.xmlchars) or start >= end:
            return

        end = min(end, len(self.xmlchars))  # Clamp `end` to valid range

        self.strchars = self.strchars[:start] + self.strchars[end:]
        self.xmlchars = self.xmlchars[:start] + self.xmlchars[end:]

    def insert(self, xmlchar: XmlChar | XmlCharRef | XmlChars, pointer: int | None = None) -> None:
        if pointer is None:
            pointer = len(self.xmlchars)
        elif not (0 <= pointer <= len(self.xmlchars)):
            raise IndexError("Pointer out of bounds")
        if xmlchar:
            self.strchars = self.strchars[:pointer] + xmlchar.strchars + self.strchars[pointer:]
            if isinstance(xmlchar, XmlChars):
                self.xmlchars = self.xmlchars[:pointer] + xmlchar.xmlchars + self.xmlchars[pointer:]
            else:
                self.xmlchars = self.xmlchars[:pointer] + [xmlchar] + self.xmlchars[pointer:]

    def append(self, *xmlchars: XmlChar | XmlCharRef | XmlChars) -> None:
        if xmlchars:
            self.strchars += "".join([xmlchar.strchars for xmlchar in xmlchars])
            for xmlchar in xmlchars:
                if isinstance(xmlchar, XmlChars):
                    self.xmlchars.extend(xmlchar.xmlchars)
                else:
                    self.xmlchars.append(xmlchar)

    def match(self, text: str, offset: int = 0) -> bool:
        return self.strchars[offset : offset + len(text)] == text

    def is_space(self, offset: int = 0) -> bool:
        return self.strchars[offset].isspace()

    def is_namestartchar(self, char: str) -> bool:
        if len(char) != 1:
            return False
        codechar = ord(char)
        if codechar == ord(":"):
            return True
        if ord("A") <= codechar <= ord("Z"):
            return True
        if codechar == ord("_"):
            return True
        if ord("a") <= codechar <= ord("z"):
            return True
        if (
            0xC0 <= codechar <= 0xD6
            or 0xD8 <= codechar <= 0xF6
            or 0xF8 <= codechar <= 0x2FF
            or 0x370 <= codechar <= 0x37D
            or 0x37F <= codechar <= 0x1FFF
            or 0x200C <= codechar <= 0x200D
            or 0x2070 <= codechar <= 0x218F
            or 0x2C00 <= codechar <= 0x2FEF
            or 0x3001 <= codechar <= 0xD7FF
            or 0xF900 <= codechar <= 0xFDCF
            or 0xFDF0 <= codechar <= 0xFFFD
            or 0x10000 <= codechar <= 0xEFFFF
        ):
            return True
        return False

    def is_namechar(self, char: str) -> bool:
        if len(char) != 1:
            return False
        if self.is_namestartchar(char):
            return True
        codechar = ord(char)
        if codechar == ord("-"):
            return True
        if codechar == ord("."):
            return True
        if ord("0") <= codechar <= ord("9"):
            return True
        if codechar == 0xB7 or 0x0300 <= codechar <= 0x036F or 0x203F <= codechar <= 0x2040:
            return True
        return False

    def is_xmlname(self) -> bool:
        error_pointers: list[int] = []
        if not self.is_namestartchar(self.strchars[0]):
            error_pointers.append(0)
        i = 1
        while i < len(self.strchars):
            if not self.is_namechar(self.strchars[i]):
                error_pointers.append(i)
            i += 1
        if len(error_pointers) > 0:
            return False
        return True

    def is_nmtoken(self) -> bool:
        error_pointers: list[int] = []
        i = 0
        while i < len(self.strchars):
            if not self.is_namechar(self.strchars[i]):
                error_pointers.append(i)
            i += 1
        if len(error_pointers) > 0:
            return False
        return True

    def is_attvalue(self) -> bool:
        # both qoutes are already included in buffer separation
        error_pointers: list[int] = []
        i = 0
        while i < len(self.strchars):
            if self.strchars[i] == "<" or self.strchars[i] == "&":
                error_pointers.append(i)
            i += 1
        if len(error_pointers) > 0:
            return False
        return True

    def is_entityvalue(self) -> bool:
        # both qoutes are already included in buffer separation
        error_pointers: list[int] = []
        i = 0
        while i < len(self.strchars):
            if self.strchars[i] == "%" or self.strchars[i] == "&":
                error_pointers.append(i)
            i += 1
        if len(error_pointers) > 0:
            return False
        return True

    def is_pubidchar(self, char: str) -> bool:
        if len(char) != 1:
            return False
        if char in {" ", "\r", "\n"}:  # 0x20 | 0x0D | 0x0A
            return True
        if char.isalnum():  # [a-zA-Z0-9]
            return True
        if char in {"-()+,./:=?;!*#@$_%"}:
            return True
        return False

    def check_pubid_literal(self) -> bool:
        error_pointers: list[int] = []
        i = 0
        while i < len(self.strchars):
            if not self.is_pubidchar(self.strchars[i]):
                error_pointers.append(i)
            i += 1
        if len(error_pointers) > 0:
            return False
        return True

    def strip_quotes(self) -> XmlChars:
        start = 0
        end = len(self.xmlchars)
        if self.xmlchars[0] == "'" or self.xmlchars[0] == '"':
            start += 1
        if self.xmlchars[-1] == "'" or self.xmlchars[-1] == '"':
            end -= 1
        xmlchars: list[XmlChar | XmlCharRef] = self.xmlchars[start:end]
        return XmlChars(*xmlchars)
