from dtd import ElementDefinitionsDefined, DefinitionTreeValidator, TagElement, PCDATAElement
from buffer_controller import Fragment, Token
from errorcollector import ErrorCollector

def tokenize_definition(definition: str) -> list[Token]:
    tokens: list[Token] = []
    accumulator: str = ""
    for char in definition:
        if char.isspace():
            continue
        if any(char == operator for operator in "|(),?*+"):
            if accumulator != "":
                tokens.append(Token(Fragment(accumulator, 0,0)))
                accumulator = ""
            tokens.append(Token(Fragment(char, 0,0)))
            continue
        accumulator += char
    return tokens

def tokenize_elements_to_validate(targets: list[str]) -> list[Token]:
    tokenized_targets: list[Token] = []
    for target in targets:
        token = Token(Fragment(target, 0, 0))
        tokenized_targets.append(token)
    return tokenized_targets

def create_pcdata_element(content: str) -> PCDATAElement:
    return PCDATAElement(Token(Fragment(content, 0, 0)))

def create_tag_element(name: str) -> TagElement:
    return TagElement(Token(Fragment(name, 0, 0)))

class MixedContentTest:
    def __init__(self) -> None:
        self.mixed_contents: list[PCDATAElement | TagElement] = []

    def add_pcdata(self, content: str) -> None:
        self.mixed_contents.append(create_pcdata_element(content))

    def add_element(self, name: str) -> None:
        self.mixed_contents.append(create_tag_element(name))

def create_def_tree(definition: str) -> DefinitionTreeValidator:
    tokens = tokenize_definition(definition)
    edd = ElementDefinitionsDefined(tokens)
    def_tree = DefinitionTreeValidator(edd, ErrorCollector())
    return def_tree
