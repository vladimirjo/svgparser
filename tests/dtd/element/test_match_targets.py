from re import A
from dtd import ChoiceDefinition, SequenceDefinition, TargetDefinition
from tests.conftest import create_def_tree

# def random_names() -> None:
    # hollowcrescent
    # snappyglyph
    # pepperhorizon
    # sapphirequirk
    # bouncywaffle
    # timberecho
    # fizzycomet
    # noodlemirage
    # velvetorbit
    # cosmictundra
    # shadowflicker
    # rustyparadox
    # zigzagpebble
    # crimsonnimbus
    # jellyecho
    # wobbletornado
    # nebulacactus
    # glimmerfable
    # snappyvortex
    # frothymonsoon
    # quirkytadpole
    # hollowquasar
    # pass

def test__nebulagazer() -> None:
    # Sequential group with repetition and choice
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
    # Repeating sequence or single elements
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
    assert len(available_targets) == 1
    assert available_targets[0].name == "a"
    tree.match_element("a", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 1
    assert available_targets[0].name == "b"
    tree.match_element("b", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 1
    assert available_targets[0].name == "a"

def test__velvetcactus() -> None:
    # Choice between single element, repeating sequence, or another element
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

def test__mysticraven() -> None:
    # Choice between a single element, a repeating sequence, or another element
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
    assert len(available_targets) == 1
    assert available_targets[0].name == "b"

def test__lunarpebble() -> None:
    # Zero-or-more repetitions of a choice between single elements and sequences
    tree = create_def_tree("(a | (b, c)* | d)*")
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

def test__hollowcrescent_ver1() -> None:
    # Sequence containing a choice followed by a required element
    tree = create_def_tree("((a | (b, c)* | d), e)")
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 3
    assert available_targets[0].name == "a"
    assert available_targets[1].name == "b"
    assert available_targets[2].name == "d"
    tree.match_element("a", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 1
    assert available_targets[0].name == "e"

def test__hollowcrescent_ver2() -> None:
    # Sequence containing a choice followed by a required element
    tree = create_def_tree("((a | (b, c)* | d), e)")
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
    assert len(available_targets) == 2
    assert available_targets[0].name == "b"
    assert available_targets[1].name == "e"

def test__quarkmurmur() -> None:
    # Sequential group with repetition and choice
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
    tree.match_element("b",available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 1
    assert available_targets[0].name == "c"
    tree.match_element("c",available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 2
    assert available_targets[0].name == "b"
    assert available_targets[1].name == "d"
    tree.match_element("d",available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 0

def test__flimsytoast() -> None:
    # Nested choice with repetition and grouping
    tree = create_def_tree("((a | (b, (c | (d, e*)))), f)")
    root = tree.root
    assert isinstance(root, SequenceDefinition)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 2
    assert available_targets[0].name == "a"
    assert available_targets[1].name == "b"
    tree.match_element("b", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 2
    assert available_targets[0].name == "c"
    assert available_targets[1].name == "d"
    tree.match_element("d", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 2
    assert available_targets[0].name == "e"
    assert available_targets[1].name == "f"

def test_echopine()-> None:
    # Alternating required and optional elements
    tree = create_def_tree("(a, (b | c)?, d, e*)")
    root = tree.root
    assert isinstance(root, SequenceDefinition)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 1
    assert available_targets[0].name == "a"
    tree.match_element("a", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 2
    assert available_targets[0].name == "b"
    assert available_targets[1].name == "c"
    tree.match_element("b", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 3
    assert available_targets[0].name == "b"
    assert available_targets[1].name == "c"
    assert available_targets[2].name == "d"
    tree.match_element("d", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 1
    assert available_targets[0].name == "e"
    tree.match_element("e", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 1
    assert available_targets[0].name == "e"

def test_whiskermosaic_ver1()-> None:
    # Nested repetition with optional elements
    tree = create_def_tree("((a, b*) | (c, d+))")
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 2
    assert available_targets[0].name == "a"
    assert available_targets[1].name == "c"
    tree.match_element("a", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 1
    assert available_targets[0].name == "b"
    tree.match_element("b", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 1
    assert available_targets[0].name == "b"

def test_whiskermosaic_ver2()-> None:
    # Nested repetition with optional elements
    tree = create_def_tree("((a, b*) | (c, d+))")
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 2
    assert available_targets[0].name == "a"
    assert available_targets[1].name == "c"
    tree.match_element("c", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 1
    assert available_targets[0].name == "d"
    tree.match_element("d", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 0

def test_sizzlefable()-> None:
    # Complex grouping with sequences and choices
    tree = create_def_tree("((a | b*), (c?, d+), e*)")
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 2
    assert available_targets[0].name == "a"
    assert available_targets[1].name == "b"
    tree.match_element("a", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 1
    assert available_targets[0].name == "c"
    tree.match_element("c", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 3
    assert available_targets[0].name == "c"
    assert available_targets[1].name == "d"
    assert available_targets[2].name == "e"
    tree.match_element("d", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 1
    assert available_targets[0].name == "e"
    tree.match_element("e", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 1
    assert available_targets[0].name == "e"


def test_arcanetide()-> None:
    # Combining multiple choice and sequence rules
    tree = create_def_tree("(a, ((b, c*) | d)+, e?)")
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 1
    assert available_targets[0].name == "a"
    tree.match_element("a", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 3
    assert available_targets[0].name == "b"
    assert available_targets[1].name == "d"
    assert available_targets[2].name == "e"
    tree.match_element("b", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 2
    assert available_targets[0].name == "c"
    assert available_targets[1].name == "e"
    tree.match_element("c", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 2
    assert available_targets[0].name == "c"
    assert available_targets[1].name == "e"
    tree.match_element("e", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 1
    assert available_targets[0].name == "e"


def test_velcrolark_ver1()-> None:
    # Nested optional sequences
    tree = create_def_tree("((a?, b*), (c, (d | e+)))")
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 1
    assert available_targets[0].name == "a"
    tree.match_element("a", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 3
    assert available_targets[0].name == "a"
    assert available_targets[1].name == "b"
    assert available_targets[2].name == "c"
    tree.match_element("c", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 2
    assert available_targets[0].name == "d"
    assert available_targets[1].name == "e"
    tree.match_element("d", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 0

def test_velcrolark_ver2()-> None:
    # Nested optional sequences
    tree = create_def_tree("((a?, b*), (c, (d | e+)))")
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 1
    assert available_targets[0].name == "a"
    tree.match_element("a", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 3
    assert available_targets[0].name == "a"
    assert available_targets[1].name == "b"
    assert available_targets[2].name == "c"
    tree.match_element("c", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 2
    assert available_targets[0].name == "d"
    assert available_targets[1].name == "e"
    tree.match_element("e", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 0

def test_plasmafig()-> None:
    # Multiple sequences with zero-or-more repetitions
    tree = create_def_tree("((a, b*)*, (c, d+))")
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 2
    assert available_targets[0].name == "a"
    assert available_targets[1].name == "c"
    tree.match_element("a", available_targets)
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 2
    assert available_targets[0].name == "b"
    assert available_targets[1].name == "c"



def test_frostedmarble()-> None:
    # Repeating choices inside nested groups
    tree = create_def_tree("((a | (b, c)+)?, d*)")
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 0

def test_quirkynimbus()-> None:
    # Deeply nested optional and required elements
    tree = create_def_tree("(((a, b?) | c*), d, (e | f+))")
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 0

def test_zebraquirk()-> None:
    # Complex nesting with required sequences
    tree = create_def_tree("((a, (b | (c, d?))), e*, f)")
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 0

def test_orbitdoodle()-> None:
    # Grouping required elements with optional substructures
    tree = create_def_tree("((a, (b?, (c, d+)) | e), f)")
    available_targets = tree.get_available_targets()
    assert len(available_targets) == 0
