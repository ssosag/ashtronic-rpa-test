class BotError(Exception):
    """Base class for all RPA bot errors. Carries the step name for traceability."""

    def __init__(self, message: str, step: str = "unknown"):
        super().__init__(message)
        self.message = message
        self.step = step

    def __str__(self) -> str:
        return f"[{self.step}] {self.message}"


class LoginError(BotError):
    def __init__(self, message: str):
        super().__init__(message, step="login")


class InvalidCredentialsError(LoginError):
    """Structural login failure — not retryable (portal reached /login still after submit)."""


class NavigationError(BotError):
    def __init__(self, message: str):
        super().__init__(message, step="navigate")


class FilterError(BotError):
    def __init__(self, message: str):
        super().__init__(message, step="filters")


class ExtractError(BotError):
    def __init__(self, message: str):
        super().__init__(message, step="extract")
