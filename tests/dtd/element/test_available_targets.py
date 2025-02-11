from dtd import ChoiceDefinition, SequenceDefinition, TargetDefinition
from tests.conftest import create_def_tree


def test__quarkmurmur() -> None:
    tree = create_def_tree("( (a, (b, c)*, d) | e)")
    root = tree.root
    assert isinstance(root, ChoiceDefinition)
    branch0=root.branches[0]
    branch1=root.branches[1]
    assert isinstance(branch0, SequenceDefinition)
    assert isinstance(branch1, TargetDefinition)
    branch0_0 = branch0.branches[0]
    branch0_1 = branch0.branches[1]
    branch0_2 = branch0.branches[2]
    assert isinstance(branch0_0, TargetDefinition)
    assert isinstance(branch0_1, SequenceDefinition)
    assert isinstance(branch0_2, TargetDefinition)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 2
    assert available_targets[0].name == "a"
    assert available_targets[1].name == "e"
    branch0_1.count += 1
    branch0.chosen_branch = branch0_1
    root.chosen_branch = branch0
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 2
    assert available_targets[0].name == "b"
    assert available_targets[1].name == "d"

def test__flimsytoast() -> None:
    tree = create_def_tree("((a | (b, (c | (d, e*)))), f)")
    root = tree.root
    assert isinstance(root, SequenceDefinition)
    assert f"{root!r}" == "( ( a | ( b , ( c | ( d , e * ) ) ) ) , f )"
    branch0=root.branches[0]
    assert f"{branch0!r}" == "( a | ( b , ( c | ( d , e * ) ) ) )"
    branch1=root.branches[1]
    assert f"{branch1!r}" == "f"
    assert isinstance(branch0, ChoiceDefinition)
    assert isinstance(branch1, TargetDefinition)
    branch0_0 = branch0.branches[0]
    assert f"{branch0_0!r}" == "a"
    branch0_1 = branch0.branches[1]
    assert f"{branch0_1!r}" == "( b , ( c | ( d , e * ) ) )"
    assert isinstance(branch0_0, TargetDefinition)
    assert isinstance(branch0_1, SequenceDefinition)
    branch0_1_0 = branch0_1.branches[0]
    assert f"{branch0_1_0!r}" == "b"
    branch0_1_1 = branch0_1.branches[1]
    assert f"{branch0_1_1!r}" == "( c | ( d , e * ) )"
    assert isinstance(branch0_1_0, TargetDefinition)
    assert isinstance(branch0_1_1, ChoiceDefinition)
    branch0_1_1_0 = branch0_1_1.branches[0]
    assert f"{branch0_1_1_0!r}" == "c"
    branch0_1_1_1 = branch0_1_1.branches[1]
    assert f"{branch0_1_1_1!r}" == "( d , e * )"
    assert isinstance(branch0_1_1_0, TargetDefinition)
    assert isinstance(branch0_1_1_1, SequenceDefinition)
    branch0_1_1_1_0 = branch0_1_1_1.branches[0]
    assert f"{branch0_1_1_1_0!r}" == "d"
    branch0_1_1_1_1 = branch0_1_1_1.branches[1]
    assert f"{branch0_1_1_1_1!r}" == "e *"
    assert isinstance(branch0_1_1_1_0, TargetDefinition)
    assert isinstance(branch0_1_1_1_1, TargetDefinition)

    root.chosen_branch = branch0
    branch0.chosen_branch = branch0_1
    branch0_1_0.count += 1
    branch0_1.chosen_branch = branch0_1_1
    branch0_1_1.chosen_branch = branch0_1_1_1
    branch0_1_1_1_0.count += 1
    branch0_1_1_1.chosen_branch = branch0_1_1_1_1
    branch0_1_1_1_0.count +=1
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 2
    assert available_targets[0].name == "e"
    assert available_targets[1].name == "f"
