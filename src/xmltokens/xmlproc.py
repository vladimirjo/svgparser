from __future__ import annotations

from typing import TYPE_CHECKING

from xmltokens import xmlchars


if TYPE_CHECKING:
    pass

from .xmlchars import XmlChars


class XmlProcessor:
    def __init__(
        self,
        xmlchars: XmlChars,
    ) -> None:
        self.xmlchars = xmlchars
        self.pointer: int = 0

    def remainder(self) -> XmlChars:
        return XmlChars(*self.xmlchars[self.pointer :])

    def match(self, text: str, offset: int = 0) -> bool:
        return self.xmlchars.match(text, self.pointer + offset)

    def match_followed_by_space(self, text: str, offset: int = 0) -> bool:
        if not self.xmlchars.match(text, self.pointer + offset):
            return False
        return self.xmlchars.is_space(self.pointer + offset + len(text))

    def get_spaces(self) -> XmlChars:
        spaces = XmlChars()
        while self.read().is_space():
            spaces.append(self.read())
            self.move()
        return spaces

    def get_pent_ref(self) -> XmlChars | None:
        if self.read() != "%":
            return None
        pent_ref_end_pos = self.find(";")
        if pent_ref_end_pos < 0:
            return None
        return self.read(0, pent_ref_end_pos + 1)

    def get_gent_ref(self) -> XmlChars | None:
        if self.read() != "&":
            return None
        ref_end_pos = self.find(";")
        if ref_end_pos < 0:
            return None
        return self.read(0, ref_end_pos + 1)

    def get_chrref(self) -> XmlChars | None:
        if self.read() != "&#":
            return None
        chrref_end_pos = self.find(";")
        if chrref_end_pos < 0:
            return None
        return self.read(0, chrref_end_pos + 1)

    def move(self, num: int = 1) -> None:
        self.pointer += num

    def is_end(self) -> bool:
        if self.pointer >= len(self.xmlchars.xmlchars):
            return True
        return False

    def read(self, offset: int = 0, length: int = 1) -> XmlChars:
        if offset < 0 or length < 0:
            return XmlChars()
        if self.pointer + offset + length > len(self.xmlchars.xmlchars):
            return XmlChars()
        start = self.pointer + offset
        end = self.pointer + offset + length
        return XmlChars(*self.xmlchars.xmlchars[start:end])

    def find(self, text: str) -> int:
        find_pos = self.xmlchars.strchars.find(text, self.pointer)
        if find_pos < 0:
            return find_pos
        return find_pos - self.pointer

    def ins_repl_text(self, length_to_replace: int, replace_text: XmlChars) -> None:
        self.xmlchars.remove(self.pointer, self.pointer + length_to_replace)
        self.xmlchars.insert(replace_text, self.pointer)
