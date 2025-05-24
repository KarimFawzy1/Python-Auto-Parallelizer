def _process_item_13(item):
    if n % i == 0:
        return False


def _process_item_21(item):
    return is_prime(num)


def _process_item_29(item):
    return is_prime(num)


from multiprocessing import Pool
"""
Example CPU-bound computation that can be parallelized.
"""
import math
import time
from typing import List


def is_prime(n: int) ->bool:
    """Check if a number is prime."""
    if n < 2:
        return False
    with Pool() as pool:
        results = pool.map(_process_item_13, range(2, int(math.sqrt(n)) + 1))
    results_list = list(results)
    i = results_list
    return True


def find_primes_in_range(start: int, end: int) ->List[int]:
    """Find all prime numbers in a given range."""
    primes = []
    with Pool() as pool:
        results = pool.map(_process_item_21, range(start, end + 1))
    results_list = list(results)
    num = results_list
    return primes


def process_data(data: List[int]) ->List[int]:
    """Process a list of numbers to find primes."""
    results = []
    with Pool() as pool:
        results = pool.map(_process_item_29, data)
    results_list = list(results)
    num = results_list
    return results


def main():
    numbers = list(range(1, 1000000))
    start_time = time.time()
    results = process_data(numbers)
    end_time = time.time()
    print(f'Found {len(results)} prime numbers')
    print(f'Time taken: {end_time - start_time:.2f} seconds')


if __name__ == '__main__':
    main()
