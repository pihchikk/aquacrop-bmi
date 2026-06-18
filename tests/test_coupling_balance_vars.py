"""Tests for coupling/balance BMI variables.

Requires a built AquaCrop BMI library and a valid config file.
Set AQUACROP_TEST_CONFIG env var to point at a JSON config, or skip.
"""
from __future__ import annotations

import os
import pytest
import numpy as np


CONFIG = os.environ.get("AQUACROP_TEST_CONFIG")
SKIP_REASON = "Set AQUACROP_TEST_CONFIG to a valid JSON config path"


def _make_model():
    from aquacrop_bmi_babel import AquaCrop
    m = AquaCrop()
    m.initialize(CONFIG)
    m.update()
    return m


@pytest.fixture(scope="module")
def model():
    if not CONFIG:
        pytest.skip(SKIP_REASON)
    m = _make_model()
    yield m
    m.finalize()


class TestCompartmentVectors:
    def test_water_content_length(self, model):
        g = model.get_var_grid("soil__water_content_in_compartments")
        n = model.get_grid_size(g)
        assert n > 0
        buf = np.empty(n)
        model.get_value("soil__water_content_in_compartments", buf)
        assert len(buf) == n

    def test_water_content_range(self, model):
        g = model.get_var_grid("soil__water_content_in_compartments")
        n = model.get_grid_size(g)
        buf = np.empty(n)
        model.get_value("soil__water_content_in_compartments", buf)
        assert np.all(buf >= 0.0), f"negative theta: {buf}"
        assert np.all(buf <= 1.0), f"theta > 1: {buf}"

    def test_thickness_length(self, model):
        g = model.get_var_grid("soil__compartment_thickness")
        n = model.get_grid_size(g)
        buf = np.empty(n)
        model.get_value("soil__compartment_thickness", buf)
        assert len(buf) == n
        assert np.all(buf > 0.0), f"non-positive thickness: {buf}"

    def test_thickness_sum(self, model):
        g = model.get_var_grid("soil__compartment_thickness")
        n = model.get_grid_size(g)
        buf = np.empty(n)
        model.get_value("soil__compartment_thickness", buf)
        total_depth = buf.sum()
        assert 0.5 < total_depth < 10.0, f"total depth {total_depth} m out of range"


class TestDailyFluxes:
    FLUX_VARS = [
        "soil_water__deep_percolation_flux",
        "land_surface_water__runoff_flux",
        "soil_water__infiltration_flux",
        "soil__evaporation_flux",
        "crop__transpiration_flux_actual",
        "soil_water__capillary_rise_flux",
    ]

    @pytest.mark.parametrize("var", FLUX_VARS)
    def test_flux_finite_nonnegative(self, model, var):
        buf = np.empty(1)
        model.get_value(var, buf)
        assert np.isfinite(buf[0]), f"{var} = {buf[0]}"
        assert buf[0] >= 0.0, f"{var} = {buf[0]}"

    @pytest.mark.parametrize("var", FLUX_VARS)
    def test_flux_is_scalar(self, model, var):
        g = model.get_var_grid(var)
        assert model.get_grid_size(g) == 1


class TestMetadata:
    COMPARTMENT_VARS = [
        "soil__water_content_in_compartments",
        "soil__compartment_thickness",
    ]

    @pytest.mark.parametrize("var", COMPARTMENT_VARS)
    def test_grid_is_2(self, model, var):
        g = model.get_var_grid(var)
        assert g == 2

    @pytest.mark.parametrize("var", COMPARTMENT_VARS)
    def test_nbytes_consistent(self, model, var):
        g = model.get_var_grid(var)
        n = model.get_grid_size(g)
        expected = n * 8
        assert model.get_var_nbytes(var) == expected

    def test_units_theta(self, model):
        assert model.get_var_units("soil__water_content_in_compartments") == "m3 m-3"

    def test_units_thickness(self, model):
        assert model.get_var_units("soil__compartment_thickness") == "m"

    @pytest.mark.parametrize("var", TestDailyFluxes.FLUX_VARS)
    def test_units_flux(self, model, var):
        assert model.get_var_units(var) == "mm"


class TestWaterBalance:
    """Approximate daily water balance closure check."""

    def test_balance_closure(self, model):
        rain = np.empty(1)
        model.get_value("weather__rainfall_amount", rain)
        irr = np.empty(1)
        model.get_value("management__irrigation_amount", irr)

        inf = np.empty(1)
        model.get_value("soil_water__infiltration_flux", inf)
        runoff = np.empty(1)
        model.get_value("land_surface_water__runoff_flux", runoff)

        residual = (rain[0] + irr[0]) - (inf[0] + runoff[0])
        assert abs(residual) < 5.0, (
            f"Inflow partition residual = {residual:.3f} mm "
            f"(Rain={rain[0]:.2f}, Irr={irr[0]:.2f}, "
            f"Inf={inf[0]:.2f}, Runoff={runoff[0]:.2f})"
        )
