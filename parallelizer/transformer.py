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
        
        # Track shared variables that need synchronization
        self.shared_variables = set()

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
        self.shared_variables = set()

    def visit_For(self, node: ast.For) -> ast.AST:
        """Transform for loops for parallelization."""
        if node.lineno in self.opportunities:
            opp = self.opportunities[node.lineno]
            if opp.type == 'loop':
                return self._transform_loop(node, opp)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        """Transform functions for parallelization."""
        if node.lineno in self.opportunities:
            opp = self.opportunities[node.lineno]
            if opp.type == 'function':
                return self._transform_function(node, opp)
        return node

    def _transform_loop(self, node: ast.For, opp: ParallelizationOpportunity) -> ast.AST:
        """Transform a for loop based on the parallelization strategy."""
        if opp.suggested_strategy == 'multiprocessing':
            return self._transform_loop_multiprocessing(node)
        elif opp.suggested_strategy == 'concurrent.futures':
            return self._transform_loop_futures(node)
        return node

    def _transform_loop_multiprocessing(self, node: ast.For) -> ast.AST:
        """Transform a for loop using multiprocessing."""
        self.required_imports.add('multiprocessing.Pool')
        
        # Create a function for the loop body
        loop_func = ast.FunctionDef(
            name=f'_process_item_{node.lineno}',
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
        
        # Create the parallelized loop
        pool = ast.Name(id='pool', ctx=ast.Store())
        with_block = ast.With(
            context_expr=ast.Call(
                func=ast.Name(id='Pool', ctx=ast.Load()),
                args=[],
                keywords=[]
            ),
            optional_vars=pool,
            body=[
                ast.Assign(
                    targets=[ast.Name(id='results', ctx=ast.Store())],
                    value=ast.Call(
                        func=ast.Attribute(
                            value=pool,
                            attr='map',
                            ctx=ast.Load()
                        ),
                        args=[
                            ast.Name(id=loop_func.name, ctx=ast.Load()),
                            node.iter
                        ],
                        keywords=[]
                    )
                )
            ]
        )
        
        return ast.Module(body=[loop_func, with_block])

    def _transform_loop_futures(self, node: ast.For) -> ast.AST:
        """Transform a for loop using concurrent.futures."""
        self.required_imports.add('concurrent.futures.ProcessPoolExecutor')
        
        # Create a function for the loop body
        loop_func = ast.FunctionDef(
            name=f'_process_item_{node.lineno}',
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
        
        # Create the parallelized loop
        executor = ast.Name(id='executor', ctx=ast.Store())
        with_block = ast.With(
            context_expr=ast.Call(
                func=ast.Name(id='ProcessPoolExecutor', ctx=ast.Load()),
                args=[],
                keywords=[]
            ),
            optional_vars=executor,
            body=[
                ast.Assign(
                    targets=[ast.Name(id='results', ctx=ast.Store())],
                    value=ast.Call(
                        func=ast.Attribute(
                            value=executor,
                            attr='map',
                            ctx=ast.Load()
                        ),
                        args=[
                            ast.Name(id=loop_func.name, ctx=ast.Load()),
                            node.iter
                        ],
                        keywords=[]
                    )
                )
            ]
        )
        
        return ast.Module(body=[loop_func, with_block])

    def _transform_function(self, node: ast.FunctionDef, opp: ParallelizationOpportunity) -> ast.AST:
        """Transform a function based on the parallelization strategy."""
        if opp.suggested_strategy == 'numba':
            return self._transform_function_numba(node)
        return node

    def _transform_function_numba(self, node: ast.FunctionDef) -> ast.AST:
        """Transform a function using Numba."""
        self.required_imports.add('numba.jit')
        
        # Add @jit decorator
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