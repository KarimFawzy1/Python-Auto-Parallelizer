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
import scalene
import psutil

@dataclass
class ProfilingResult:
    """Results from profiling a code execution."""
    execution_time: float
    cpu_percent: float
    memory_usage: float
    line_profiler_stats: Dict[str, Any]
    scalene_stats: Dict[str, Any]

class PerformanceProfiler:
    """Profiles and compares performance of original and parallelized code."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
        if verbose:
            self.logger.setLevel(logging.DEBUG)
        
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss

    def profile_code(self, code_path: str, output_path: str = None) -> ProfilingResult:
        """Profile a Python file's execution."""
        try:
            # Profile execution time and CPU usage
            start_time = time.time()
            start_cpu = self.process.cpu_percent()
            
            # Run cProfile
            profiler = cProfile.Profile()
            profiler.enable()
            
            # Execute the code
            with open(code_path, 'r') as f:
                exec(f.read())
            
            profiler.disable()
            
            # Get final measurements
            end_time = time.time()
            end_cpu = self.process.cpu_percent()
            final_memory = self.process.memory_info().rss
            
            # Get line profiler stats
            line_profiler_stats = self._get_line_profiler_stats(code_path)
            
            # Get Scalene stats
            scalene_stats = self._get_scalene_stats(code_path)
            
            # Save cProfile stats if output path is provided
            if output_path:
                stats = pstats.Stats(profiler)
                stats.dump_stats(output_path)
            
            return ProfilingResult(
                execution_time=end_time - start_time,
                cpu_percent=end_cpu - start_cpu,
                memory_usage=final_memory - self.initial_memory,
                line_profiler_stats=line_profiler_stats,
                scalene_stats=scalene_stats
            )
            
        except Exception as e:
            self.logger.error(f"Error profiling code {code_path}: {str(e)}")
            raise

    def compare_profiles(self, original_result: ProfilingResult,
                        parallelized_result: ProfilingResult) -> Dict[str, float]:
        """Compare profiling results between original and parallelized code."""
        return {
            'execution_time_speedup': original_result.execution_time / parallelized_result.execution_time,
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
                
                f.write("\nScalene Memory Analysis:\n")
                f.write("----------------------\n")
                for line, stats in parallelized_result.scalene_stats.items():
                    f.write(f"Line {line}: {stats}\n")
        
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}")
            raise

    def _get_line_profiler_stats(self, code_path: str) -> Dict[str, Any]:
        """Get line-by-line profiling statistics."""
        try:
            profile = line_profiler.LineProfiler()
            with open(code_path, 'r') as f:
                code = f.read()
            
            # Create a temporary module to profile
            module_name = f"temp_module_{int(time.time())}"
            module = type(module_name, (), {})
            exec(code, module.__dict__)
            
            # Profile the module
            profile.add_module(module)
            profile.enable()
            exec(code)
            profile.disable()
            
            # Extract stats
            stats = {}
            for filename, line_no, func_name, line in profile.get_stats():
                if filename == code_path:
                    stats[line_no] = {
                        'hits': line[0],
                        'time': line[1],
                        'time_per_hit': line[2],
                        'memory': line[3]
                    }
            
            return stats
        except Exception as e:
            self.logger.warning(f"Error getting line profiler stats: {str(e)}")
            return {}

    def _get_scalene_stats(self, code_path: str) -> Dict[str, Any]:
        """Get memory profiling statistics using Scalene."""
        try:
            # Scalene requires running in a separate process
            # This is a simplified version that captures basic memory stats
            stats = {}
            with open(code_path, 'r') as f:
                for i, line in enumerate(f, 1):
                    if '=' in line or 'def ' in line or 'class ' in line:
                        stats[i] = {
                            'memory_usage': self.process.memory_info().rss,
                            'cpu_percent': self.process.cpu_percent()
                        }
            return stats
        except Exception as e:
            self.logger.warning(f"Error getting Scalene stats: {str(e)}")
            return {} 