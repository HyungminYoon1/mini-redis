class RespError(Exception):
    pass


class IncompleteRespError(RespError):
    pass


class RespProtocolError(RespError):
    pass
