#!/usr/bin/env python3
"""
Python Parallelizer - Main entry point
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from parallelizer.analyzer import CodeAnalyzer
from parallelizer.transformer import CodeTransformer
from parallelizer.profiler import PerformanceProfiler

def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Automatically parallelize Python code for multi-core systems.'
    )
    
    parser.add_argument(
        'input_file',
        type=str,
        help='Path to the Python file to parallelize'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (default: input_file_parallel.py)',
        default=None
    )
    
    parser.add_argument(
        '--strategy',
        type=str,
        choices=['multiprocessing', 'futures', 'joblib', 'numba'],
        help='Preferred parallelization strategy',
        default='multiprocessing'
    )
    
    parser.add_argument(
        '--profile',
        action='store_true',
        help='Enable performance profiling'
    )
    
    parser.add_argument(
        '--report',
        type=str,
        help='Path to save performance report (default: report.txt)',
        default='report.txt'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()

def get_output_path(input_path: str, output_path: Optional[str] = None) -> str:
    """Generate output file path if not specified."""
    if output_path:
        return output_path
    
    input_path = Path(input_path)
    return str(input_path.parent / f"{input_path.stem}_parallel{input_path.suffix}")

def main() -> int:
    """Main entry point."""
    args = parse_args()
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Validate input file
        if not os.path.isfile(args.input_file):
            logger.error(f"Input file not found: {args.input_file}")
            return 1
        
        # Generate output path
        output_path = get_output_path(args.input_file, args.output)
        
        # Initialize components
        analyzer = CodeAnalyzer(verbose=args.verbose)
        transformer = CodeTransformer(verbose=args.verbose)
        profiler = PerformanceProfiler(verbose=args.verbose)
        
        # Analyze code
        logger.info("Analyzing code for parallelization opportunities...")
        opportunities = analyzer.analyze_file(args.input_file)
        
        if not opportunities:
            logger.warning("No parallelization opportunities found.")
            return 0
        
        # Transform code
        logger.info("Transforming code...")
        transformed_code = transformer.transform_file(args.input_file, opportunities)
        
        # Write transformed code
        with open(output_path, 'w') as f:
            f.write(transformed_code)
        
        logger.info(f"Parallelized code written to: {output_path}")
        
        # Profile if requested
        if args.profile:
            logger.info("Profiling performance...")
            profiler.generate_report(
                args.input_file,
                output_path,
                args.report
            )
            logger.info(f"Performance report written to: {args.report}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 