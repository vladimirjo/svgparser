class Fragment:
    def __init__(self, chars: str, buffer_pointer: int, buffer_slot: int) -> None:
        self.chars = chars
        self.buffer_pointer = buffer_pointer
        self.buffer_slot = buffer_slot

    def end_pointer(self) -> int:
        return self.buffer_pointer + len(self.chars) - 1
