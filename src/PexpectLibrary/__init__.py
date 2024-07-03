from PexpectLibrary.keywords import TerminalInteractionKeywords


class PexpectLibrary(TerminalInteractionKeywords):
    ROBOT_LIBRARY_SCOPE = "GLOBAL"
    ROBOT_LIBRARY_VERSION = __version__

    def __init__(self):
        super().__init__()