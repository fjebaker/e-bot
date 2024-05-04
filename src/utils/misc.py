def dict_reverse_lookup(dictionary: dict, value):
    """
    Utility function to perform reverse lookup in a dict where each value is unique

    :param dictionary: the dict to reverse lookup in
    :param value: the value to look for
    :returns: the key whose value in the dictionary is equal to value, else None
    """
    item_generator = filter(lambda i: i[1] == value, dictionary.items())
    if item_generator:
        return next(item_generator)[0]
    else:
        return None


def async_context_wrap(ctx, func):
    # pylint: disable=unused-argument
    async def _callback(*args):
        # turns out python contextualizes itself???
        return await func(*args)

    return _callback
