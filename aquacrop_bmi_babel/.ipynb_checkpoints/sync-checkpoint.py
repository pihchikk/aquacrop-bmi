from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from io import StringIO
from itertools import product, repeat
from typing import TYPE_CHECKING

import numpy as np
from SALib.sample import sobol

from .data_modules import get_crop_params, specs
from .models import (
    CalibrationSeason,
    CropCalibrationInput,
    CropCalibrationResult,
    FertilityStressCalibrationInput,
    FertilityStressCalibrationResult,
    Point,
    Point3D,
    ScenariosSimulationInput,
    ScenariosSimulationResult,
    Season,
    SoilLayer,
)
from .project import AquacropProject, dump_crop_file
from .settings import settings
from .soil_texture import get_soil_params
from .util import get_elevation, get_weather_data, loads_crop_file



if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from numpy.typing import NDArray



CALIBRATED_PARAMETERS = (
    'Soil water depletion factor for canopy expansion (p-exp) - Upper threshold',
    'Soil water depletion factor for canopy expansion (p-exp) - Lower threshold',
    'Shape factor for water stress coefficient for canopy expansion (0.0 = straight line)',
    'Soil water depletion fraction for stomatal control (p - sto) - Upper threshold',
    'Shape factor for water stress coefficient for stomatal control (0.0 = straight line)',
    'Soil water depletion factor for canopy senescence (p - sen) - Upper threshold',
    'Shape factor for water stress coefficient for canopy senescence (0.0 = straight line)',
    'Soil water depletion factor for pollination (p - pol) - Upper threshold',
    'Vol% for Anaerobiotic point (* (SAT - [vol%]) at which deficient aeration occurs *)',
    'Canopy growth coefficient (CGC): Increase in canopy cover (fraction soil cover per day)',
    'Canopy decline coefficient (CDC): Decrease in canopy cover (in fraction per day)',
    'Reference Harvest Index (HIo) (%)',
    'Water Productivity normalized for ETo and CO2 (WP*) (gram/m2)',
)

CALIBRATED_PARAMETERS_WITH_STRESS = (
    'Response of canopy expansion is not considered',
)

logging.getLogger('uvicorn.asgi').info('Starting %i task thread(s)', settings.max_workers)
POOL = ThreadPoolExecutor(settings.max_workers)



def run_crop_calibration(data: CropCalibrationInput) -> CropCalibrationResult:
    crop_name, crop_index, crop_params = get_crop_params(data.crop_ref)
    crop_params.update(data.crop_params.model_dump(by_alias=True, exclude_none=True))
    samples = _sample_crop_params(crop_params, data)
    _, best_error, crop_file = _run_calibration(
        data, CALIBRATED_PARAMETERS, crop_name, crop_index, crop_params, samples)

    return CropCalibrationResult(
        crop_params=crop_params,
        error=best_error,
        crop_file=crop_file,
    )



def run_fertility_stress_calibration(
    data: FertilityStressCalibrationInput,
) -> FertilityStressCalibrationResult:
    crop_name, crop_index, crop_params = loads_crop_file(data.crop_file)
    samples, stress_samples = _sample_crop_params_with_stress(crop_params, data)
    best_num, best_error, crop_file = _run_calibration(
        data, CALIBRATED_PARAMETERS_WITH_STRESS, crop_name, crop_index, crop_params,
        samples, stress_samples)

    return FertilityStressCalibrationResult(
        crop_params=crop_params,
        error=best_error,
        crop_file=crop_file,
        fertility_stress=round(stress_samples[best_num]),
    )



def run_scenarios_simulation(data: ScenariosSimulationInput) -> ScenariosSimulationResult:
    _, crop_index, crop_params = loads_crop_file(data.crop_file)
    weather_data = POOL.map(_point_weather_data_getter_factory(data.point), data.seasons)

    with AquacropProject(with_default=False) as project:
        project.write_crop_file(crop_index, crop_params)
        project.write_fertility_management_file(data.fertility_stress)
        project.write_gwt_file(depth=data.gwt_depth, ec=data.gwt_ec)
        project.write_daily_out_config()

        worker = partial(_simulation_scenarios_worker, project.root)
        args = product(data.soils, zip(data.seasons, weather_data, strict=True))
        item_iter = POOL.map(worker, args)
        items = [
            [next(item_iter) for _ in data.seasons]
            for _ in data.soils
        ]

    return ScenariosSimulationResult(
        header=specs.DAILY_OUT_HEADER,
        items=items,
    )



def _run_calibration(
    data: CropCalibrationInput | FertilityStressCalibrationInput,
    calibrated_params: tuple[str, ...],
    crop_name: str,
    crop_index: tuple[str, ...],
    crop_params: dict[str, int | float],
    samples: NDArray,
    stress_samples: Iterable[float] = repeat(0.0),
) -> tuple[np.intp, np.float64, str]:
    soil = get_soil_params(data.soil)
    sample_count = samples.shape[0]
    season_count = len(data.seasons)

    date_start = min(s.simulation_start for s in data.seasons)
    date_end = max(s.simulation_end for s in data.seasons)
    point = _normalize_point(data.point)
    weather_data = get_weather_data(
        point.latitude,
        point.longitude,
        point.altitude,
        date_start,
        date_end,
    )

    with AquacropProject(with_default=False) as project:
        project.write_climate_files(date_start, weather_data)
        project.write_soil_file(soil)
        project.write_sw0_file(soil)
        project.write_gwt_file(depth=data.gwt_depth, ec=data.gwt_ec)

        worker = partial(_calibration_worker, project.root, calibrated_params, crop_index)
        args = (
            (crop_params.copy(), a[0], *(a[1]))
            for a in product(data.seasons, zip(samples, stress_samples, strict=False)))

        error_iter = POOL.map(worker, args)
        errors: NDArray[np.float64] = (np
            .fromiter(error_iter, np.float64, season_count * sample_count)
            .reshape((season_count, sample_count))
            .mean(axis=0))

    best_num = errors.argmin()
    best_error = errors[best_num]

    crop_params.update(zip(calibrated_params, samples[best_num], strict=True))

    with StringIO() as buffer:
        dump_crop_file(buffer, crop_index, crop_params, crop_name)
        crop_file = buffer.getvalue()

    return best_num, best_error, crop_file



def _calibration_worker(
    parent: Path,
    calibrated_params: tuple[str, ...],
    crop_index: tuple[str, ...],
    args: tuple[dict[str, int | float], CalibrationSeason, NDArray, float],
) -> float:
    crop_params, season, sample, stress = args
    with AquacropProject(parent) as project:
        project.write_calendar_file(season)
        project.write_project_file(season)
        project.write_fertility_management_file(stress)
        for key, val in zip(calibrated_params, sample, strict=True):
            crop_params[key] = val
        project.write_crop_file(crop_index, crop_params)
        project.run_aquacrop()
        yield_simulated = project.read_final_yield()
        return abs(season.yield_ - yield_simulated)



def _simulation_scenarios_worker(
    parent: Path,
    args: tuple[list[SoilLayer], tuple[Season, np.recarray]],
):
    soil_layer, (season, weather_data) = args
    with AquacropProject(parent) as project:
        soil = get_soil_params(soil_layer)
        project.write_soil_file(soil)
        project.write_sw0_file(soil)
        project.write_climate_files(season.simulation_start, weather_data)
        project.write_calendar_file(season)
        project.write_project_file(season)
        project.run_aquacrop()
        return project.read_daily_out()



def _sample_crop_params(
    crop_params: dict[str, int | float],
    data: CropCalibrationInput,
) -> NDArray[np.floating]:
    bounds = list(_crop_params_bounds(CALIBRATED_PARAMETERS, crop_params, data.sampling_range))
    return sobol.sample(
        {
            'num_vars': len(CALIBRATED_PARAMETERS),
            'names': CALIBRATED_PARAMETERS,
            'bounds': bounds,
        },
        data.sample_size,
    )



def _sample_crop_params_with_stress(
    crop_params: dict[str, int | float],
    data: FertilityStressCalibrationInput,
) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
    bounds = list(
        _crop_params_bounds(CALIBRATED_PARAMETERS_WITH_STRESS, crop_params, data.sampling_range))
    bounds.append(tuple(data.fertility_stress_range))

    names = [*CALIBRATED_PARAMETERS_WITH_STRESS, 'fertility_stress']
    samples = sobol.sample(
        {
            'num_vars': len(names),
            'names': names,
            'bounds': bounds,
        },
        data.sample_size,
    )

    #      samples,        stress_samples
    return samples[:,:-1], samples[:,-1]



def _crop_params_bounds(
    calibrated_params: tuple[str, ...],
    crop_params: dict[str, int | float],
    sampling_range: float,
):
    sampling_range /= 100.0
    for name in calibrated_params:
        value = crop_params[name]
        yield (
            value - (value * sampling_range),
            value + (value * sampling_range),
        )



def _normalize_point(point: Point | Point3D):
    if isinstance(point, Point3D):
        return point

    latitude = point.latitude
    longitude = point.longitude
    altitude = get_elevation(latitude, longitude)

    return Point3D(latitude=latitude, longitude=longitude, altitude=altitude)



def _point_weather_data_getter_factory(point: Point | Point3D):
    p = _normalize_point(point)
    lat = p.latitude
    lon = p.longitude
    alt = p.altitude
    def impl(season: Season):
        return get_weather_data(lat, lon, alt, season.simulation_start, season.simulation_end)
    return impl