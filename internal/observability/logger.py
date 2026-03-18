import sys


class Logger:
    def info(self, message: str) -> None:
        print(message)

    def error(self, message: str) -> None:
        print(message, file=sys.stderr)
