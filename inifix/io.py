from inifix.iniconf import InifixConf


def load(dict_or_path_or_buffer, /) -> InifixConf:
    return InifixConf(dict_or_path_or_buffer)


def dump(conf: dict, file_descriptor, /) -> None:
    """Write a `conf` dict to a file.

    `file_descriptor` can represent a file path or an object with a `write` method.
    """
    conf = InifixConf(conf)
    conf.write(file_descriptor)
