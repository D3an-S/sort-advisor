def insertion_sort(values):
    a = list(values)
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0 and a[j] > key:
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key
    return a


def merge_sort(values):
    if len(values) <= 1:
        return list(values)
    mid = len(values) // 2
    left, right = merge_sort(values[:mid]), merge_sort(values[mid:])
    result, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    return result + left[i:] + right[j:]


def quick_sort(arr):
    a = list(arr)
    _qs(a, 0, len(a) - 1)
    return a

def _qs(a, lo, hi):
    while lo < hi:
        p = a[(lo + hi) // 2]
        i, j = lo, hi
        while i <= j:
            while a[i] < p:
                i += 1
            while a[j] > p:
                j -= 1
            if i <= j:
                a[i], a[j] = a[j], a[i]
                i += 1
                j -= 1
        if j - lo < hi - i:
            _qs(a, lo, j)
            lo = i
        else:
            _qs(a, i, hi)
            hi = j
            
def heap_sort(values):
    a = list(values)
    n = len(a)

    def sift_down(start, end):
        root = start
        while 2 * root + 1 < end:
            child = 2 * root + 1
            if child + 1 < end and a[child] < a[child + 1]:
                child += 1
            if a[root] < a[child]:
                a[root], a[child] = a[child], a[root]
                root = child
            else:
                return

    for start in range(n // 2 - 1, -1, -1):
        sift_down(start, n)
    for end in range(n - 1, 0, -1):
        a[0], a[end] = a[end], a[0]
        sift_down(0, end)
    return a

ALGORITHMS = {
    "Insertion Sort": insertion_sort,
    "Merge Sort": merge_sort,
    "Quick Sort": quick_sort,
    "Heap Sort": heap_sort,
}