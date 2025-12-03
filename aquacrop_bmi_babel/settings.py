from multiprocessing import cpu_count
from typing import Annotated

from pydantic import AnyHttpUrl, Field, PositiveInt
from pydantic_settings import BaseSettings



def _default_max_workers():
    return int(cpu_count() * 0.75) or 1



class Settings(BaseSettings):
    model_config = {
        'env_file': ('.env', ),
        'extra': 'ignore',
    }

    max_workers: Annotated[PositiveInt, Field(default_factory=_default_max_workers)]
    open_elevation_url: AnyHttpUrl = AnyHttpUrl('https://api.open-elevation.com/api/v1/lookup')
    rosetta_url: AnyHttpUrl = AnyHttpUrl('http://www.handbook60.org/api/v1/rosetta/3')



settings = Settings()
