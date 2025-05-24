"""
Example CPU-bound computation that can be parallelized.
"""

import math
import time
from typing import List

def is_prime(n: int) -> bool:
    """Check if a number is prime."""
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

def find_primes_in_range(start: int, end: int) -> List[int]:
    """Find all prime numbers in a given range."""
    primes = []
    for num in range(start, end + 1):
        if is_prime(num):
            primes.append(num)
    return primes

def process_data(data: List[int]) -> List[int]:
    """Process a list of numbers to find primes."""
    results = []
    for num in data:
        if is_prime(num):
            results.append(num)
    return results

def main():
    # Generate a large list of numbers
    numbers = list(range(1, 1000000))
    
    # Process the numbers sequentially
    start_time = time.time()
    results = process_data(numbers)
    end_time = time.time()
    
    print(f"Found {len(results)} prime numbers")
    print(f"Time taken: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main() 