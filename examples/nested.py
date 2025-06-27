from pydantic_settings import (
    BaseSettings,
    CliApp,
)

from pydantic_settings_ctapipe import Configurable
from pydantic_settings_ctapipe.logging import LogConfig


class Settings(BaseSettings):
    pass


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
        self.sub.do_something()


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
