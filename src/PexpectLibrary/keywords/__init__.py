import sys
import gc
import re
from typing import List, Union

from pexpect import popen_spawn
from pexpect.exceptions import TIMEOUT as PexpectTimeout
from io import StringIO
from robot.api import logger
from psutil import NoSuchProcess
import psutil
import time

from src.PexpectLibrary.const import PEXPECT_TIMEOUT_FOR_LAUNCH_COMMAND, SearchModeType


class TerminalInteractionKeywords:

    def __init__(self):
        self.main_process: Union[None, popen_spawn.PopenSpawn] = None
        self.sub_process: Union[None, psutil.Process] = None

    @staticmethod
    def _error_handler(func):
        def wrapper(expect_value, timeout, *args, **kwargs):
            try:
                return func(*args, **kwargs)
            except PexpectTimeout:
                raise PexpectTimeout(f"Matching timeout({timeout}).")
            except Exception:
                raise ValueError(f"No matching '{expect_value}'")

        return wrapper

    def __kill_process_for_error(self):
        self.sub_process.kill()
        psutil.Process(self.main_process.pid).kill()
        self.main_process = None
        logger.error("Process kill under unexpected conditions...")

    def run_command(self, *args):
        try:
            logger.info(f"Launching Command: '{' '.join(args)}'...")
            sign_time = time.perf_counter()
            self.main_process = popen_spawn.PopenSpawn(' '.join(args), encoding='utf-8')
            parent_proc = psutil.Process(self.main_process.pid)

            while (time.perf_counter() - sign_time) > PEXPECT_TIMEOUT_FOR_LAUNCH_COMMAND:
                if parent_proc.children(recursive=True):
                    self.sub_process = parent_proc.children(recursive=True)[0]
                    break
            self.main_process.logfile = sys.stdout
        except Exception as error:
            self.__kill_process_for_error()
            self.main_process = None
            raise Exception(f"Launching Command is failure!{error}")

    @_error_handler
    def command_expect(self, *, expect_value: Union[str, List], timeout: int = 0):
        self.main_process.logfile = sys.stdout
        self.main_process.expect(pattern=expect_value, timeout=timeout)

    def command_send(self, send: str):
        try:
            self.main_process.logfile = sys.stdout
            self.main_process.sendline(send)
        except Exception:
            raise TypeError(f"Parameter {send} input error in command send process")

    @_error_handler
    def command_interaction(self, *, expect_value: Union[str, List], send: str, timeout: int = 0):
        if self.main_process is None:
            logger.warn("No process is existed.")
            return
        logger.debug("A process is existed...")
        logger.debug("Starting Interaction Step...")
        self.command_expect(expect_value=expect_value, timeout=timeout)
        self.main_process.sendline(send)

    @_error_handler
    def expect_and_return(
            self, *, expect_value: Union[str, List], reg_exp: str,
            reg_flag: int = re.IGNORECASE, timeout: int = 0,
            **kwargs
    ):
        """


        :param expect_value: expect value in stdout
        :param reg_exp: regex expression with custom, e.g. r"(\d+).*{}.*{}"
        :param reg_flag: regex flag in RegexFlag
        :param timeout: timeout value in expect()
        :param kwargs: str(reg_exp).format(**kwargs)
        :return: according to reg_exp, return the first value in re.findall() -> re.findall()[0]
        """
        output = StringIO()
        old_stdout = sys.stdout
        sys.stdout = output

        self.command_expect(expect_value=expect_value, timeout=timeout)

        value = output.getvalue()
        output.close()
        sys.stdout = old_stdout

        self.main_process.logfile = sys.stdout
        self.main_process.logfile.write(value)
        self.main_process.logfile.flush()

        part = re.compile(pattern=str(reg_exp).format(**kwargs), flags=reg_flag)
        send = part.findall(string=value)

        if send:
            return send[0]

        logger.error(f"Regex expression: {str(reg_exp).format(**kwargs)}; flag: {reg_flag}")
        logger.error(value)
        raise Exception(f"Regex expression can not match in stdout")

    def expect_and_return_for_index(
            self, *, expect_value: Union[str, List], search_mode: int = SearchModeType.HEAD.value,
            reg_flag: int = re.IGNORECASE, timeout: int = 0, point1: str, point2: str
    ):
        """

        :param expect_value:
        :param search_mode:
        :param reg_flag:
        :param timeout:
        :param point1:
        :param point2:
        :return:
        """

        if search_mode == SearchModeType.HEAD.value:
            reg_exp = r"(\d+).*{point1}.*{point2}"
        elif search_mode == SearchModeType.TAIL.value:
            reg_exp = r"{point1}.*{point2}.*(\d+)"
        elif search_mode == SearchModeType.MIDDLE.value:
            reg_exp = r"{point1}.*(\d+).*{point2}"
        else:
            reg_exp = ''

        if not reg_exp:
            raise ValueError("The value of search mode is invalid.")

        index = self.expect_and_return(
            expect_value=expect_value, reg_exp=reg_exp, reg_flag=reg_flag, timeout=timeout,
            pattern1=point1, pattern2=point2
        )
        return index

    def clean_process(self):
        try:
            parent_proc = psutil.Process(self.main_process.pid)
            if not self.main_process:
                for child_proc in parent_proc.children(recursive=True):
                    child_proc.kill()

            psutil.Process(self.main_process.pid).kill()
        except NoSuchProcess:
            logger.debug("This process has been exited.")
        except AttributeError:
            logger.debug("This process has been exited.")
        except Exception as error:
            logger.warn(error)

        gc.collect()
        logger.debug("Cleaning process is completed.")
