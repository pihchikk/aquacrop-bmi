import os
from importlib.resources import files



_NAME = 'aquacrop.exe' if os.name == 'nt' else 'aquacrop'
AQUACROP_EXE = str(files(__package__).joinpath(_NAME))
