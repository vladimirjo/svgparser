from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from dtd.dtdcore import Dtd
    from errcl import ErrorCollector
    from xmltokens import XmlProccesor

from xmltokens import XmlChars
from xmltokens.xmlcharref import XmlCharRef


class SystemLiteral:
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
        self.parse_startquote()
        self.parse_content()

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
