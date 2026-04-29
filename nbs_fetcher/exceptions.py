class NBSFetcherError(Exception):
    """Base exception for nbs_fetcher."""


class PageNotFoundError(NBSFetcherError):
    pass


class PathNotFoundError(NBSFetcherError):
    pass


class IndicatorNotFoundError(NBSFetcherError):
    pass


class AreaNotFoundError(NBSFetcherError):
    pass


class NBSRequestError(NBSFetcherError):
    pass


class NBSChallengeError(NBSRequestError):
    pass
