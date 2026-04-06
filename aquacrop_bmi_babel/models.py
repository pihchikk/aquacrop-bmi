from datetime import date
from typing import Annotated, Any, Self

from annotated_types import Interval
from pydantic import (
    BaseModel,
    Discriminator,
    Field,
    NonNegativeFloat,
    PositiveInt,
    Tag,
    field_validator,
    model_validator,
)

from .data_modules import CropRef
from .examples import load_example



IntPercent = Annotated[int, Interval(ge=0, le=100)]



class Point(BaseModel):
    latitude: float
    longitude: float



class Point3D(Point):
    altitude: float



class CropFileMixin(BaseModel):
    crop_file: Annotated[
        str,
        Field(description='Откалиброванные параметры культуры в формате Aquacrop CRO'),
    ]



class Season(BaseModel):
    simulation_start: date
    simulation_end: date
    growing_season_start: date
    growing_season_end: date

    @model_validator(mode='after')
    def check_date_order(self) -> Self:
        errors = []
        if self.simulation_end <= self.simulation_start:
            errors.append(
                f"simulation_end ({self.simulation_end}) must be after "
                f"simulation_start ({self.simulation_start})"
            )
        if self.growing_season_end <= self.growing_season_start:
            errors.append(
                f"growing_season_end ({self.growing_season_end}) must be after "
                f"growing_season_start ({self.growing_season_start})"
            )
        if errors:
            raise ValueError('; '.join(errors))
        return self



class CalibrationSeason(Season):
    yield_: Annotated[
        NonNegativeFloat,
        Field(alias='yield', description='Фактический урожай'),
    ]



class SoilLayerBase(BaseModel):
    """Почвенный горизонт."""

    thickness: float
    penetrability: float
    gravel: float
    wc: float
    ec: float



class SoilLayerWithConstants(SoilLayerBase):
    sat: float
    fc: float
    wp: float
    ksat: float



class SoilLayerWithTexture(SoilLayerBase):
    clay: float
    silt: float
    sand: float


    @model_validator(mode='after')
    def check_sum(self) -> Self:
        total = round(self.clay + self.silt + self.sand, 4)

        if total == 100.0:
            return self

        msg = f'The sum of clay, silt, and sand must be strictly equal to 100%, got {total}'
        raise ValueError(msg)



def _get_soil_discriminator_value(v: Any):
    if isinstance(v, dict):
        return 'const' if 'sat' in v else 'text'
    return 'const' if hasattr(v, 'sat') else 'text'



SoilLayer = Annotated[
    Annotated[SoilLayerWithConstants, Tag('const')]
    | Annotated[SoilLayerWithTexture, Tag('text')],
    Discriminator(_get_soil_discriminator_value),
]



class CropParams(BaseModel):
    plants_number: Annotated[
        int | None,
        Field(serialization_alias='Number of plants per hectare'),
    ] = None
    emergence_day: Annotated[
        int | None,
        Field(serialization_alias='Calendar Days: from sowing to emergence'),
    ] = None
    maximum_rooting_depth_day: Annotated[
        int | None,
        Field(serialization_alias='Calendar Days: from sowing to maximum rooting depth'),
    ] = None
    start_senescence_day: Annotated[
        int | None,
        Field(serialization_alias='Calendar Days: from sowing to start senescence'),
    ] = None
    maturity_day: Annotated[
        int | None,
        Field(serialization_alias='Calendar Days: from sowing to maturity (length of crop cycle)'),
    ] = None
    flowering_day: Annotated[
        int | None,
        Field(serialization_alias='Calendar Days: from sowing to flowering'),
    ] = None
    flowering_stage_days: Annotated[
        int | None,
        Field(serialization_alias='Length of the flowering stage (days)'),
    ] = None
    harvest_index: Annotated[
        int | None,
        Field(serialization_alias='Building up of Harvest Index starting at flowering (days)'),
    ] = None
    minimum_effective_rooting_depth: Annotated[
        float | None,
        Field(serialization_alias='Minimum effective rooting depth (m)'),
    ] = None
    maximum_effective_rooting_depth: Annotated[
        float | None,
        Field(serialization_alias='Maximum effective rooting depth (m)'),
    ] = None



class CropOverrides(BaseModel):
    """Optional crop parameter overrides applied on top of the base CRO file.

    Every field is optional — only provided values override the CRO defaults.
    Field names are short Python names; ``serialization_alias`` holds the
    exact CRO key used internally by ``loads_crop_file`` / ``dump_crop_file``.
    """

    # ── Phenology (calendar days) ───────────────────────────────────
    emergence_day: Annotated[
        int | None,
        Field(serialization_alias='Calendar Days: from sowing to emergence'),
    ] = None
    max_rooting_day: Annotated[
        int | None,
        Field(serialization_alias='Calendar Days: from sowing to maximum rooting depth'),
    ] = None
    senescence_day: Annotated[
        int | None,
        Field(serialization_alias='Calendar Days: from sowing to start senescence'),
    ] = None
    maturity_day: Annotated[
        int | None,
        Field(serialization_alias='Calendar Days: from sowing to maturity (length of crop cycle)'),
    ] = None
    flowering_day: Annotated[
        int | None,
        Field(serialization_alias='Calendar Days: from sowing to flowering'),
    ] = None
    flowering_duration: Annotated[
        int | None,
        Field(serialization_alias='Length of the flowering stage (days)'),
    ] = None
    hi_duration: Annotated[
        int | None,
        Field(serialization_alias='Building up of Harvest Index starting at flowering (days)'),
    ] = None

    # ── Canopy ──────────────────────────────────────────────────────
    plants_per_hectare: Annotated[
        int | None,
        Field(serialization_alias='Number of plants per hectare'),
    ] = None
    ccx: Annotated[
        float | None,
        Field(
            serialization_alias='Maximum canopy cover (CCx) in fraction soil cover',
            gt=0, le=1,
        ),
    ] = None
    cgc: Annotated[
        float | None,
        Field(
            serialization_alias='Canopy growth coefficient (CGC): Increase in canopy cover (fraction soil cover per day)',
            gt=0,
        ),
    ] = None
    cdc: Annotated[
        float | None,
        Field(
            serialization_alias='Canopy decline coefficient (CDC): Decrease in canopy cover (in fraction per day)',
            gt=0,
        ),
    ] = None
    seedling_size: Annotated[
        float | None,
        Field(serialization_alias='Soil surface covered by an individual seedling at 90 % emergence (cm2)'),
    ] = None

    # ── Rooting ─────────────────────────────────────────────────────
    root_min: Annotated[
        float | None,
        Field(
            serialization_alias='Minimum effective rooting depth (m)',
            gt=0,
        ),
    ] = None
    root_max: Annotated[
        float | None,
        Field(
            serialization_alias='Maximum effective rooting depth (m)',
            gt=0,
        ),
    ] = None

    # ── Yield ───────────────────────────────────────────────────────
    harvest_index: Annotated[
        int | None,
        Field(
            serialization_alias='Reference Harvest Index (HIo) (%)',
            gt=0, le=100,
        ),
    ] = None
    wp_star: Annotated[
        float | None,
        Field(
            serialization_alias='Water Productivity normalized for ETo and CO2 (WP*) (gram/m2)',
            gt=0,
        ),
    ] = None

    # ── Temperature ─────────────────────────────────────────────────
    base_temp: Annotated[
        float | None,
        Field(serialization_alias='Base temperature (°C) below which crop development does not progress'),
    ] = None
    upper_temp: Annotated[
        float | None,
        Field(serialization_alias='Upper temperature (°C) above which crop development no longer increases with an increase in temperature'),
    ] = None
    pollination_cold: Annotated[
        int | None,
        Field(serialization_alias='Minimum air temperature below which pollination starts to fail (cold stress) (°C)'),
    ] = None
    pollination_heat: Annotated[
        int | None,
        Field(serialization_alias='Maximum air temperature above which pollination starts to fail (heat stress) (°C)'),
    ] = None

    # ── Water stress ────────────────────────────────────────────────
    kc_max: Annotated[
        float | None,
        Field(
            serialization_alias='Crop coefficient when canopy is complete but prior to senescence (KcTr,x)',
            gt=0,
        ),
    ] = None
    fertility_stress: Annotated[
        int | None,
        Field(
            serialization_alias='Considered soil fertility stress for calibration of stress response (%)',
            ge=0, le=100,
        ),
    ] = None

    def to_cro_overrides(self) -> dict[str, int | float]:
        """Return {CRO_key: value} for non-None fields only."""
        return {
            field.alias: getattr(self, name)
            for name, field in self.model_fields.items()
            if (alias := field.alias) and getattr(self, name) is not None
        }



class InputBase(BaseModel):
    gwt_depth: Annotated[float, Field(description='Уровень грунтовых вод, м')]
    gwt_ec: Annotated[float, Field(description='Электропроводность грунтовых вод')]
    point: Point | Point3D



class CalibrationInputBase(InputBase):
    sample_size: Annotated[
        PositiveInt,
        Field(description='Число генерируемых значений для каждого калибруемого параметра'),
    ] = 8
    sampling_range: Annotated[
        float,
        Field(
            gt=0.0,
            le=100.0,
            description='Процент отклонения генерируемых значений параметров от табличных',
        ),
    ]
    seasons: list[CalibrationSeason]
    soil: list[SoilLayer]


    @field_validator('sample_size', mode='after')
    @classmethod
    def validate_sampling_range(cls, value: int) -> int:
        if value & value - 1 != 0:
            msg = '`sample_size` must be a power of 2'
            raise ValueError(msg)
        return value



class CropCalibrationInput(CalibrationInputBase):
    model_config = {
        'json_schema_extra': {
            'examples': [load_example('crop-calibration')],
        },
    }

    crop_ref: CropRef
    crop_params: Annotated[
        CropParams,
        Field(
            description='Параметры культуры для уточнения табличных значений',
            default_factory=CropParams,
        ),
    ]



class FertilityStressCalibrationInput(CropFileMixin, CalibrationInputBase):
    model_config = {
        'json_schema_extra': {
            'examples': [load_example('fertility-stress-calibration')],
        },
    }

    fertility_stress_range: Annotated[
        list[IntPercent],
        Field(
            min_length=2,
            max_length=2,
            description='Границы генерируемых значений стресса минерального питания (%)',
        ),
    ] = [1, 75]



class ScenariosSimulationInput(CropFileMixin, InputBase):
    model_config = {
        'json_schema_extra': {
            'examples': [load_example('scenarios-simulation')],
        },
    }

    seasons: list[Season]
    soils: list[list[SoilLayer]]
    fertility_stress: Annotated[
        IntPercent,
        Field(description='Стресс минерального питания (%)'),
    ]
    crop_params: Annotated[
        CropOverrides | None,
        Field(
            default=None,
            description='Опциональные переопределения параметров культуры (поверх crop_file)',
        ),
    ]



class CropCalibrationResult(CropFileMixin):
    crop_params: Annotated[
        dict[str, int | float],
        Field(description='Откалиброванные параметры культуры'),
    ]
    error: Annotated[float, Field(description='Средняя ошибка реального и смоделированного урожая')]



class FertilityStressCalibrationResult(CropCalibrationResult):
    fertility_stress: Annotated[
        IntPercent | None,
        Field(description='Стресс минерального питания (%)'),
    ]



class ScenariosSimulationResult(BaseModel):
    header: list[str]
    items: Annotated[
        list[list[list[tuple[date | int | float, ...]]]],
        Field(description='Почва -> Сезон -> Дата'),
    ]