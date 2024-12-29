EMPTY_SPACES = {" ", "\n", "\r", "\t"}
QUOTES = {'"', "'"}


class SvgReader:
    def __init__(self, buffer: str) -> None:
        self.buffer: str = buffer
        self.pointer: int = 0

    def current(self) -> str:
        return self.buffer[self.pointer]

    def next(self) -> None:
        self.pointer += 1

    def skip_forward(self) -> None:
        while self.current() in EMPTY_SPACES:
            self.pointer += 1

    def skip_backward(self) -> None:
        while self.current() in EMPTY_SPACES:
            self.pointer -= 1
