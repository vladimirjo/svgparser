from dtd import ChoiceDefinition, SequenceDefinition, TargetDefinition
from tests.conftest import create_def_tree

def test__nebulagazer() -> None:
    tree = create_def_tree("( (a, (b, c)*, d) | e)")
    root = tree.root
    assert isinstance(root, ChoiceDefinition)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 2
    assert available_targets[0].name == "a"
    assert available_targets[1].name == "e"
    tree.match_element("a", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 2
    assert available_targets[0].name == "b"
    assert available_targets[1].name == "d"
    tree.match_element("b", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 1
    assert available_targets[0].name == "c"
    tree.match_element("c", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 2
    assert available_targets[0].name == "b"
    assert available_targets[1].name == "d"
    tree.match_element("d", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 0

def test__tidalwhisper() -> None:
    tree = create_def_tree("( (a, b)* | c | d)")
    root = tree.root
    assert isinstance(root, ChoiceDefinition)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 3
    assert available_targets[0].name == "a"
    assert available_targets[1].name == "c"
    assert available_targets[2].name == "d"
    tree.match_element("a", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 1
    assert available_targets[0].name == "b"
    tree.match_element("b", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 3
    assert available_targets[0].name == "a"
    assert available_targets[1].name == "c"
    assert available_targets[2].name == "d"
    tree.match_element("c", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 0

def test__velvetcactus() -> None:
    tree = create_def_tree("(a | (b, c)* | d)")
    root = tree.root
    assert isinstance(root, ChoiceDefinition)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 3
    assert available_targets[0].name == "a"
    assert available_targets[1].name == "b"
    assert available_targets[2].name == "d"
    tree.match_element("a", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 0

def test__velvetcactus1() -> None:
    tree = create_def_tree("(a | (b, c)* | d)")
    root = tree.root
    assert isinstance(root, ChoiceDefinition)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 3
    assert available_targets[0].name == "a"
    assert available_targets[1].name == "b"
    assert available_targets[2].name == "d"
    tree.match_element("b", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 1
    assert available_targets[0].name == "c"
    tree.match_element("c", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 3
    assert available_targets[0].name == "b"
    assert available_targets[1].name == "a"
    assert available_targets[2].name == "d"

    # assert available_targets[1].name == "d"
    # tree.match_element("b", available_targets)
    # available_targets = tree.get_available_targets()
    # assert len(available_targets) == 1
    # assert available_targets[0].name == "c"
    # tree.match_element("c", available_targets)
    # available_targets = tree.get_available_targets()
    # assert len(available_targets) == 2
    # assert available_targets[0].name == "b"
    # assert available_targets[1].name == "d"
    # tree.match_element("d", available_targets)
    # available_targets = tree.get_available_targets()
    # assert len(available_targets) == 0

def test__zestyquokka() -> None:
    pass
