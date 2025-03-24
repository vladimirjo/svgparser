from __future__ import annotations


from xmltokens.xmlchars import XmlChars


class Tag:
    def __init__(self) -> None:
        self.contents: XmlChars | None = None

    def can_add_xmltoken(self, xmlchars: XmlChars) -> bool:
        if xmlchars == "<":
            return False
        if self.contents is None:
            self.contents = XmlChars()
        self.contents.append(xmlchars)
        return True
