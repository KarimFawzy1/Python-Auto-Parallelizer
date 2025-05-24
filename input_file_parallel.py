from numba import jit


@jit(nopython=True)
def square(x):
    return x * x


@jit(nopython=True)
def main():
    data = list(range(100000))
    results = []
    for item in data:
        results.append(square(item))
    print(f'Sum of squares: {sum(results)}')


if __name__ == '__main__':
    main()
