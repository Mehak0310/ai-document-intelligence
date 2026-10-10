class AppError(Exception):
    """Only explicitly safe messages may cross the API boundary."""
    def __init__(self, message, status=422):
        super().__init__(message)
        self.status = status
