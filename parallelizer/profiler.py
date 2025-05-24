"""
Performance profiling module for comparing original and parallelized code.
"""

import cProfile
import pstats
import time
import logging
import os
from typing import Dict, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import line_profiler
import psutil
import threading
import queue
import ast

@dataclass
class ProfilingResult:
    """Results from profiling a code execution."""
    execution_time: float
    cpu_percent: float
    memory_usage: float
    line_profiler_stats: Dict[str, Any]
    memory_stats: Dict[str, Any]

class PerformanceProfiler:
    """Profiles and compares performance of original and parallelized code."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
        if verbose:
            self.logger.setLevel(logging.DEBUG)
        
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss
        self.cpu_queue = queue.Queue()
        self.memory_queue = queue.Queue()

    def _monitor_cpu(self, stop_event):
        """Monitor CPU usage in a separate thread."""
        cpu_percent = 0
        while not stop_event.is_set():
            current_cpu = self.process.cpu_percent(interval=0.1)
            cpu_percent = max(cpu_percent, current_cpu)
        self.cpu_queue.put(cpu_percent)

    def _monitor_memory(self, stop_event):
        """Monitor memory usage in a separate thread."""
        max_memory = 0
        while not stop_event.is_set():
            current_memory = self.process.memory_info().rss
            max_memory = max(max_memory, current_memory)
        self.memory_queue.put(max_memory - self.initial_memory)

    def profile_code(self, code_path: str, output_path: str = None) -> ProfilingResult:
        """Profile a Python file's execution."""
        try:
            # Start monitoring threads
            stop_event = threading.Event()
            cpu_thread = threading.Thread(target=self._monitor_cpu, args=(stop_event,))
            memory_thread = threading.Thread(target=self._monitor_memory, args=(stop_event,))
            cpu_thread.start()
            memory_thread.start()

            # Profile execution time
            start_time = time.time()
            
            # Run cProfile
            profiler = cProfile.Profile()
            profiler.enable()
            
            # Execute the code
            with open(code_path, 'r') as f:
                exec(f.read())
            
            profiler.disable()
            
            # Get final measurements
            end_time = time.time()
            stop_event.set()
            cpu_thread.join()
            memory_thread.join()
            
            cpu_percent = self.cpu_queue.get()
            memory_usage = self.memory_queue.get()
            
            # Get line profiler stats
            line_profiler_stats = self._get_line_profiler_stats(code_path)
            
            # Get memory stats
            memory_stats = self._get_memory_stats(code_path)
            
            # Save cProfile stats if output path is provided
            if output_path:
                stats = pstats.Stats(profiler)
                stats.dump_stats(output_path)
            
            return ProfilingResult(
                execution_time=end_time - start_time,
                cpu_percent=cpu_percent,
                memory_usage=memory_usage,
                line_profiler_stats=line_profiler_stats,
                memory_stats=memory_stats
            )
            
        except Exception as e:
            self.logger.error(f"Error profiling code {code_path}: {str(e)}")
            raise

    def compare_profiles(self, original_result: ProfilingResult,
                        parallelized_result: ProfilingResult) -> Dict[str, float]:
        """Compare profiling results between original and parallelized code."""
        return {
            'execution_time_speedup': original_result.execution_time / parallelized_result.execution_time if parallelized_result.execution_time > 0 else 0,
            'cpu_utilization_change': parallelized_result.cpu_percent - original_result.cpu_percent,
            'memory_usage_change': parallelized_result.memory_usage - original_result.memory_usage
        }

    def generate_report(self, original_path: str, parallelized_path: str,
                       output_path: str) -> None:
        """Generate a comprehensive performance report."""
        try:
            # Profile both versions
            original_result = self.profile_code(original_path)
            parallelized_result = self.profile_code(parallelized_path)
            
            # Compare results
            comparison = self.compare_profiles(original_result, parallelized_result)
            
            # Generate report
            with open(output_path, 'w') as f:
                f.write("Performance Analysis Report\n")
                f.write("========================\n\n")
                
                f.write("Original Code Performance:\n")
                f.write(f"Execution Time: {original_result.execution_time:.2f} seconds\n")
                f.write(f"CPU Usage: {original_result.cpu_percent:.1f}%\n")
                f.write(f"Memory Usage: {original_result.memory_usage / 1024 / 1024:.2f} MB\n\n")
                
                f.write("Parallelized Code Performance:\n")
                f.write(f"Execution Time: {parallelized_result.execution_time:.2f} seconds\n")
                f.write(f"CPU Usage: {parallelized_result.cpu_percent:.1f}%\n")
                f.write(f"Memory Usage: {parallelized_result.memory_usage / 1024 / 1024:.2f} MB\n\n")
                
                f.write("Performance Improvements:\n")
                f.write(f"Speedup: {comparison['execution_time_speedup']:.2f}x\n")
                f.write(f"CPU Utilization Change: {comparison['cpu_utilization_change']:+.1f}%\n")
                f.write(f"Memory Usage Change: {comparison['memory_usage_change'] / 1024 / 1024:+.2f} MB\n\n")
                
                f.write("Detailed Line Profiling:\n")
                f.write("----------------------\n")
                for line, stats in parallelized_result.line_profiler_stats.items():
                    f.write(f"Line {line}: {stats}\n")
                
                f.write("\nMemory Analysis:\n")
                f.write("----------------------\n")
                for line, stats in parallelized_result.memory_stats.items():
                    f.write(f"Line {line}: {stats}\n")
        
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}")
            raise

    def _get_line_profiler_stats(self, code_path: str) -> Dict[str, Any]:
        """Get line-by-line profiling statistics."""
        try:
            profile = line_profiler.LineProfiler()
            
            # Create a namespace for execution
            namespace = {}
            
            # Add the code to the profiler
            with open(code_path, 'r') as f:
                code = f.read()
            
            # Parse the code to find functions
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Create a function object for profiling
                    func_code = compile(ast.Module(body=[node], type_ignores=[]), code_path, 'exec')
                    exec(func_code, namespace)
                    profile.add_function(namespace[node.name])
            
            # Profile the code
            profile.enable()
            exec(code, namespace)
            profile.disable()
            
            # Extract stats
            stats = {}
            for filename, line_no, func_name, line in profile.get_stats():
                if filename == code_path:
                    stats[line_no] = {
                        'hits': line[0],
                        'time': line[1],
                        'time_per_hit': line[2]
                    }
            
            return stats
        except Exception as e:
            self.logger.warning(f"Error getting line profiler stats: {str(e)}")
            return {}

    def _get_memory_stats(self, code_path: str) -> Dict[str, Any]:
        """Get memory usage statistics per line."""
        try:
            stats = {}
            initial_memory = self.process.memory_info().rss
            
            with open(code_path, 'r') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                if line.strip():
                    # Execute the line and measure memory
                    try:
                        exec(line)
                        current_memory = self.process.memory_info().rss
                        stats[i] = {
                            'memory_usage': current_memory - initial_memory,
                            'cpu_percent': self.process.cpu_percent()
                        }
                    except:
                        continue
            
            return stats
        except Exception as e:
            self.logger.warning(f"Error getting memory stats: {str(e)}")
            return {} 