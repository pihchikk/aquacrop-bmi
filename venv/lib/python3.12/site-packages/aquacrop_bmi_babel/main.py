from anyio.to_thread import run_sync
from fastapi import FastAPI

import sync
from .models import (
    CropCalibrationInput,
    CropCalibrationResult,
    FertilityStressCalibrationInput,
    FertilityStressCalibrationResult,
    ScenariosSimulationInput,
    ScenariosSimulationResult,
)



app = FastAPI()



@app.post(
    path='/crop-calibration',
    description='Калибровка параметров культуры',
    response_model=CropCalibrationResult,
)
async def run_crop_calibration(
    data: CropCalibrationInput,
):
    return await run_sync(sync.run_crop_calibration, data)



@app.post(
    path='/fertility-stress-calibration',
    description='Калибровка стресса минерального питания',
    response_model=FertilityStressCalibrationResult,
)
async def run_fertility_stress_calibration(
    data: FertilityStressCalibrationInput,
):
    return await run_sync(sync.run_fertility_stress_calibration, data)



@app.post(
    path='/scenarios-simulation',
    description='Моделирование сценариев для почвы и климатических условий',
    response_model=ScenariosSimulationResult,
)
async def run_scenarios_simulation(
    data: ScenariosSimulationInput,
):
    return await run_sync(sync.run_scenarios_simulation, data)