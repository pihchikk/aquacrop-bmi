from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np
from soiltexture.texture import tables as soiltexture_tables

from models import SoilLayer, SoilLayerWithConstants, SoilLayerWithTexture
from util import ask_rosetta



if TYPE_CHECKING:
    from collections.abc import Callable

    from matplotlib.path import Path as MplPath



WILTING_POINT = 15_295.7



class SoilTextureClass(Enum):
    Sandy = 1
    Loamy = 2
    SandyClayey = 3
    SiltyClayey = 4


    @staticmethod
    def from_constants(sat: float, fc: float, wp: float, ksat: float) -> SoilTextureClass:
        if wp >= 20:
            if sat > 49 and fc >= 40:
                return SoilTextureClass.SiltyClayey
            return SoilTextureClass.SandyClayey
        if fc < 23:
            return SoilTextureClass.Sandy
        if wp > 16 and ksat < 100:
            return SoilTextureClass.SandyClayey
        if wp < 6 and fc < 28 and ksat > 750:
            return SoilTextureClass.Sandy
        return SoilTextureClass.Loamy


    @staticmethod
    def from_texture(sand: float, clay: float) -> SoilTextureClass:
        try:
            cls_ = next(c for c, p in _USDA_SOIL_TEXTURES if p.contains_point((sand, clay)))
        except StopIteration as exc:
            raise NotImplementedError from exc
        else:
            match cls_:
                case 'sand' | 'loamy sand' | 'sandy loam':
                    return SoilTextureClass.Sandy
                case 'loam' | 'silt loam' | 'silt':
                    return SoilTextureClass.Loamy
                case 'sandy clay' | 'sandy clay loam' | 'clay loam':
                    return SoilTextureClass.SandyClayey
                case 'silty clay loam' | 'silty clay' | 'clay':
                    return SoilTextureClass.SiltyClayey
                case _:
                    raise NotImplementedError


    def field_moisture_capacity(self) -> float:
        if self in {SoilTextureClass.Sandy, SoilTextureClass.Loamy}:
            return 101.972
        return 305.915



@dataclass
class SoilLayerParams:
    thickness: float
    sat: float
    fc: float
    wp: float
    ksat: float
    penetrability: float
    gravel: float
    cr_a: float
    cr_b: float
    wc: float
    ec: float
    texture_class: SoilTextureClass



def get_soil_params(layers: list[SoilLayer]) -> list[SoilLayerParams]:
    res: list[SoilLayerParams] = []
    with_texture_ind: list[int] = []
    soildata: list[tuple[float, float, float]] = []
    for ind, layer in enumerate(layers):
        if isinstance(layer, SoilLayerWithConstants):
            sat = layer.sat
            fc = layer.fc
            wp = layer.wp
            ksat = layer.ksat
            texture_class = SoilTextureClass.from_constants(sat, fc, wp, ksat)
            cr_a, cr_b = _CAPILLARY_RISE_EQUATIONS[texture_class](ksat)
            res.append(SoilLayerParams(
                layer.thickness, sat, fc, wp, ksat, layer.penetrability, layer.gravel, cr_a, cr_b,
                layer.wc, layer.ec, texture_class))
        elif isinstance(layer, SoilLayerWithTexture):
            with_texture_ind.append(ind)
            soildata.append((layer.sand, layer.silt, layer.clay))
            res.append(SoilLayerParams(
                layer.thickness, 0, 0, 0, 0, layer.penetrability, layer.gravel, 0, 0,
                layer.wc, layer.ec, SoilTextureClass.Sandy))
        else:
            raise NotImplementedError

    if not soildata:
        return res

    van_genuchten_params = ask_rosetta(soildata)

    for (
        ind,
        (sand, _silt, clay),
        (th_r, sat, log10alpha, log10npar, log10ksat),
    ) in zip(with_texture_ind, soildata, van_genuchten_params, strict=True):
        alpha: float = 10.0 ** log10alpha
        npar: float = 10.0 ** log10npar
        ksat = 10.0 ** log10ksat
        texture_class = SoilTextureClass.from_texture(sand, clay)
        h_fc = texture_class.field_moisture_capacity()
        params = res[ind]
        params.sat = sat * 100.0
        params.ksat = ksat
        params.fc = _van_genuchten(th_r, sat, alpha, h_fc, npar) * 100.0
        params.wp = _van_genuchten(th_r, sat, alpha, WILTING_POINT, npar) * 100.0
        params.texture_class = texture_class

    return res



def rew_calc(
    fc: float,
    air: float,
    ze: float = 0.04,
) -> float:
    rew = round(1000 * (fc / 100 - air / 100) * ze)
    if rew < 0:
        return 0
    if rew > 15:
        return 15
    return rew



def curve_number_calc(ksat: float) -> int:
    if ksat > 864:
        return 46
    if ksat >= 347:
        return 61
    if 36 <= ksat <= 346:
        return 72

    return 77



_USDA_SOIL_TEXTURES: list[tuple[str, MplPath]] = list(soiltexture_tables['USDA'].items())

_CAPILLARY_RISE_EQUATIONS: dict[SoilTextureClass, Callable[[float], tuple[float, float]]] = {
    SoilTextureClass.Sandy: lambda ksat: (
        -0.3112 - ksat / 100000,
        -1.4936 + 0.2416 * np.log(ksat),
    ),
    SoilTextureClass.Loamy: lambda ksat: (
        -0.4986 + 9 * ksat / 100000,
        -2.1320 + 0.4778 * np.log(ksat),
    ),
    SoilTextureClass.SandyClayey: lambda ksat: (
        -3.7189 + 0.5922 * np.log(ksat),
        -3.7189 + 0.5922 * np.log(ksat),
    ),
    SoilTextureClass.SiltyClayey: lambda ksat: (
        -0.6366 + 8 * ksat / 10000,
        -1.9165 + 0.7063 * np.log(ksat),
    ),
}



def _van_genuchten(
    th_r: float,
    th_s: float,
    alpha: float,
    h: float,
    npar: float,
) -> float:
    m = 1.0 - 1.0 / npar
    return th_r + (th_s - th_r) / ((1.0 + (alpha * h)**npar)**m)
