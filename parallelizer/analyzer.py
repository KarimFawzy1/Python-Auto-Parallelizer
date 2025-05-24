"""
Code analyzer module for detecting parallelization opportunities.
"""

import ast
import logging
from typing import List, Dict, Any, Set
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ParallelizationOpportunity:
    """Represents a detected opportunity for parallelization."""
    node: ast.AST
    type: str  # 'loop', 'function', 'io_bound', 'cpu_bound'
    confidence: float  # 0.0 to 1.0
    line_number: int
    description: str
    suggested_strategy: str

class CodeAnalyzer:
    """Analyzes Python code to detect parallelization opportunities."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
        if verbose:
            self.logger.setLevel(logging.DEBUG)
        
        # Keywords that suggest CPU-bound operations
        self.cpu_bound_keywords = {
            'math', 'numpy', 'scipy', 'pandas', 'compute', 'calculate',
            'process', 'transform', 'matrix', 'vector', 'array', 'is_prime',
            'sqrt', 'range', 'append', 'result'
        }
        
        # Keywords that suggest I/O-bound operations
        self.io_bound_keywords = {
            'read', 'write', 'file', 'network', 'http', 'request',
            'download', 'upload', 'socket', 'database', 'sql', 'open',
            'get', 'stream', 'content'
        }

    def analyze_file(self, file_path: str) -> List[ParallelizationOpportunity]:
        """Analyze a Python file for parallelization opportunities."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            return self._analyze_ast(tree)
        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {str(e)}")
            raise

    def _analyze_ast(self, tree: ast.AST) -> List[ParallelizationOpportunity]:
        """Analyze AST for parallelization opportunities."""
        opportunities = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                opp = self._analyze_loop(node)
                if opp:
                    opportunities.append(opp)
            elif isinstance(node, ast.FunctionDef):
                # Check for loops inside functions
                for child in ast.walk(node):
                    if isinstance(child, ast.For):
                        opp = self._analyze_loop(child)
                        if opp:
                            opportunities.append(opp)
                # Also check the function itself
                opp = self._analyze_function(node)
                if opp:
                    opportunities.append(opp)
        
        return opportunities

    def _analyze_loop(self, node: ast.For) -> ParallelizationOpportunity:
        """Analyze a for loop for parallelization potential."""
        # Check if loop body contains CPU-bound operations
        cpu_bound_score = self._calculate_cpu_bound_score(node)
        io_bound_score = self._calculate_io_bound_score(node)
        
        # Lower the threshold for detection
        if cpu_bound_score > 0.3:  # Changed from 0.5
            return ParallelizationOpportunity(
                node=node,
                type='loop',
                confidence=cpu_bound_score,
                line_number=node.lineno,
                description="CPU-bound loop detected",
                suggested_strategy='multiprocessing'
            )
        elif io_bound_score > 0.3:  # Changed from 0.5
            return ParallelizationOpportunity(
                node=node,
                type='loop',
                confidence=io_bound_score,
                line_number=node.lineno,
                description="I/O-bound loop detected",
                suggested_strategy='concurrent.futures'
            )
        
        # If we have a loop with a significant body, consider it for parallelization
        if len(node.body) > 1:
            return ParallelizationOpportunity(
                node=node,
                type='loop',
                confidence=0.4,
                line_number=node.lineno,
                description="Loop with significant body detected",
                suggested_strategy='multiprocessing'
            )
        
        return None

    def _analyze_function(self, node: ast.FunctionDef) -> ParallelizationOpportunity:
        """Analyze a function for parallelization potential."""
        cpu_bound_score = self._calculate_cpu_bound_score(node)
        io_bound_score = self._calculate_io_bound_score(node)
        
        # Lower the threshold for detection
        if cpu_bound_score > 0.3:  # Changed from 0.5
            return ParallelizationOpportunity(
                node=node,
                type='function',
                confidence=cpu_bound_score,
                line_number=node.lineno,
                description="CPU-bound function detected",
                suggested_strategy='numba'
            )
        elif io_bound_score > 0.3:  # Changed from 0.5
            return ParallelizationOpportunity(
                node=node,
                type='function',
                confidence=io_bound_score,
                line_number=node.lineno,
                description="I/O-bound function detected",
                suggested_strategy='concurrent.futures'
            )
        
        # If we have a function with a significant body, consider it for parallelization
        if len(node.body) > 2:
            return ParallelizationOpportunity(
                node=node,
                type='function',
                confidence=0.4,
                line_number=node.lineno,
                description="Function with significant body detected",
                suggested_strategy='numba'
            )
        
        return None

    def _calculate_cpu_bound_score(self, node: ast.AST) -> float:
        """Calculate how likely a node is CPU-bound."""
        score = 0.0
        total_nodes = 0
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                total_nodes += 1
                func_name = self._get_function_name(child)
                if any(keyword in func_name.lower() for keyword in self.cpu_bound_keywords):
                    score += 1.0
            elif isinstance(child, (ast.BinOp, ast.UnaryOp, ast.Compare)):
                total_nodes += 1
                score += 0.5
            elif isinstance(child, ast.For):
                total_nodes += 1
                score += 0.3  # Loops often indicate CPU-bound work
            elif isinstance(child, ast.If):
                total_nodes += 1
                score += 0.2  # Conditionals often indicate computation
        
        return score / max(total_nodes, 1)

    def _calculate_io_bound_score(self, node: ast.AST) -> float:
        """Calculate how likely a node is I/O-bound."""
        score = 0.0
        total_nodes = 0
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                total_nodes += 1
                func_name = self._get_function_name(child)
                if any(keyword in func_name.lower() for keyword in self.io_bound_keywords):
                    score += 1.0
            elif isinstance(child, ast.With):
                total_nodes += 1
                score += 0.5  # Context managers often indicate I/O
            elif isinstance(child, ast.Try):
                total_nodes += 1
                score += 0.3  # Try blocks often indicate I/O error handling
        
        return score / max(total_nodes, 1)

    def _get_function_name(self, node: ast.Call) -> str:
        """Extract function name from a Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return "" 