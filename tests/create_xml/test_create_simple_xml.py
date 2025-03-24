from xmlvalidator import XmlValidator

def test__simple_xml() -> None:
    xmlvalidator = XmlValidator()
    # x41 = A
    xmlvalidator.add_buffer("<tag>&#x41;</tag>")
    print()
