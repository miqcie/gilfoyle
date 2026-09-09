def shared_members(left, right):
    matches = []
    for item in left:
        if item in right:
            matches.append(item)
    return matches
