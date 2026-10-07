def is_numeric(values):
    return all(isinstance(v, (int, float)) for v in values)

def length(values):
    return len(values)


def sortedness(values):
    if length(values) < 2: 
        return 1.0

    counter = 0
    for i in range(length(values)-1):
        if values[i] <= values[i+1]:
            counter += 1
    return counter / length(values)-1


def duplicates(values): 
    if not values:
        return 0.0
    else: 
        return 1 - len(set(values)) / len(values)


def analyze(values):
    return {
        "n": len(values),
        "sortedness": sortedness(values),
        "duplicate_ratio": duplicates(values),
        "is_numeric": is_numeric(values),
    }