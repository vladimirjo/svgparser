from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    pass

from dtd.dtdcore import Dtd
from textbuffer import TextBuffer
from xmlstruct.entity import Entity
from xmlstruct.tag import Tag
from xmlstruct.text import Text
from xmltokens import XmlChar
from xmltokens import XmlCharRef
from xmltokens import XmlChars
from xmltokens import XmlMarkup
from xmltokens import XmlProccesor


class XmlValidator:
    def __init__(self) -> None:
        self.buffers: list[TextBuffer] = []
        self.root_entity: XmlChars | None = None
        self.ext_subset: XmlChars | None = None
        self.dtd = Dtd()
        self.nodetree: list[Entity] | None = None

    def build(self) -> None:
        if self.root_entity is None:
            raise ValueError("Root entity not found.")
        main = XmlProccesor(self.root_entity)
        while not main.is_end():
            if main.match("<!ENTITY"):
                Entity()
            pass

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


class BufferStack:
    def __init__(self) -> None:
        pass
