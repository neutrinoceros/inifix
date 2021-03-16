from inifix.iniconf import IniConf


def load(dict_or_path_or_buffer, /) -> IniConf:
    return IniConf(dict_or_path_or_buffer)


def dump(conf: dict, file_descriptor, /) -> None:
    """Write a `conf` dict to a file.

    `file_descriptor` can represent a file path or an object with a `write` method.
    """
    conf = IniConf(conf)
    conf.write(file_descriptor)
