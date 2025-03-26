from __future__ import annotations

from typing import TYPE_CHECKING

from xmltokens.xmlcharref import XmlCharRef


if TYPE_CHECKING:
    from dtd.dtdcore import Dtd
    from errcl import ErrorCollector
    from xmltokens import XmlProccesor

from xmltokens import XmlChars


class AttLiteral:
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
        self.parse()

    def normalize_white_spaces(self, deref_gent: XmlChars):
        norm_deref_gent = XmlChars()
        for char in deref_gent.xmlchars:
            if char.strchars in {"\r", "\n", "\t"}:
                norm_deref_gent.append(XmlCharRef(" ", char))
            else:
                norm_deref_gent.append(char)
        return norm_deref_gent

    def parse_startquote(self) -> XmlChars:
        startqoute = self.proc.read(0, 1)
        if startqoute is None or not startqoute.is_quote():
            raise ValueError()
        self.proc.move(1)
        return startqoute

    def parse(self) -> None:
        while not self.proc.is_end():
            if self.proc.match("<"):
                return
            if (
                self.proc.match(self.startquote.strchars)
                and self.proc.read(0, 1).xmlchars[0].entity_id == self.startquote.xmlchars[0].entity_id
            ):
                self.endquote = self.proc.read(0, 1)
                self.proc.move(1)
                return
            if self.proc.read(0, 2) == "&#":
                chrref = self.proc.get_chrref()
                if chrref is None:
                    # error chrref not ended properly
                    self.content.append(self.proc.read(0, 1))
                    self.proc.move(1)
                    continue
                chrref_value = self.dtd.entity.get_chrref_value(chrref)
                if chrref_value is None:
                    # error chrref not recognized
                    self.content.append(self.proc.read(0, 1))
                    self.proc.move(1)
                    continue
                self.content.append(chrref_value)
                self.proc.move(len(chrref.xmlchars))
                continue
            if self.proc.read(0, 1) == "&":
                gent_ref = self.proc.get_gent_ref()
                if gent_ref is None:
                    # error gent_ref not ended properly
                    self.content.append(self.proc.read(0, 1))
                    self.proc.move(1)
                    continue
                deref_gent = self.dtd.entity.deref_gent(gent_ref)
                if deref_gent is None:
                    # error chrref not recognized
                    self.content.append(self.proc.read(0, 1))
                    self.proc.move(1)
                    continue
                norm_deref_gent = self.normalize_white_spaces(deref_gent)
                self.content.append(norm_deref_gent)
                self.proc.move(len(gent_ref.xmlchars))
                continue
            if self.proc.read(0, 1).is_space() and self.proc.read(0, 1) != " ":
                normalized_space = XmlCharRef(" ", self.proc.read(0, 1).xmlchars[0])
                self.content.append(normalized_space)
                continue
            self.content.append(self.proc.read())
            self.proc.move()
