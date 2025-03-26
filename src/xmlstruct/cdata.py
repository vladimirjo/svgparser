from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from errcl import ErrorCollector
    from xmltokens.xmlproc import XmlProcessor
    from xmlvalidator import XmlValidator

    from .doctype import Doctype
    from .includeignore import IncludeIgnore
    from .tag import Tag

from xmltokens.xmlchars import XmlChars


class CData:
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
        self.content: XmlChars | None = None
