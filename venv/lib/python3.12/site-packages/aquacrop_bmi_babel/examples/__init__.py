import json
from pathlib import Path
from typing import Any



def load_example(name: str) -> Any:
    path = Path(__file__).parent.joinpath(name + '.json')
    with path.open(encoding='utf-8') as rdr:
        return json.load(rdr)
