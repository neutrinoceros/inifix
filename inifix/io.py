from inifix.idefix_conf import IdefixConf


def load(dict_or_path_or_buffer, /) -> IdefixConf:
    return IdefixConf(dict_or_path_or_buffer)


def dump(conf: dict, file_descriptor, /) -> None:
    """Write a `conf` dict to a file.

    `file_descriptor` can represent a file path or an object with a `write` method.
    """
    conf = IdefixConf(conf)
    conf.write(file_descriptor)
