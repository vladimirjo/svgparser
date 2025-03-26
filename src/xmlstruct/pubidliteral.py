from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from dtd.dtdcore import Dtd
    from errcl import ErrorCollector
    from xmltokens import XmlProccesor

from errcl import CritErr
from xmltokens import XmlChars


class PubidLiteral:
    def __init__(
        self,
        proc: XmlProccesor,
        dtd: Dtd,
        err: ErrorCollector,
    ) -> None:
        self.proc = proc
        self.dtd = dtd
        self.err = err
        self.startquote = XmlChars()
        self.endquote = XmlChars()
        self.content = XmlChars()
        self.PUBID_CHAR_SET = set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-'()+,./:=?;!*#@$_% \n"
        )
        self.parse_startquote()
        self.parse_content()
        self.validate_chars()

    def parse_startquote(self) -> None:
        startqoute = self.proc.read(0, 1)
        if not startqoute.is_quote():
            raise ValueError("Internal library error, please repost to author.")
        self.proc.move(1)
        self.startquote = startqoute

    def parse_content(self) -> None:
        while not self.proc.is_end():
            if self.proc.read() == self.startquote:
                self.endquote = self.proc.read()
                self.proc.move()
                return
            self.content.append(self.proc.read())
            self.proc.move()

    def validate_chars(self):
        if len(self.content.xmlchars) == 0:
            return
        i = 0
        while i < len(self.content.xmlchars):
            if self.content.xmlchars[i] not in self.PUBID_CHAR_SET:
                self.err.add(self.content, CritErr.PUBID_LITERAL_CHAR_NOT_ALLOWED, i)
