from enum import Enum

from PexpectLibrary.utils.env import get_int_env

PEXPECT_TIMEOUT_FOR_LAUNCH_COMMAND = get_int_env('PEXPECT_TIMEOUT_FOR_LAUNCH_COMMAND', 15)


class SearchModeType(int, Enum):
    HEAD = 0
    TAIL = 1
    MIDDLE = 2
