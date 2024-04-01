import ast
import importlib


class CodeParser:
    """Parse the code and split it into functions and classes."""
    def __call__(self, code_import_path: str):
        code = self._read_code(code_import_path)
        imports, classes, functions = self._split_code(code)
        return imports, classes, functions
        
    
    def _read_code(self, code_import_path: str) -> str:
        """Read the code from the given module."""
        module = importlib.import_module(code_import_path)
        with open(module.__file__) as f:
            code = f.read()
        return code
    
    def _split_code(self, code: str) -> tuple[list[str], list[str], list[str]]:
        """Split the code into functions and classes."""
        ast_node = ast.parse(code)
        classes = [ast.get_source_segment(code, n) for n in ast.walk(ast_node) if isinstance(n, ast.ClassDef)]

        # Filter out methods (functions inside classes)
        methods = {n for c in ast.walk(ast_node) if isinstance(c, ast.ClassDef)
                for n in c.body if isinstance(n, ast.FunctionDef)}

        # Get top-level functions (not methods)
        functions = [ast.get_source_segment(code, n) for n in ast.walk(ast_node) 
                    if isinstance(n, ast.FunctionDef) and n not in methods]
        
        imports = self._get_imports(code)

        return imports, classes, functions
    
    def _get_imports(code: str) -> list[str]:
        """Extract import statements from the given code."""
        ast_node = ast.parse(code)
        imports = []

        for node in ast.walk(ast_node):
            if isinstance(node, ast.Import):
                module_names = [f"import {alias.name}" for alias in node.names]
                imports.extend(module_names)
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module if node.module else ''
                imported_names = ', '.join(alias.name for alias in node.names)
                imports.append(f"from {module_name} import {imported_names}")

        return imports

