def _process_item_7(item):
    return square(item)


from multiprocessing import Pool


def square(x):
    return x * x


def main():
    data = list(range(100000))
    results = []
    with Pool() as pool:
        results = pool.map(_process_item_7, data)
    results_list = list(results)
    item = results_list
    print(f'Sum of squares: {sum(results)}')


if __name__ == '__main__':
    main()
