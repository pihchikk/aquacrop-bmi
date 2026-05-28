"""
Pre-Fortran input validation for AquaCrop BMI.

AquaCrop's Fortran core uses int8 variables (max 127), fixed-size arrays
(max 5 soil layers), and unprotected file reads. Invalid inputs cause
segfaults, integer overflows, or cryptic Fortran runtime errors instead
of useful messages. This module catches those issues on the Python side.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Season, SoilLayerWithConstants, SoilLayerWithTexture
    from .soil_texture import SoilLayerParams


# ── Fortran limits ──────────────────────────────────────────────────
MAX_SOIL_LAYERS = 10         # global.f90:21  max_SoilLayers
MAX_COMPARTMENTS = 12        # global.f90:22  max_No_compartments
INT8_MIN = -128
INT8_MAX = 127


class AquaCropValidationError(ValueError):
    """Raised when input parameters would crash the Fortran core."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        bullet_list = "\n".join(f"  - {e}" for e in errors)
        super().__init__(
            f"AquaCrop input validation failed ({len(errors)} error(s)):\n"
            f"{bullet_list}"
        )


# ── Public API ──────────────────────────────────────────────────────

def validate_soil_layers(
    layers: list[SoilLayerWithConstants | SoilLayerWithTexture | SoilLayerParams],
) -> None:
    """Validate soil layers against Fortran constraints.

    Checks performed (references to global.f90):
    - Number of layers: 1..5  (max_SoilLayers, line 21)
    - thickness > 0           (division-by-zero in compartment calc, line 7752)
    - sat, fc, wp ordering    (negative TAW → nonsense results)
    - sat in (0, 100] vol%    (LoadProfile, line 7668)
    - fc in (0, 100) vol%
    - wp in [0, fc) vol%
    - ksat > 0                (division-by-zero, line 7716)
    - penetrability 0..100    (int8, line 7668)
    - gravel 0..100           (int8, line 7668)
    """
    errors: list[str] = []

    n = len(layers)
    if n == 0:
        errors.append("At least 1 soil layer is required")
        raise AquaCropValidationError(errors)
    if n > MAX_SOIL_LAYERS:
        errors.append(
            f"Too many soil layers: {n} (max {MAX_SOIL_LAYERS}). "
            f"Fortran array max_SoilLayers = {MAX_SOIL_LAYERS}"
        )

    for i, layer in enumerate(layers, 1):
        prefix = f"soil[{i}]"

        # ── thickness ───────────────────────────────────────────
        if layer.thickness <= 0:
            errors.append(
                f"{prefix}.thickness = {layer.thickness}: "
                f"must be > 0 (used for compartment sizing)"
            )

        # ── penetrability (int8 in Fortran) ─────────────────────
        _check_int8_percent(
            errors, layer.penetrability, f"{prefix}.penetrability"
        )

        # ── gravel (int8 in Fortran) ────────────────────────────
        _check_int8_percent(errors, layer.gravel, f"{prefix}.gravel")

        # ── hydraulic constants (only for SoilLayerWithConstants / SoilLayerParams)
        if hasattr(layer, "sat"):
            sat = layer.sat
            fc = layer.fc
            wp = layer.wp
            ksat = layer.ksat

            if sat <= 0 or sat > 100:
                errors.append(
                    f"{prefix}.sat = {sat}: must be in (0, 100] vol%"
                )
            if fc <= 0 or fc >= 100:
                errors.append(
                    f"{prefix}.fc = {fc}: must be in (0, 100) vol%"
                )
            if wp < 0 or wp >= 100:
                errors.append(
                    f"{prefix}.wp = {wp}: must be in [0, 100) vol%"
                )

            # Physical ordering: sat > fc > wp
            if sat > 0 and fc > 0 and sat <= fc:
                errors.append(
                    f"{prefix}: sat ({sat}) must be > fc ({fc})"
                )
            if fc > 0 and wp >= 0 and fc <= wp:
                errors.append(
                    f"{prefix}: fc ({fc}) must be > wp ({wp})"
                )

            # ksat — division by zero at global.f90:7716
            if ksat <= 0:
                errors.append(
                    f"{prefix}.ksat = {ksat}: must be > 0 "
                    f"(division-by-zero in capillary rise calc)"
                )

        # ── texture fields (SoilLayerWithTexture) ───────────────
        if hasattr(layer, "clay"):
            for field in ("clay", "silt", "sand"):
                val = getattr(layer, field)
                if val < 0 or val > 100:
                    errors.append(
                        f"{prefix}.{field} = {val}: must be in [0, 100] %"
                    )

    if errors:
        raise AquaCropValidationError(errors)


def validate_fertility_stress(value: int | float) -> None:
    """Validate fertility stress (int8 in Fortran, 0-100%).

    Written to .MAN file → read as int8 at global.f90:3383.
    """
    errors: list[str] = []
    _check_int8_percent(errors, value, "fertility_stress")
    if errors:
        raise AquaCropValidationError(errors)


def validate_season(season: Season) -> None:
    """Validate season date ordering."""
    errors: list[str] = []

    if season.simulation_start > season.simulation_end:
        errors.append(
            f"simulation_start ({season.simulation_start}) "
            f"must be <= simulation_end ({season.simulation_end})"
        )
    if season.growing_season_start > season.growing_season_end:
        errors.append(
            f"growing_season_start ({season.growing_season_start}) "
            f"must be <= growing_season_end ({season.growing_season_end})"
        )
    if season.simulation_start > season.growing_season_start:
        errors.append(
            f"simulation_start ({season.simulation_start}) "
            f"must be <= growing_season_start ({season.growing_season_start})"
        )
    if season.growing_season_end > season.simulation_end:
        errors.append(
            f"growing_season_end ({season.growing_season_end}) "
            f"must be <= simulation_end ({season.simulation_end})"
        )

    if errors:
        raise AquaCropValidationError(errors)


def validate_all(
    *,
    soil_layers: list | None = None,
    fertility_stress: int | float | None = None,
    seasons: list[Season] | None = None,
) -> None:
    """Run all applicable validations, collecting errors from each."""
    all_errors: list[str] = []

    if soil_layers is not None:
        try:
            validate_soil_layers(soil_layers)
        except AquaCropValidationError as e:
            all_errors.extend(e.errors)

    if fertility_stress is not None:
        try:
            validate_fertility_stress(fertility_stress)
        except AquaCropValidationError as e:
            all_errors.extend(e.errors)

    if seasons is not None:
        for i, season in enumerate(seasons):
            try:
                validate_season(season)
            except AquaCropValidationError as e:
                all_errors.extend(
                    f"season[{i + 1}]: {err}" for err in e.errors
                )

    if all_errors:
        raise AquaCropValidationError(all_errors)


# ── Internal helpers ────────────────────────────────────────────────

def _check_int8_percent(
    errors: list[str], value: float, name: str
) -> None:
    """Check value fits in Fortran int8 (−128..127) AND is a valid 0-100%."""
    if value < 0 or value > 100:
        errors.append(
            f"{name} = {value}: must be in [0, 100] % "
            f"(stored as int8 in Fortran, max 127)"
        )
    elif value > INT8_MAX:
        # Shouldn't happen with 0-100 check, but guard anyway
        errors.append(
            f"{name} = {value}: exceeds Fortran int8 max ({INT8_MAX})"
        )
