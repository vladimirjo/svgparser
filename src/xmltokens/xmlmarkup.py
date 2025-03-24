from __future__ import annotations

from typing import TYPE_CHECKING
from typing import NamedTuple


if TYPE_CHECKING:
    from xmltokens.xmlchars import XmlChars


class XmlMarkup(NamedTuple):
    entity_id: int
    xmlchars: XmlChars
