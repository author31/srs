class SRSException(Exception):
    """
    Generic exception for all external‐service errors.
    Carries a machine‐readable `code` and human `message`.
    """
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")

