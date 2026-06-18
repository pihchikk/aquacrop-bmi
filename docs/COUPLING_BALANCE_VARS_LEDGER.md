# Coupling & Balance Variables Ledger

## BMI Variable Mapping

### Vector outputs (grid 2 — compartments, rank 1, size = NrCompartments)

| BMI name | Fortran accessor | Units | Grid | Target standard name (project) |
|---|---|---|---|---|
| `soil__water_content_in_compartments` | `GetCompartment_theta(i)` | `m3 m-3` | 2 | `soil_water_actual` (per compartment) |
| `soil__compartment_thickness` | `GetCompartment_Thickness(i)` | `m` | 2 | `soil_depth~compartment` (COINED-pending) |

### Scalar outputs (grid 0, daily fluxes)

| BMI name | Fortran accessor | Units | Grid | Target standard name (project) |
|---|---|---|---|---|
| `soil_water__deep_percolation_flux` | `GetDrain()` | `mm` | 0 | `soil_water_drainage~deep` (COINED-pending) |
| `land_surface_water__runoff_flux` | `GetRunoff()` | `mm` | 0 | `water~surface_runoff` (COINED-pending) |
| `soil_water__infiltration_flux` | `GetInfiltrated()` | `mm` | 0 | `soil_infiltration~rate` (verify registry) |
| `soil__evaporation_flux` | `GetEact()` | `mm` | 0 | `air_evaporation` |
| `crop__transpiration_flux_actual` | `GetTact()` | `mm` | 0 | `air_transpiration` |
| `soil_water__capillary_rise_flux` | `GetCRwater()` | `mm` | 0 | `soil_water_capillary_rise` (COINED-pending) |

### Pre-existing outputs (unchanged)

| BMI name | Notes |
|---|---|
| `crop__transpiration` | Cumulative `GetSumWaBal_Tact()` (mm) — NOT daily |
| `crop__evapotranspiration` | Cumulative `GetSumWaBal_Eact()` (mm) — NOT daily |
| `soil__moisture` | Root zone WC `GetRootZoneWC_Actual()` (mm) |
| `soil__moisture_layer_1..10` | Per-layer theta via `GetSoilLayerTheta()` (m3 m-3) |
| `soil__water_content_in_layers` | Vector of per-layer theta (m3 m-3), grid 1 |

## Daily Water Balance (AquaCrop)

### Equation

    Inflow partition:   Rain + Irrigation = Infiltrated + Runoff
    Storage change:     dS = Infiltrated + CRwater - Drain - Eact - Tact

Where:
- `dS` = change in total profile water storage (sum of compartment theta * thickness)
- All fluxes in mm/day

### Balance check results

To be filled after running `tests/test_coupling_balance_vars.py` with a real config.

## Grid Summary

| Grid ID | Type | Rank | Size | Used by |
|---|---|---|---|---|
| 0 | scalar | 0 | 1 | All scalar variables |
| 1 | uniform_rectilinear | 1 | NrSoilLayers | `soil__water_content_in_layers` |
| 2 | uniform_rectilinear | 1 | NrCompartments | `soil__water_content_in_compartments`, `soil__compartment_thickness` |
