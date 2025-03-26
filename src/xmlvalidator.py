from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    pass

from dtd.dtdcore import Dtd
from errcl import ErrorCollector
from textbuffer import TextBuffer
from xmlstruct.attlist import AttList
from xmlstruct.cdata import CData
from xmlstruct.comment import Comment
from xmlstruct.doctype import Doctype
from xmlstruct.element import Element
from xmlstruct.endtag import EndTag
from xmlstruct.entity import Entity
from xmlstruct.includeignore import IncludeIgnore
from xmlstruct.instructions import Instructions
from xmlstruct.notation import Notation
from xmlstruct.tag import Tag
from xmlstruct.text import Text
from xmlstruct.xmldecl import XmlDecl
from xmltokens import XmlChar
from xmltokens import XmlCharRef
from xmltokens import XmlChars
from xmltokens import XmlProccesor


class XmlValidator:
    def __init__(self) -> None:
        self.err = ErrorCollector()
        self.buffers: list[TextBuffer] = []
        self.root_entity: XmlChars | None = None
        self.ext_subset: XmlChars | None = None
        self.dtd = Dtd(self.err)
        self.children: list[Entity | Tag] = []

    def get_active_node(self) -> Tag | Doctype | IncludeIgnore | XmlValidator:
        if len(self.children) == 0:
            return self
        if isinstance(self.children[-1], (Tag, Doctype, IncludeIgnore)) and not self.children[-1].closed:
            return self.children[-1].get_active_node()
        return self

    def build(self) -> None:
        if self.root_entity is None:
            raise ValueError("Root entity not found.")
        main = XmlProccesor(self.root_entity)
        while not main.is_end():
            parent = self.get_active_node()
            if main.match_followed_by_space("<!ENTITY"):
                node = Entity(main, parent, self.dtd, self.err)
                self.children.append(node)
                continue
            if main.match("</"):
                node = EndTag(main, parent, self.err)
                continue
            if main.match("<"):
                node = Tag(main, parent, self.dtd, self.err)
                parent.children.append(node)
                continue

    def set_root_entity(self, buffer: TextBuffer) -> None:
        xmlchars_arr: list[XmlChar] = []
        for char_pos, char in enumerate(buffer.valid_chars):
            xmlchars_arr.append(XmlChar(char, buffer.bufferslot, char_pos, 1))
        self.root_entity = XmlChars(*xmlchars_arr)

    def set_extsubset(self, buffer: TextBuffer) -> None:
        xmlchars_arr: list[XmlChar] = []
        for char_pos, char in enumerate(buffer.valid_chars):
            xmlchars_arr.append(XmlChar(char, buffer.bufferslot, char_pos, 2))
        self.ext_subset = XmlChars(*xmlchars_arr)

    def add_buffer(self, buffer: str) -> None:
        buffer_index = len(self.buffers)
        root_entity_buffer = TextBuffer(buffer, buffer_index)
        self.buffers.append(root_entity_buffer)
        self.set_root_entity(root_entity_buffer)
