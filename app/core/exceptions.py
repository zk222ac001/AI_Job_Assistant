class NotFoundError(Exception):
    """Raised when a requested domain object cannot be found."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)
