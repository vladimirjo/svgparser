from dtd import ElementDefinitionsDefined, DefinitionTreeValidator
from buffer_controller import Fragment, Token

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

def create_def_tree(definition: str) -> DefinitionTreeValidator:
    tokens = tokenize_definition(definition)
    edd = ElementDefinitionsDefined(tokens)
    def_tree = DefinitionTreeValidator(edd)
    return def_tree
