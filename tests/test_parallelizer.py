"""
Tests for the Python Parallelizer tool.
"""

import os
import pytest
from pathlib import Path
from parallelizer.analyzer import CodeAnalyzer
from parallelizer.transformer import CodeTransformer
from parallelizer.profiler import PerformanceProfiler

@pytest.fixture
def example_cpu_code():
    """Example CPU-bound code for testing."""
    return """
def process_data(data):
    results = []
    for item in data:
        result = item * item
        results.append(result)
    return results
"""

@pytest.fixture
def example_io_code():
    """Example I/O-bound code for testing."""
    return """
def process_files(files):
    results = []
    for file in files:
        with open(file, 'r') as f:
            content = f.read()
        results.append(content)
    return results
"""

def test_analyzer_detects_cpu_bound(example_cpu_code, tmp_path):
    """Test that the analyzer detects CPU-bound operations."""
    # Write example code to a temporary file
    test_file = tmp_path / "test_cpu.py"
    test_file.write_text(example_cpu_code)
    
    # Analyze the code
    analyzer = CodeAnalyzer(verbose=True)
    opportunities = analyzer.analyze_file(str(test_file))
    
    # Check that opportunities were found
    assert len(opportunities) > 0
    assert any(opp.type == 'loop' for opp in opportunities)
    assert any(opp.suggested_strategy == 'multiprocessing' for opp in opportunities)

def test_analyzer_detects_io_bound(example_io_code, tmp_path):
    """Test that the analyzer detects I/O-bound operations."""
    # Write example code to a temporary file
    test_file = tmp_path / "test_io.py"
    test_file.write_text(example_io_code)
    
    # Analyze the code
    analyzer = CodeAnalyzer(verbose=True)
    opportunities = analyzer.analyze_file(str(test_file))
    
    # Check that opportunities were found
    assert len(opportunities) > 0
    assert any(opp.type == 'loop' for opp in opportunities)
    assert any(opp.suggested_strategy == 'concurrent.futures' for opp in opportunities)

def test_transformer_parallelizes_cpu_bound(example_cpu_code, tmp_path):
    """Test that the transformer parallelizes CPU-bound code."""
    # Write example code to a temporary file
    test_file = tmp_path / "test_cpu.py"
    test_file.write_text(example_cpu_code)
    
    # Analyze and transform the code
    analyzer = CodeAnalyzer(verbose=True)
    transformer = CodeTransformer(verbose=True)
    
    opportunities = analyzer.analyze_file(str(test_file))
    transformed_code = transformer.transform_file(str(test_file), opportunities)
    
    # Check that the code was transformed
    assert 'multiprocessing' in transformed_code
    assert 'Pool' in transformed_code
    assert 'map' in transformed_code

def test_transformer_parallelizes_io_bound(example_io_code, tmp_path):
    """Test that the transformer parallelizes I/O-bound code."""
    # Write example code to a temporary file
    test_file = tmp_path / "test_io.py"
    test_file.write_text(example_io_code)
    
    # Analyze and transform the code
    analyzer = CodeAnalyzer(verbose=True)
    transformer = CodeTransformer(verbose=True)
    
    opportunities = analyzer.analyze_file(str(test_file))
    transformed_code = transformer.transform_file(str(test_file), opportunities)
    
    # Check that the code was transformed
    assert 'concurrent.futures' in transformed_code
    assert 'ProcessPoolExecutor' in transformed_code
    assert 'map' in transformed_code

def test_profiler_generates_report(example_cpu_code, tmp_path):
    """Test that the profiler generates a performance report."""
    # Write example code to a temporary file
    test_file = tmp_path / "test_cpu.py"
    test_file.write_text(example_cpu_code)
    
    # Create a parallelized version
    analyzer = CodeAnalyzer(verbose=True)
    transformer = CodeTransformer(verbose=True)
    
    opportunities = analyzer.analyze_file(str(test_file))
    transformed_code = transformer.transform_file(str(test_file), opportunities)
    
    parallel_file = tmp_path / "test_cpu_parallel.py"
    parallel_file.write_text(transformed_code)
    
    # Generate performance report
    profiler = PerformanceProfiler(verbose=True)
    report_file = tmp_path / "report.txt"
    
    profiler.generate_report(
        str(test_file),
        str(parallel_file),
        str(report_file)
    )
    
    # Check that the report was generated
    assert report_file.exists()
    report_content = report_file.read_text()
    assert "Performance Analysis Report" in report_content
    assert "Original Code Performance" in report_content
    assert "Parallelized Code Performance" in report_content 