class CommandError(Exception):
    pass


class CommandValidationError(CommandError):
    pass


class CommandExecutionError(CommandError):
    pass
