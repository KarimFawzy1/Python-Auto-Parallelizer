"""
Code transformer module for parallelizing Python code.
"""

import ast
import astor
import logging
from typing import List, Dict, Any, Optional
from .analyzer import ParallelizationOpportunity

class CodeTransformer:
    """Transforms Python code to add parallelization."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
        if verbose:
            self.logger.setLevel(logging.DEBUG)
        
        # Track imports to add
        self.required_imports = set()
        # Track helper functions to add at module level
        self.helper_functions = []

    def transform_file(self, file_path: str, opportunities: List[ParallelizationOpportunity]) -> str:
        """Transform a Python file based on detected parallelization opportunities."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content)
            transformed_tree = self._transform_ast(tree, opportunities)
            return astor.to_source(transformed_tree)
        except Exception as e:
            self.logger.error(f"Error transforming file {file_path}: {str(e)}")
            raise

    def _transform_ast(self, tree: ast.AST, opportunities: List[ParallelizationOpportunity]) -> ast.AST:
        """Transform AST nodes based on parallelization opportunities."""
        transformer = ParallelizationTransformer(opportunities, self.verbose)
        transformed_tree = transformer.visit(tree)
        # Add required imports
        if transformer.required_imports:
            import_nodes = self._create_import_nodes(transformer.required_imports)
            transformed_tree.body = import_nodes + transformed_tree.body
        # Add helper functions at the module level
        if transformer.helper_functions:
            transformed_tree.body = transformer.helper_functions + transformed_tree.body
        return transformed_tree

    def _create_import_nodes(self, imports: set) -> List[ast.Import]:
        """Create AST nodes for required imports."""
        import_nodes = []
        for imp in sorted(imports):
            if '.' in imp:
                module, name = imp.rsplit('.', 1)
                import_nodes.append(
                    ast.ImportFrom(
                        module=module,
                        names=[ast.alias(name=name, asname=None)],
                        level=0
                    )
                )
            else:
                import_nodes.append(
                    ast.Import(names=[ast.alias(name=imp, asname=None)])
                )
        return import_nodes

class ParallelizationTransformer(ast.NodeTransformer):
    """AST transformer for parallelization."""
    
    def __init__(self, opportunities: List[ParallelizationOpportunity], verbose: bool = False):
        self.opportunities = {opp.line_number: opp for opp in opportunities}
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
        self.required_imports = set()
        self.helper_functions = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        # Replace loops inside the function if marked for parallelization
        new_body = []
        for stmt in node.body:
            if isinstance(stmt, ast.For) and stmt.lineno in self.opportunities:
                opp = self.opportunities[stmt.lineno]
                if opp.type == 'loop':
                    # Generate helper function at module level
                    helper_func_name = f'_process_item_{stmt.lineno}'
                    # Create a new body for the helper function that returns the computed value
                    helper_body = []
                    for child in stmt.body:
                        if isinstance(child, ast.Expr) and isinstance(child.value, ast.Call):
                            # Handle append calls
                            if isinstance(child.value.func, ast.Attribute) and child.value.func.attr == 'append':
                                helper_body.append(ast.Return(value=child.value.args[0]))
                            else:
                                helper_body.append(ast.Return(value=child.value))
                        elif isinstance(child, ast.If):
                            # Handle if statements
                            if isinstance(child.test, ast.Call):
                                helper_body.append(ast.Return(value=child.test))
                            else:
                                helper_body.append(child)
                        else:
                            helper_body.append(child)
                    
                    helper_func = ast.FunctionDef(
                        name=helper_func_name,
                        args=ast.arguments(
                            posonlyargs=[],
                            args=[ast.arg(arg='item', annotation=None)],
                            kwonlyargs=[],
                            kw_defaults=[],
                            defaults=[]
                        ),
                        body=helper_body,
                        decorator_list=[],
                        returns=None
                    )
                    self.helper_functions.append(helper_func)
                    
                    # Choose the appropriate parallelization strategy
                    if opp.suggested_strategy == 'multiprocessing':
                        self.required_imports.add('multiprocessing.Pool')
                        pool_assign = ast.With(
                            context_expr=ast.Call(
                                func=ast.Name(id='Pool', ctx=ast.Load()),
                                args=[],
                                keywords=[]
                            ),
                            optional_vars=ast.Name(id='pool', ctx=ast.Store()),
                            body=[
                                ast.Assign(
                                    targets=[ast.Name(id='results', ctx=ast.Store())],
                                    value=ast.Call(
                                        func=ast.Attribute(
                                            value=ast.Name(id='pool', ctx=ast.Load()),
                                            attr='map',
                                            ctx=ast.Load()
                                        ),
                                        args=[
                                            ast.Name(id=helper_func_name, ctx=ast.Load()),
                                            stmt.iter
                                        ],
                                        keywords=[]
                                    )
                                )
                            ]
                        )
                    else:  # concurrent.futures
                        self.required_imports.add('concurrent.futures.ThreadPoolExecutor')
                        pool_assign = ast.With(
                            context_expr=ast.Call(
                                func=ast.Name(id='ThreadPoolExecutor', ctx=ast.Load()),
                                args=[],
                                keywords=[]
                            ),
                            optional_vars=ast.Name(id='executor', ctx=ast.Store()),
                            body=[
                                ast.Assign(
                                    targets=[ast.Name(id='results', ctx=ast.Store())],
                                    value=ast.Call(
                                        func=ast.Attribute(
                                            value=ast.Name(id='executor', ctx=ast.Load()),
                                            attr='map',
                                            ctx=ast.Load()
                                        ),
                                        args=[
                                            ast.Name(id=helper_func_name, ctx=ast.Load()),
                                            stmt.iter
                                        ],
                                        keywords=[]
                                    )
                                )
                            ]
                        )
                    
                    # Convert results to list and assign to original target
                    list_convert = ast.Assign(
                        targets=[ast.Name(id='results_list', ctx=ast.Store())],
                        value=ast.Call(
                            func=ast.Name(id='list', ctx=ast.Load()),
                            args=[ast.Name(id='results', ctx=ast.Load())],
                            keywords=[]
                        )
                    )
                    
                    # Assign results to the original target
                    assign_results = ast.Assign(
                        targets=[stmt.target],
                        value=ast.Name(id='results_list', ctx=ast.Load())
                    )
                    
                    new_body.extend([pool_assign, list_convert, assign_results])
                    continue
            new_body.append(stmt)
        node.body = new_body
        return node

    def visit_For(self, node: ast.For) -> ast.AST:
        # Only transform top-level loops (not inside functions)
        if node.lineno in self.opportunities:
            opp = self.opportunities[node.lineno]
            if opp.type == 'loop' and opp.suggested_strategy == 'multiprocessing':
                helper_func_name = f'_process_item_{node.lineno}'
                helper_func = ast.FunctionDef(
                    name=helper_func_name,
                    args=ast.arguments(
                        posonlyargs=[],
                        args=[ast.arg(arg='item', annotation=None)],
                        kwonlyargs=[],
                        kw_defaults=[],
                        defaults=[]
                    ),
                    body=node.body,
                    decorator_list=[],
                    returns=None
                )
                self.helper_functions.append(helper_func)
                self.required_imports.add('multiprocessing.Pool')
                pool_assign = ast.With(
                    context_expr=ast.Call(
                        func=ast.Name(id='Pool', ctx=ast.Load()),
                        args=[],
                        keywords=[]
                    ),
                    optional_vars=ast.Name(id='pool', ctx=ast.Store()),
                    body=[
                        ast.Assign(
                            targets=[ast.Name(id='results', ctx=ast.Store())],
                            value=ast.Call(
                                func=ast.Attribute(
                                    value=ast.Name(id='pool', ctx=ast.Load()),
                                    attr='map',
                                    ctx=ast.Load()
                                ),
                                args=[
                                    ast.Name(id=helper_func_name, ctx=ast.Load()),
                                    node.iter
                                ],
                                keywords=[]
                            )
                        )
                    ]
                )
                assign_results = ast.Assign(
                    targets=[node.target],
                    value=ast.Name(id='results', ctx=ast.Load())
                )
                return [pool_assign, assign_results]
        return node

    def _transform_function(self, node: ast.FunctionDef, opp: ParallelizationOpportunity) -> ast.AST:
        if opp.suggested_strategy == 'numba':
            return self._transform_function_numba(node)
        return node

    def _transform_function_numba(self, node: ast.FunctionDef) -> ast.AST:
        self.required_imports.add('numba.jit')
        node.decorator_list.append(
            ast.Call(
                func=ast.Name(id='jit', ctx=ast.Load()),
                args=[],
                keywords=[
                    ast.keyword(
                        arg='nopython',
                        value=ast.Constant(value=True)
                    )
                ]
            )
        )
        return node 