import functools


def _mergedicts(dict1: dict, dict2: dict):
    """Function adapted from https://stackoverflow.com/a/7205672"""
    for k in set(dict1.keys()).union(dict2.keys()):
        if k in dict1 and k in dict2:
            if isinstance(dict1[k], dict) and isinstance(dict2[k], dict):
                yield (k, dict(_mergedicts(dict1[k], dict2[k])))
            else:
                # If one of the values is not a dict, you can't continue merging it.
                # Value from second dict overrides one in first and we move on.
                yield (k, dict2[k])
                # Alternatively, replace this with exception raiser to alert you of value conflicts
        elif k in dict1:
            yield (k, dict1[k])
        else:
            yield (k, dict2[k])


def _dmerge(d1, d2) -> dict:
    """Convenience function to turn :func:`._mergedicts` into a binary operator."""
    return dict(_mergedicts(d1, d2))


def dmerge(*dicts) -> dict:
    """Recursively deep merges all dictionary in the arguments."""
    return functools.reduce(_dmerge, dicts)
