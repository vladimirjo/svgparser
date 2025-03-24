from __future__ import annotations

from xmltokens import XmlChars


class Text:
    def __init__(self) -> None:
        self.contents: XmlChars | None = None

    def can_add_xmltoken(self, xmltoken: XmlChars) -> bool:
        if xmltoken == "<":
            return False
        if self.contents is None:
            self.contents = XmlChars()
        self.contents.append(xmltoken)
        return True
