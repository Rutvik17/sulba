def survivor(people, step):
    place = 0
    for size in range(2, people + 1):
        place = (place + step) % size
    return place + 1
