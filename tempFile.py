import concurrent.futures


def iterate():
    global ae
    a = 0
    for i in range(10000):
        a += i
    return a


if __name__ == '__main__':
    with concurrent.futures.ProcessPoolExecutor() as executor:
        e = executor.submit(iterate)
        f = executor.submit(iterate)
        print(e.result())
        print(f.result())
