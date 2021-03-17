from typing import TextIO, Union

from inifix._typing import PathLike
from inifix.iniconf import InifixConf


def load(dict_or_path_or_buffer: Union[dict, PathLike, TextIO], /) -> InifixConf:
    return InifixConf(dict_or_path_or_buffer)


def dump(conf: dict, file_descriptor: TextIO, /) -> None:
    """Write a `conf` dict to a file.

    `file_descriptor` can represent a file path or an object with a `write` method.
    """
    conf = InifixConf(conf)
    conf.write(file_descriptor)
