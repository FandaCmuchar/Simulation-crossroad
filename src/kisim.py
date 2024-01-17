import simpy


class Logger():
    def __init__(self, logEnabled = True):
        self.logEnabled = logEnabled

    def log_off(self):
        self.logEnabled = False

    def log_on(self):
        self.logEnabled = True

    def log(self, text, entity = None):
        if self.logEnabled:
            print(f"{self.now:8.3f}: {text}\t{f'({entity})' if entity is not None else ''}")


class Environment(simpy.Environment):
    def __init__(self, logEnabled=True):
        super().__init__()
        self.logEnabled = logEnabled

    def log_off(self):
        self.logEnabled = False

    def log_on(self):
        self.logEnabled = True

    def log(self, text, entity = None):
        if self.logEnabled:
            print(f"{self.now:8.1f}: {text}\t {f'({entity})' if entity is not None else ''}")


class Entity:
    counter = 0

    def __init__(self, env):
        self.__class__.counter += 1
        self.id = self.__class__.counter
        self.env = env
        self.env.process(self.lifetime())

    def log(self, text):
        self.env.log(text, self)

    def __str__(self):
        return f"{self.__class__.__name__}:{self.id}"

    def lifetime(self):
        raise NotImplemented("abstract method")


class Collector(Entity):
    def __init__(self, env, interval):
        super().__init__(env)
        self.interval = interval
        self.times = []

    def lifetime(self):
        while True:
            self.times.append(self.env.now)
            self.collect()
            yield self.env.timeout(self.interval)

    def collect(self):
        raise NotImplemented("abstract method")
