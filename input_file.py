def square(x):
    return x * x

def main():
    data = list(range(100000))
    results = []
    for item in data:
        results.append(square(item))
    print(f"Sum of squares: {sum(results)}")

if __name__ == "__main__":
    main() 