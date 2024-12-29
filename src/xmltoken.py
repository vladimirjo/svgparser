from __future__ import annotations
from tkinter import NO

from shared import EMPTY_SPACES


class XMLToken:
    def __init__(self, content: str, pointer: int, buffer_slot: int) -> None:
        self.content = content
        self.pointer = pointer
        self.buffer_slot = buffer_slot

    def __repr__(self):
        if self.content is None:
            return "Token"
        return f"Token: {self.content}"

    def begins_with_empty_space(self) -> bool:
        if self.content[0] in EMPTY_SPACES:
            return True
        return False

    def add_value(self, content: str) -> None:
        self.content += content

    def add_token(self, token: XMLToken) -> None:
        self.content += token.content

    def has_value(self) -> bool:
        if self.content is None:
            return False
        return True

    def match(self, text: str) -> bool:
        if self.content == text:
            return True
        return False

    def begins_with(self, text: str) -> bool:
        num_chars = len(text)
        if len(self.content) < num_chars:
            return False
        if self.content[:num_chars] == text:
            return True
        return False

    def ends_with(self, text: str) -> bool:
        num_chars = len(text)
        if len(self.content) < num_chars:
            return False
        num_last_chars = -1 * num_chars
        if self.content[num_last_chars:] == text:
            return True
        return False

    def end_pointer(self) -> int:
        return self.pointer + len(self.content)
