from __future__ import annotations

from typing import TYPE_CHECKING

from xmltokens.xmlcharref import XmlCharRef


if TYPE_CHECKING:
    from dtd.dtdcore import Dtd
    from errcl import ErrorCollector
    from xmltokens import XmlProccesor

from xmltokens import XmlChars


class EntityLiteral:
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
        startqoute = self.proc.read()
        if startqoute.is_quote():
            raise ValueError("Internal library error, please repost to author.")
        self.proc.move()
        self.startquote = startqoute

    def parse_content(self) -> None:
        while not self.proc.is_end():
            if (
                self.proc.match(self.startquote.strchars)
                and self.proc.read().get_entity_id() == self.startquote.get_entity_id()
            ):
                self.endquote = self.proc.read()
                self.proc.move()
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
            if self.proc.read() == "%":
                pent_ref = self.proc.get_pent_ref()
                if pent_ref is None:
                    # error gent_ref not ended properly
                    self.content.append(self.proc.read())
                    self.proc.move()
                    continue
                deref_pent = self.dtd.entity.deref_pent(pent_ref)
                if deref_pent is None:
                    # error chrref not recognized
                    self.content.append(self.proc.read())
                    self.proc.move()
                    continue
                self.content.append(deref_pent)
                self.proc.move(len(pent_ref.xmlchars))
                continue
            if self.proc.read().is_space() and self.proc.read() != " ":
                normalized_space = XmlCharRef(" ", self.proc.read().xmlchars[0])
                self.content.append(normalized_space)
                continue
            self.content.append(self.proc.read())
            self.proc.move()
