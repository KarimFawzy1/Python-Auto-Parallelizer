# Python Parallelizer

An intelligent tool that automatically parallelizes sequential Python code to run efficiently on multi-core systems.

## Features

- Automatic detection of parallelization opportunities in Python code
- Support for both CPU-bound and I/O-bound task parallelization
- Multiple parallelization strategies using:
  - multiprocessing
  - concurrent.futures
  - joblib
  - Numba (for computational acceleration)
- Performance profiling and comparison
- Windows OS compatibility

## Installation

1. Clone this repository:

```bash
git clone https://github.com/yourusername/python-parallelizer.git
cd python-parallelizer
```

2. Create a virtual environment (recommended):

```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Basic usage:

```bash
python parallelizer.py input_file.py
```

Advanced usage with options:

```bash
python parallelizer.py input_file.py --strategy multiprocessing --profile --output parallel_version.py
```

### Command Line Arguments

- `--strategy`: Choose parallelization strategy (multiprocessing, futures, joblib, numba)
- `--profile`: Enable performance profiling
- `--output`: Specify output file name
- `--workers`: Number of worker processes/threads
- `--verbose`: Enable detailed logging

## Project Structure

```
python-parallelizer/
├── parallelizer/
│   ├── __init__.py
│   ├── analyzer.py        # Code analysis and bottleneck detection
│   ├── transformer.py     # Code transformation logic
│   ├── parallelizers/     # Different parallelization strategies
│   │   ├── __init__.py
│   │   ├── multiprocessing.py
│   │   ├── futures.py
│   │   ├── joblib.py
│   │   └── numba.py
│   └── profiler.py        # Performance profiling
├── examples/             # Example scripts
│   ├── cpu_bound.py
│   └── io_bound.py
├── tests/               # Test suite
├── parallelizer.py      # Main entry point
├── requirements.txt     # Project dependencies
└── README.md           # This file
```

## Example

Input code (sequential):

```python
def process_data(data):
    results = []
    for item in data:
        result = heavy_computation(item)
        results.append(result)
    return results
```

Parallelized output:

```python
from concurrent.futures import ProcessPoolExecutor

def process_data(data):
    with ProcessPoolExecutor() as executor:
        results = list(executor.map(heavy_computation, data))
    return results
```

## Performance Profiling

The tool generates a detailed performance report including:

- Execution time comparison
- Memory usage analysis
- CPU utilization
- Speedup metrics
- Parallelization effectiveness

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
