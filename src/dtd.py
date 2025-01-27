from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from buffer_controller import Token
    from xmlvalidator import ErrorCollector


class Dtd:
    def __init__(self, element_tokens: list[Token], error_collector: ErrorCollector | None = None) -> None:
        self.tokens = element_tokens
        self.error_collector = error_collector
