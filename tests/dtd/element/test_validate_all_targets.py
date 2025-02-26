from tests.conftest import create_element_definition, tokenize_elements_to_validate


def test__nebulagazer_validate_ver1() -> None:
    tree = create_element_definition("( (a, (b, c)*, d) | e)")
    elements = tokenize_elements_to_validate(["a", "b", "c", "d"])
    tree.validate_elements(elements)
    assert tree.is_requirements_met() is True

def test__nebulagazer_validate_ver2() -> None:
    tree = create_element_definition("( (a, (b, c)*, d) | e)")
    elements = tokenize_elements_to_validate(["a", "b", "c"])
    tree.validate_elements(elements)
    assert tree.is_requirements_met() is False
