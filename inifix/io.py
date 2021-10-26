from typing import TextIO
from typing import Union

from inifix._deprecation import future_positional_only
from inifix._typing import PathLike
from inifix.iniconf import InifixConf


@future_positional_only({0: "dict_or_path_or_buffer"})
def load(dict_or_path_or_buffer: Union[dict, PathLike, TextIO]) -> InifixConf:
    return InifixConf(dict_or_path_or_buffer)


@future_positional_only({0: "conf", 1: "file_descriptor"})
def dump(conf: dict, file_descriptor: TextIO) -> None:
    """Write a `conf` dict to a file.

    `file_descriptor` can represent a file path or an object with a `write` method.
    """
    conf = InifixConf(conf)
    conf.write(file_descriptor)
