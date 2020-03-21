class CLogException(Exception):
    ...


class InvalidSite(ValueError):
    ...


class MissingContent(ValueError):
    ...


class GitException(CLogException):
    ...


class GitPermissionDenied(GitException):
    ...
