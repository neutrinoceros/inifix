from inifix.idefix_conf import IdefixConf


def load(dict_or_path_or_buffer, /) -> IdefixConf:
    return IdefixConf(dict_or_path_or_buffer)


def dump(conf: dict, file_descriptor) -> None:
    """Write a `conf` dict to a file.

    `file_desciptor` can represent a path or an opened file.
    """
    conf = IdefixConf(conf)
    conf.write(file_descriptor)
