from __future__ import annotations

from re import A
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from errcl import ErrorCollector
    from xmltokens.xmlproc import XmlProcessor
    from xmlvalidator import XmlValidator

    from .doctype import Doctype
    from .includeignore import IncludeIgnore
    from .tag import Tag

from errcl import CritErr
from xmltokens.xmlchars import XmlChars


class EndTag:
    def __init__(
        self,
        proc: XmlProcessor,
        parent: Tag | Doctype | IncludeIgnore | XmlValidator,
        err: ErrorCollector,
    ) -> None:
        self.proc = proc
        self.parent = parent
        self.err = err
        self.tokens: list[XmlChars] = []
        self.startseq = XmlChars()
        self.endseq = XmlChars()
        self.name = XmlChars()
        self.parse_startseq()
        self.parse_name()
        self.parse_space()
        self.parse_trailing()
        self.parse_end()
        self.close_matching_start_tag()
        self.verify_endseq()
        self.verify_start_and_end_entity_origin()

    def verify_endseq(self) -> None:
        if self.endseq == "":
            self.err.add(self.startseq, CritErr.NODE_MISSING_END)

    def parse_startseq(self) -> None:
        startseq = self.proc.read(0, 2)
        self.proc.move(2)
        self.tokens.append(startseq)
        self.startseq = startseq

    def parse_name(self) -> None:
        while not self.proc.is_end():
            if self.is_parse_end():
                self.parse_end()
                return
            if not self.proc.read().is_space():
                break
            self.name.append(self.proc.read())
            self.proc.move()
        while not self.proc.is_end():
            if self.is_parse_end():
                self.parse_end()
                return
            if self.proc.read().is_space():
                return
            self.name.append(self.proc.read())
            self.proc.move()

    def parse_space(self) -> None:
        while not self.proc.is_end():
            if self.is_parse_end():
                return
            if self.proc.read().is_space():
                self.proc.get_spaces()
                break

    def parse_trailing(self) -> None:
        while not self.proc.is_end():
            if self.is_parse_end():
                return
            self.proc.move()
        self.err.add(self.proc.read(), CritErr.END_TAG_INVALID_TRAILING)

    def is_parse_end(self) -> bool:
        if self.proc.read() == "<" or self.proc.read() == ">":
            return True
        if self.proc.read(0, 2) == "/>":
            return True
        return False

    def parse_end(self) -> None:
        if self.proc.is_end():
            return
        if self.proc.read() == "<":
            return
        if self.proc.read() == ">":
            self.endseq = self.proc.read()
            self.tokens.append(self.proc.read())
            self.proc.move()
            return

    def verify_start_and_end_entity_origin(self) -> None:
        if self.startseq.get_entity_id() != self.endseq.get_entity_id():
            self.err.add(self.endseq, CritErr.NODE_START_END)

    def close_matching_start_tag(self) -> None:
        from xmlstruct.doctype import Doctype
        from xmlstruct.includeignore import IncludeIgnore
        from xmlstruct.tag import Tag
        from xmlvalidator import XmlValidator

        active_node = self.parent
        missing_close_tags: list[Tag] = []
        while not isinstance(active_node, XmlValidator):
            if isinstance(active_node, (Doctype, IncludeIgnore)):
                self.err.add(self.startseq, CritErr.END_TAG_NESTED_IN_DTD)
                active_node = active_node.parent
                continue
            if isinstance(active_node, Tag):
                if active_node.close_tag(self.name):
                    if len(missing_close_tags) > 0:
                        for tag in missing_close_tags:
                            self.err.add(tag.startseq, CritErr.TAG_NOT_CLOSED)
                    break
                else:
                    missing_close_tags.append(active_node)
                    active_node = active_node.parent
                continue
