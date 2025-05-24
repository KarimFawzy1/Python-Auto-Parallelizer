def _process_item_33(item):
    filename = url.split('/')[-1]
    save_path = os.path.join(output_dir, filename)
    results[url] = download_file(url, save_path)


from concurrent.futures import ThreadPoolExecutor
"""
Example I/O-bound operations that can be parallelized.
"""
import os
import time
import requests
from typing import List, Dict
from pathlib import Path


def download_file(url: str, save_path: str) ->bool:
    """Download a file from a URL."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f'Error downloading {url}: {str(e)}')
        return False


def process_urls(urls: List[str], output_dir: str) ->Dict[str, bool]:
    """Process a list of URLs to download files."""
    results = {}
    os.makedirs(output_dir, exist_ok=True)
    with ThreadPoolExecutor() as executor:
        results = executor.map(_process_item_33, urls)
    results_list = list(results)
    url = results_list
    return results


def main():
    urls = ['https://raw.githubusercontent.com/python/cpython/main/README.rst',
        'https://raw.githubusercontent.com/python/cpython/main/LICENSE',
        'https://raw.githubusercontent.com/python/cpython/main/Misc/README',
        'https://raw.githubusercontent.com/python/cpython/main/Misc/NEWS',
        'https://raw.githubusercontent.com/python/cpython/main/Misc/ACKS']
    output_dir = 'downloaded_files'
    start_time = time.time()
    results = process_urls(urls, output_dir)
    end_time = time.time()
    successful = sum(1 for success in results.values() if success)
    print(f'Successfully downloaded {successful} out of {len(urls)} files')
    print(f'Time taken: {end_time - start_time:.2f} seconds')


if __name__ == '__main__':
    main()
