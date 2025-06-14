from ..connection.exceptions.execution_statuses import ScriptRunStatusesEnum
from .file_logger import FileLogger
__loop_num__ = 0
__verbosity_lvl__ = 3

logger = FileLogger()

def get_loop_num() -> int:
    global __loop_num__
    return __loop_num__

def inc_loop_num():
    global __loop_num__
    __loop_num__ += 1
    return

def dec_loop_num():
    global __loop_num__
    __loop_num__ -= 1
    return

def set_print_verbosity_lvl(verbosity_lvl: int):
    global __verbosity_lvl__
    __check_verbosity_valid__(verbosity_lvl)
    __verbosity_lvl__ = verbosity_lvl
    return

def is_verbosity_printable(verbosity: int) -> bool:
    global __verbosity_lvl__
    __check_verbosity_valid__(verbosity)
    return __verbosity_lvl__ >= verbosity

def print_loop(text: str, verbosity: int):
    global __loop_num__
    if is_verbosity_printable(verbosity):
        print(f"[LOOP #{__loop_num__}] {text}")
    return

def print_info(text: str, verbosity: int = 1):
    if is_verbosity_printable(verbosity):
        print(f"[INFO] {text}")
    return

def print_error(text: str):
    print(f"[ERROR] {text}")
    return

def print_executable(text: str, verbosity: int = 2):
    if is_verbosity_printable(verbosity):
        print(f"[EXE] {text}")
    return

def print_untagged(text: str, verbosity: int = 1, end="\n"):
    if is_verbosity_printable(verbosity):
        print(text, end=end)
    return

def print_thread_terminated(script:str, func:str):
    print(f"[THREAD] Script {script} is terminated while executing {func}()")
    return

def __check_verbosity_valid__(verbosity: int) -> int:
    if verbosity not in range(3):
        raise ValueError(f"verbosity level {verbosity} is out of range")
    return 0

# PRINT PROGRESS BAR
def timer_bar(iterable, prefix = '', suffix = '', length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create timer bar
    @params:
        iterable    - Required  : iterable object (Iterable)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    total = len(iterable)
    # Progress Bar Printing Function
    def print_timer_bar (iteration):
        time = iteration
        filledLength = int(iteration * length // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print_untagged(f'\r{prefix} |{bar}| {time} sec {suffix}', 0, end = printEnd)
    # Initial Call
    print_timer_bar(total)
    # Update Progress Bar
    for item in iterable:
        yield item
        print_timer_bar(item)
    # Print New Line on Complete
    print_untagged("",0)
    