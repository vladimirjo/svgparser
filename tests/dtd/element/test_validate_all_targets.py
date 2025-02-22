from dtd import ChoiceDefinition, SequenceDefinition
from tests.conftest import create_def_tree, tokenize_elements_to_validate
from buffer_controller import Fragment, Token


def test__nebulagazer_validate_ver1() -> None:
    tree = create_def_tree("( (a, (b, c)*, d) | e)")
    elements = tokenize_elements_to_validate(["a", "b", "c", "d"])
    tree.validate_elements(elements)
    assert tree.is_requirements_met() is True

def test__nebulagazer_validate_ver2() -> None:
    tree = create_def_tree("( (a, (b, c)*, d) | e)")
    elements = tokenize_elements_to_validate(["a", "b", "c"])
    tree.validate_elements(elements)
    assert tree.is_requirements_met() is False
