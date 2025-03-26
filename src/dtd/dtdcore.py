from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from errcl import ErrorCollector

from .dtdentity import DtdEntity


class Dtd:
    def __init__(self, err: ErrorCollector) -> None:
        self.err = err
        self.entity = DtdEntity(self.err)
