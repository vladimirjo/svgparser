from dataclasses import dataclass


@dataclass
class BufferUnit:
    buffer: str
    filename: str
    buffer_slot: int
