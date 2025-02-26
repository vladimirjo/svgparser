from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .token import Token


class TokenAccumulator:
    def __init__(self) -> None:
        self.tokens: list[Token] = []

    def add_token(self, token: Token) -> None:
        self.tokens.append(token)

    def get_token(self) -> Token | None:
        if len(self.tokens) == 0:
            return None
        accumulator_token = self.tokens[0]
        i = 1
        while i < len(self.tokens):
            accumulator_token.add_token(self.tokens[i])
            i += 1
        return accumulator_token
