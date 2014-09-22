
def strclass(cls):
    """Generate a class name string, including module path.

    Remove module '__main__' from the ID, as it is not useful in most cases.
    """
    if cls.__module__ == '__main__':
        return cls.__name__
    return "{0}.{1}".format(cls.__module__, cls.__name__)
