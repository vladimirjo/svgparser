from dtd import ElementDefinitionsMixed, TagElement, PCDATAElement
from tests.conftest import MixedContentTest,tokenize_definition
from buffer_controller import Fragment, Token
from errorcollector import ErrorCollector


def test__mixed_content_only_pcdata() -> None:
    definition = tokenize_definition("(#PCDATA)")
    mixed_definition = ElementDefinitionsMixed(definition, ErrorCollector())
    elements = MixedContentTest()
    elements.add_pcdata("test")
    mixed_definition.validate_elements(elements.mixed_contents)
    assert len(mixed_definition.err.tokens) == 0



def test__mixed_content_with_valid_elements() -> None:
    definitions = tokenize_definition("(#PCDATA | a)*")
    mixed_definition = ElementDefinitionsMixed(definitions, ErrorCollector())
    elements = MixedContentTest()
    elements.add_pcdata("test")
    elements.add_element("a")
    mixed_definition.validate_elements(elements.mixed_contents)
    assert len(mixed_definition.err.tokens) == 0

def test__mixed_content_with_invalid_elements() -> None:
    definitions = tokenize_definition("(#PCDATA | a)*")
    mixed_definition = ElementDefinitionsMixed(definitions, ErrorCollector())
    elements = MixedContentTest()
    elements.add_pcdata("test")
    elements.add_element("b")
    mixed_definition.validate_elements(elements.mixed_contents)
    assert len(mixed_definition.err.tokens) != 0

# def test__nebulagazer_validate_ver2() -> None:
#     tree = create_def_tree("( (a, (b, c)*, d) | e)")
#     elements = tokenize_elements_to_validate(["a", "b", "c"])
#     tree.validate_elements(elements)
#     assert tree.is_requirements_met() is False
