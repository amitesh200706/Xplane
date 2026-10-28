from Parser.Visitor import traverse, file_metadata, scope_stack, Entity_depth
import tree_sitter_python as tspython
from tree_sitter import Language, Parser


def lexer(file_path: str):
    PY_LANGUAGE = Language(tspython.language())
    parser = Parser(PY_LANGUAGE)

    entities = []
    symbol_index = {}
    
    with open(file_path) as f:
        code = f.read()

            
    tree = parser.parse(code.encode())
    cursor = tree.walk()
    
    traverse(cursor, scope_stack, entities)
    src_metadata = file_metadata(file_path)
    
    
    return src_metadata, entities



    
if __name__ == "__main__":
    src_metadata, entities = lexer("D:/untitled/Parser/Visitor.py")

    for entity in entities:
        indent = "    " * entity.depth
        print(f"{indent}Entity: {entity}\n ")
