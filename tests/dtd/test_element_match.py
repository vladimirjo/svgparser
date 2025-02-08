from dtd import ChoiceDefinition, ElementDefinitionsDefined, SequenceDefinition, TreeDefinitionValidator
import pytest
from xmlvalidator import ValidatorDocument, ValidatorTag

@pytest.fixture
def complex_xml() -> str:
    return """<!DOCTYPE element [
    <!ELEMENT element ((e1 | (e2 , (e3 | (e4 , e5*)))), e6)>
]>
<element>
    <e2></e2>
    <e4></e4>
    <e5></e5>
    <e5></e5>
    <e6></e6>
</element>"""

def generate_doc(xml: str) -> ValidatorDocument:
    doc= ValidatorDocument()
    doc.read_buffer(xml)
    doc.build_validation_tree()
    return doc

def test__element_match_complex(complex_xml: str) -> None:
    doc=generate_doc(complex_xml)
    assert isinstance(doc.children[1], ValidatorTag)
    assert doc.dtd is not None
    assert doc.children[1].name == "element"
    element = doc.children[1]
    assert element.name is not None
    element_definition = doc.dtd.element_definitions[element.name]
    if not isinstance(element_definition, ElementDefinitionsDefined):
        return
    edd_tree = TreeDefinitionValidator(element_definition)
    assert repr(edd_tree) == "( ( e1 | ( e2 , ( e3 | ( e4 , e5 * ) ) ) ) , e6 )"
    targets=edd_tree.get_available_targets()
    edd_tree.match_element("e2", targets)
    targets=edd_tree.get_available_targets()
    edd_tree.match_element("e4", targets)
    targets=edd_tree.get_available_targets()
    edd_tree.match_element("e5",targets)
    edd_tree.match_element("e5",targets)
    edd_tree.match_element("e5",targets)
    targets=edd_tree.get_available_targets()




        # assert repr(edd_tree.branches[0]) == "( e1 | ( e2 , ( e3 | ( e4 , e5 * ) ) ) )"
        # assert repr(edd_tree.branches[1]) == "e6"
        # assert repr(edd_tree.branches[0].branches[0]) == "e1"
        # assert repr(edd_tree.branches[0].branches[1]) == "( e2 , ( e3 | ( e4 , e5 * ) ) )"
        # # e1 match
        # edd_tree.branches[0].match_count = 1
        # edd_tree.branches[0].branches[0].match_count = 1
        # targets = edd_tree.get_all_targets()
        # assert len(targets) == 1
        # assert targets[0].target is not None and targets[0].target.chars == "e6"
        # # RESET MATCHES
        # edd_tree.branches[0].match_count = 0
        # edd_tree.branches[0].branches[0].match_count = 0
        # # e2 match
        # edd_tree.branches[0].branches[1].match_count = 1
        # targets = edd_tree.get_all_targets()
        # assert len(targets) == 2
        # assert targets[0].target is not None and targets[0].target.chars == "e3"
        # assert targets[1].target is not None and targets[0].target.chars == "e4"


def test__tree(complex_xml: str) -> None:
    doc=generate_doc(complex_xml)
    assert isinstance(doc.children[1], ValidatorTag)
    assert doc.dtd is not None
    assert doc.children[1].name == "element"
    element = doc.children[1]
    assert element.name is not None
    element_definition = doc.dtd.element_definitions[element.name]
    if isinstance(element_definition, ElementDefinitionsDefined):
        edd_tree = TreeDefinitionValidator(element_definition)
        assert repr(edd_tree.root) == "( ( e1 | ( e2 , ( e3 | ( e4 , e5 * ) ) ) ) , e6 )"
        available_targets = edd_tree.get_available_targets()
        print()
        # # e1 match
        # edd_tree.branches[0].match_count = 1
        # edd_tree.branches[0].branches[0].match_count = 1
        # targets = edd_tree.get_all_targets()
        # assert len(targets) == 1
        # assert targets[0].target is not None and targets[0].target.chars == "e6"
        # # RESET MATCHES
        # edd_tree.branches[0].match_count = 0
        # edd_tree.branches[0].branches[0].match_count = 0
        # # e2 match
        # edd_tree.branches[0].branches[1].match_count = 1
        # targets = edd_tree.get_all_targets()
        # assert len(targets) == 2
        # assert targets[0].target is not None and targets[0].target.chars == "e3"
        # assert targets[1].target is not None and targets[0].target.chars == "e4"
