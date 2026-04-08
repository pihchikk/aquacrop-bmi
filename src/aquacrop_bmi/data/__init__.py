from enum import Enum
from pathlib import Path

from ..util import CropData, loads_crop_file



DEFAULT_DATA_DIR = Path(__file__).parent.joinpath('default')


class CropRef(Enum):
    Barley = 'Barley'
    Canola = 'Canola'
    Maize = 'Maize'
    Oat = 'Oat'
    Potato = 'Potato'
    Soybean = 'Soybean'
    SugarBeet = 'SugarBeet'
    Sunflower = 'Sunflower'
    Tomato = 'Tomato'
    Wheat = 'Wheat'



def get_crop_params(ref: CropRef) -> CropData:
    crop_name, index, params = _CROPS[ref]
    return crop_name, index, params.copy()



_CROPS = {
    CropRef(p.stem): loads_crop_file(p.read_text())
    for p in Path(__file__).parent.glob('crops/*.CRO')
}
