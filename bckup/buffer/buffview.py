from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .buffunit import BufferUnit


class BufferView:
    def __init__(self, buffer_unit: BufferUnit, buffer_type: str = "xml") -> None:
        self.buffer_unit = buffer_unit
        self.buffer_type = buffer_type
        self.in_buffer_pointer_start = 0
        self.in_buffer_pointer_end = self.in_buffer_pointer_start + len(self.buffer_unit.buffer)
        self.in_buffer_pointer_current = 0
