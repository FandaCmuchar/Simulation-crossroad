from simpy import Environment
from simpy.rt import RealtimeEnvironment

class Entity:
    counter: int = 0

    def __init__(self, env: Environment | RealtimeEnvironment) -> None:
        self.__class__.counter += 1
        self.id: int = self.__class__.counter
        self.env: Environment | RealtimeEnvironment = env
        self.env.process(self.lifetime())

    def log(self, text: str) -> None:
        self.env.log(text, self)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}:{self.id:02d}"

    def lifetime(self) -> None:
        raise NotImplementedError("abstract method")

class Logger:
    """Handles logging functionality.

    Attributes:
        logEnabled (bool): Flag to control logging. Default is True.
    """

    def __init__(self, logEnabled: bool = True) -> None:
        """Initialize the Logger.

        Parameters:
            logEnabled (bool): Flag to control logging. Default is True.
        """
        self.logEnabled: bool = logEnabled

    def log_off(self) -> None:
        """Turn off logging."""
        self.logEnabled = False

    def log_on(self) -> None:
        """Turn on logging."""
        self.logEnabled = True

    def log(self, text: str, entity: Entity = None) -> None:
        """Print log messages.

        Parameters:
            text (str): The log message text.
            entity: An optional entity associated with the log message.
        """
        if self.logEnabled:
            print(f"{self.now:8.3f} {f'({entity})' if entity is not None else ''}  {text}")
