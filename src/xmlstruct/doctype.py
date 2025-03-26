from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from errcl import ErrorCollector
    from xmltokens.xmlproc import XmlProcessor
    from xmlvalidator import XmlValidator

    from .attlist import AttList
    from .cdata import CData
    from .comment import Comment
    from .element import Element
    from .entity import Entity
    from .includeignore import IncludeIgnore
    from .instructions import Instructions
    from .notation import Notation
    from .tag import Tag
    from .text import Text
    from .xmldecl import XmlDecl

from xmltokens.xmlchars import XmlChars


class Doctype:
    def __init__(
        self,
        proc: XmlProcessor,
        startseq: XmlChars,
        parent: Tag | Doctype | IncludeIgnore | XmlValidator,
        err: ErrorCollector,
    ) -> None:
        self.proc = proc
        self.startseq = startseq
        self.parent = parent
        self.err = err
        self.endseq: XmlChars | None = None
        self.tokens: list[XmlChars] = []
        self.root_name: XmlChars | None = None
        self.extern_system: XmlChars | None = None
        self.extern_public: XmlChars | None = None
        self.intern_declarations_closed = True
        self.closed = False
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

    def get_active_node(self) -> Tag | Doctype | IncludeIgnore:
        if len(self.children) == 0:
            return self
        if isinstance(self.children[-1], (Tag, Doctype, IncludeIgnore)) and not self.children[-1].closed:
            return self.children[-1].get_active_node()
        return self
