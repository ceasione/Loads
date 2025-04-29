

def log_safely(message):
    try:
        print(message)
    except OSError:
        pass


def __sliding_window(iterable, n):
    # yields a number of lists where len=n sliced from iterable
    if len(iterable) > n > 0:
        possible_windows = len(iterable) - n + 1
        for pointer in range(0, possible_windows):
            closing = pointer+n
            yield iterable[pointer:closing]
    else:
        yield iterable


def __remove_duplicates(places):
    # This removes duplicates in a row elements from list by 'name' field
    # Logic assumes that first place is the farthest
    # Not used in this project. Only for further use
    nodupes = list()
    nodupes.append(places[0])
    for window in __sliding_window(places, 2):
        if window[0].name != window[1].name:
            nodupes.append(window[1])
        else:
            nodupes.pop()
            nodupes.append(window[1])
    return nodupes


def __merge_same(places):

    # Merges 2 places to 1 if they are the same

    if len(places) != 4:
        raise RuntimeError('Internal error 4')

    upd_places = list()
    try:

        if places[0].name not in places[1].name:
            upd_places.append(places[0])
            upd_places.append(places[1])
        else:
            upd_places.append(places[0])

        if places[2].name not in places[3].name:
            upd_places.append(places[2])
            upd_places.append(places[3])
        else:
            upd_places.append(places[3])

        return upd_places
    except TypeError:
        return places
