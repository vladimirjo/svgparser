from __future__ import annotations

from enum import Enum
from enum import auto
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from dtd.dtdcore import Dtd
    from errcl import ErrorCollector
    from xmltokens.xmlproc import XmlProcessor
    from xmlvalidator import XmlValidator

    from .attlist import AttList
    from .cdata import CData
    from .comment import Comment
    from .doctype import Doctype
    from .element import Element
    from .entity import Entity
    from .includeignore import IncludeIgnore
    from .instructions import Instructions
    from .notation import Notation
    from .text import Text
    from .xmldecl import XmlDecl

from errcl import CritErr
from xmltokens.xmlchars import XmlChars

from .attliteral import AttLiteral


class AttrSwitch(Enum):
    NAME = auto()
    EQUAL = auto()
    VALUE = auto()


class Tag:
    def __init__(
        self,
        proc: XmlProcessor,
        parent: Tag | Doctype | IncludeIgnore | XmlValidator,
        dtd: Dtd,
        err: ErrorCollector,
    ) -> None:
        self.proc = proc
        self.parent = parent
        self.dtd = dtd
        self.err = err
        self.tokens: list[XmlChars] = []
        self.startseq = XmlChars()
        self.endseq = XmlChars()
        self.closed: bool = False
        self.is_invalid: bool = False
        self.name: XmlChars = XmlChars()
        self.attributes: dict[XmlChars, XmlChars] = {}
        self.children: list[
            AttList
            | CData
            | Comment
            | Element
            | Entity
            | IncludeIgnore
            | Instructions
            | Notation
            | Tag
            | Text
            | XmlDecl
        ] = []
        self.parse_startseq()
        self.parse_name()
        self.parse_attributes()
        self.parse_invalid()
        self.parse_end()
        self.verify_endseq()
        self.verify_location()
        self.verify_start_and_end_entity_origin()

    def get_active_node(self) -> Tag | Doctype | IncludeIgnore:
        if len(self.children) == 0:
            return self
        if isinstance(self.children[-1], (Tag, Doctype, IncludeIgnore)) and not self.children[-1].closed:
            return self.children[-1].get_active_node()
        return self

    def parse_startseq(self) -> None:
        startseq = self.proc.read(0, len("<"))
        self.proc.move(1)
        self.tokens.append(startseq)
        self.startseq = startseq

    def verify_start_and_end_entity_origin(self) -> None:
        if self.startseq.get_entity_id() != self.endseq.get_entity_id():
            self.err.add(self.endseq, CritErr.NODE_START_END)

    def is_parse_end(self) -> bool:
        if self.proc.match("<") or self.proc.match(">") or self.proc.match("/>"):
            return True
        return False

    def parse_end(self) -> None:
        if self.proc.is_end():
            return
        if self.proc.read(0, 1) == "<":
            return
        if self.proc.read(0, 2) == "/>":
            self.closed = True
            self.endseq = self.proc.read(0, 2)
            self.tokens.append(self.proc.read(0, 2))
            self.proc.move(2)
            return
        if self.proc.read(0, 1) == ">":
            self.endseq = self.proc.read()
            self.tokens.append(self.proc.read())
            self.proc.move()
            return

    def parse_name(self) -> None:
        if self.is_invalid:
            return
        while not self.proc.is_end():
            if self.is_parse_end():
                return
            if not self.proc.read().is_space():
                break
            self.name.append(self.proc.read())
            self.proc.move()
        while not self.proc.is_end():
            if self.is_parse_end():
                return
            if self.proc.read().is_quote() or self.proc.read() == "=":
                self.err.add(self.startseq, CritErr.TAG_NAME_INVALID)
                self.is_invalid = True
                return
            if self.proc.read().is_space():
                return
            self.name.append(self.proc.read())
            self.proc.move()

    def parse_attr_name(self) -> XmlChars:
        attr_name = XmlChars()
        while not self.proc.is_end():
            if self.is_parse_end():
                break
            if self.proc.read() == "=":
                break
            if self.proc.read().is_quote():
                break
            if self.proc.read().is_space():
                break
            attr_name.append(self.proc.read())
            self.proc.move()
        return attr_name

    def parse_attributes(self) -> None:
        if self.is_invalid:
            return
        attr_name = XmlChars()
        attr_switch: AttrSwitch = AttrSwitch.NAME
        while not self.proc.is_end():
            if self.is_parse_end():
                return
            if self.proc.read().is_space():
                self.tokens.append(self.proc.get_spaces())
                continue
            if attr_switch == AttrSwitch.NAME:
                attr_name = self.parse_attr_name()
                if attr_name == "":
                    self.err.add(self.proc.read(), CritErr.ATTR_EXPECTED_NAME)
                    return
                attr_switch = AttrSwitch.EQUAL
                self.tokens.append(attr_name)
                continue
            if attr_switch == AttrSwitch.EQUAL:
                if self.proc.read() != "=":
                    self.err.add(self.proc.read(), CritErr.ATTR_EXPECTED_EQUAL)
                    return
                attr_switch = AttrSwitch.VALUE
                self.tokens.append(self.proc.read())
                self.proc.move()
                continue
            if attr_switch == AttrSwitch.VALUE:
                if not self.proc.read().is_quote():
                    self.err.add(self.proc.read(), CritErr.ATTR_EXPECTED_VALUE)
                    return
                attr_value = AttLiteral(self.proc, self.dtd, self.err).content
                if attr_value == "":
                    self.err.add(self.proc.read(), CritErr.ATTR_EXPECTED_VALUE)
                    return
                self.attributes[attr_name] = attr_value
                self.tokens.append(attr_value)
                attr_switch = AttrSwitch.NAME
                attr_name = XmlChars()
                if not self.proc.read().is_space():
                    if self.is_parse_end():
                        continue
                    self.err.add(self.proc.read(), CritErr.ATTR_EXPECTED_SPACE)
                continue

    def parse_invalid(self) -> None:
        while not self.proc.is_end():
            if self.is_parse_end():
                return
            self.proc.move()

    def verify_location(self) -> None:
        from xmlstruct.doctype import Doctype
        from xmlstruct.includeignore import IncludeIgnore
        from xmlvalidator import XmlValidator

        if isinstance(self.parent, XmlValidator):
            for node in self.parent.children:
                if isinstance(node, Tag):
                    self.err.add(self.startseq, CritErr.TAG_ONLY_ONE_ROOT)
                    return
        if isinstance(self.parent, (Doctype, IncludeIgnore)):
            self.err.add(self.startseq, CritErr.TAG_LOCATION_INVALID)
            return

    def verify_endseq(self) -> None:
        if self.endseq == "":
            self.err.add(self.startseq, CritErr.NODE_MISSING_END)

    def close_tag(self, end_tag_name: XmlChars) -> bool:
        if self.name == "":
            return False
        if self.closed:
            return False
        if self.name.strchars.strip() == end_tag_name.strchars.strip():
            self.closed = True
            return True
        return False
