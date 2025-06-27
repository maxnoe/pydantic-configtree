from pydantic_settings import (
    BaseSettings,
    CliApp,
)

from pydantic_settings_ctapipe.logging import LogConfig


class Settings(BaseSettings):
    pass


class ConfigurableMeta(type):
    def __new__(cls, name, bases, dct):
        config_cls = dct.get("config_cls")

        # only validate concrete implementations, not the Configurable base class
        if len(bases) > 0:
            if config_cls is None:
                raise TypeError(f"Class {name} must define a config_cls")

            if not issubclass(config_cls, BaseSettings):
                raise TypeError(
                    f"{name}.config_cls must be a subclass of {BaseSettings}, got: {config_cls}"
                )

        return super().__new__(cls, name, bases, dct)


class Configurable(metaclass=ConfigurableMeta):
    config_cls = None

    def __init__(self, settings: BaseSettings | None = None):
        if self.config_cls is not None:
            if settings is None:
                settings = self.config_cls()

            elif not isinstance(settings, self.config_cls):
                raise TypeError(
                    f"Expected an instance of {self.config_cls!r}, got {settings!r}"
                )

        self.settings = settings


class SubConfig(Settings):
    option: int = 1


class Sub(Configurable):
    config_cls = SubConfig

    def do_something(self):
        if self.settings.option == 1:
            print("option is 1")
        else:
            print("option is != 1")


class CompConfig(Settings):
    sub: SubConfig = SubConfig()
    foo: str = "bar"


class Comp(Configurable):
    config_cls = CompConfig

    def __init__(self, settings: "CompConfig | None" = None):
        super().__init__(settings=settings)
        self.sub = Sub(settings=self.settings.sub)

    def do_something(self):
        print(self.sub.do_something())


class Tool(BaseSettings):
    log_config: LogConfig = LogConfig()


class App(Tool):
    comp: CompConfig = CompConfig()

    def cli_cmd(self) -> None:
        print(self.model_dump())

        comp = Comp(self.comp)
        comp.do_something()


def main():
    CliApp.run(App)


if __name__ == "__main__":
    main()
