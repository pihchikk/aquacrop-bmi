"""BMI wrapper for AquaCrop that uses existing API functions."""

from __future__ import annotations

import numpy as np
from bmipy import Bmi
from numpy.typing import NDArray

from aquacrop_bmi import sync
from aquacrop_bmi.models import ScenariosSimulationInput

class BmiAquaCrop(Bmi):
    """BMI wrapper using existing aquacrop_api sync functions."""

    _name = "AquaCrop"
    _input_var_names = ("crop__fertility_stress", "soil__water_content_in_layers")
    _output_var_names = (
        "crop__yield", "crop__biomass", "crop__canopy_cover",
        "soil__water_content_in_compartments", "soil__compartment_thickness",
        "soil_water__deep_percolation_flux", "land_surface_water__runoff_flux",
        "soil_water__infiltration_flux", "soil__evaporation_flux",
        "crop__transpiration_flux_actual", "soil_water__capillary_rise_flux",
    )

    def __init__(self) -> None:
        self._time = 0.0
        self._time_step = 1.0
        self._end_time = 0.0
        
        self._input_data: ScenariosSimulationInput | None = None
        self._result = None
        self._current_season = 0
        self._current_day = 0
        self._values: dict[str, NDArray] = {}

    def initialize(self, config_file: str) -> None:
        """Initialize from JSON file (like the API examples)."""
        import json
        from aquacrop_bmi.models import ScenariosSimulationInput
        
        with open(config_file) as f:
            config = json.load(f)
        
        self._input_data = ScenariosSimulationInput(**config)
        
        # Calculate time bounds
        total_days = sum(
            (s.simulation_end - s.simulation_start).days + 1
            for s in self._input_data.seasons
        )
        self._end_time = float(total_days)
        
        # Initialize values
        for var in self._output_var_names:
            self._values[var] = np.array([0.0])
        self._values["crop__fertility_stress"] = np.array([float(self._input_data.fertility_stress)])

    def update(self) -> None:
        """Advance one time step."""
        # Run simulation on first call ONLY
        if self._result is None:
            print("=== Running AquaCrop Fortran simulation (ONE TIME) ===")
            self._result = sync.run_scenarios_simulation(self._input_data)
            
            # DEBUG: Show what we got from Fortran (PRINTS ONCE)
            print(f"\n=== Simulation Results ===")
            print(f"Number of soil profiles: {len(self._result.items)}")
            print(f"Number of seasons: {len(self._result.items[0])}")
            
            for season_idx, season_data in enumerate(self._result.items[0]):
                print(f"\nSeason {season_idx + 1}:")
                print(f"  Days simulated: {len(season_data)}")
                
                if len(season_data) > 0:
                    first_day = season_data[0]
                    last_day = season_data[-1]
                    mid_day = season_data[len(season_data)//2]
                    
                    print(f"  First day: Date={first_day[0]}, CC={first_day[28]}%, Biomass={first_day[37]} t/ha, Yield={first_day[39]} t/ha")
                    print(f"  Mid day:   Date={mid_day[0]}, CC={mid_day[28]}%, Biomass={mid_day[37]} t/ha, Yield={mid_day[39]} t/ha")
                    print(f"  Last day:  Date={last_day[0]}, CC={last_day[28]}%, Biomass={last_day[37]} t/ha, Yield={last_day[39]} t/ha")
            
            print("\n=== Starting BMI time-stepping ===\n")
        
        # This part runs EVERY call (reading from cache)
        soil_idx = 0
        
        if self._current_season >= len(self._input_data.seasons):
            return
        
        daily_data = self._result.items[soil_idx][self._current_season]
        # ... rest of update code
        
        if self._current_day < len(daily_data):
            day_row = daily_data[self._current_day]
            
            # Map to correct indices from DAILY_OUT_HEADER
            # 28: CC (Canopy Cover %)
            # 37: Biomass (tonnes/ha)
            # 39: Y(dry) (Yield tonnes/ha)
            
            if len(day_row) > 39:
                cc_val = day_row[28]
                biomass_val = day_row[37]
                yield_val = day_row[39]
                
                # Handle -9 (no data) values
                self._values["crop__canopy_cover"][0] = float(cc_val) if cc_val != -9 else 0.0
                self._values["crop__biomass"][0] = float(biomass_val) if biomass_val != -9 else 0.0
                self._values["crop__yield"][0] = float(yield_val) if yield_val != -9 else 0.0
        
        self._time += self._time_step
        self._current_day += 1
        
        # Move to next season if needed
        season = self._input_data.seasons[self._current_season]
        season_days = (season.simulation_end - season.simulation_start).days + 1
        if self._current_day >= season_days:
            self._current_season += 1
            self._current_day = 0

    def update_until(self, then: float) -> None:
        while self._time < then:
            self.update()

    def finalize(self) -> None:
        self._result = None
        self._values.clear()

    def get_component_name(self) -> str:
        return self._name

    def get_input_item_count(self) -> int:
        return len(self._input_var_names)

    def get_output_item_count(self) -> int:
        return len(self._output_var_names)

    def get_input_var_names(self) -> tuple[str, ...]:
        return self._input_var_names

    def get_output_var_names(self) -> tuple[str, ...]:
        return self._output_var_names

    def get_var_grid(self, var_name: str) -> int:
        return 0

    def get_var_type(self, var_name: str) -> str:
        return "float64"

    def get_var_units(self, var_name: str) -> str:
        units = {
            "crop__yield": "tonnes/ha",
            "crop__biomass": "tonnes/ha",
            "crop__canopy_cover": "percent",
            "crop__fertility_stress": "percent",
        }
        return units.get(var_name, "")

    def get_var_itemsize(self, var_name: str) -> int:
        return 8

    def get_var_nbytes(self, var_name: str) -> int:
        return 8

    def get_var_location(self, var_name: str) -> str:
        return "node"

    def get_current_time(self) -> float:
        return self._time

    def get_start_time(self) -> float:
        return 0.0

    def get_end_time(self) -> float:
        return self._end_time

    def get_time_units(self) -> str:
        return "days"

    def get_time_step(self) -> float:
        return self._time_step

    def get_value(self, var_name: str, dest: NDArray) -> NDArray:
        dest[:] = self._values[var_name]
        return dest

    def get_value_ptr(self, var_name: str) -> NDArray:
        return self._values[var_name]

    def get_value_at_indices(self, var_name: str, dest: NDArray, indices: NDArray) -> NDArray:
        dest[:] = self._values[var_name][indices]
        return dest

    def set_value(self, var_name: str, src: NDArray) -> None:
        self._values[var_name][:] = src
        if var_name == "crop__fertility_stress" and self._input_data:
            self._input_data.fertility_stress = int(src[0])

    def set_value_at_indices(self, var_name: str, inds: NDArray, src: NDArray) -> None:
        self._values[var_name][inds] = src

    def get_grid_rank(self, grid_id: int) -> int:
        return 0

    def get_grid_size(self, grid_id: int) -> int:
        return 1

    def get_grid_type(self, grid_id: int) -> str:
        return "scalar"

    def get_grid_x(self, grid_id: int, x: NDArray) -> NDArray:
        if self._input_data:
            x[0] = self._input_data.point.longitude
        return x

    def get_grid_y(self, grid_id: int, y: NDArray) -> NDArray:
        if self._input_data:
            x[0] = self._input_data.point.latitude
        return y

    def get_grid_z(self, grid_id: int, z: NDArray) -> NDArray:
        if self._input_data:
            x[0] = self._input_data.point.altitude
        return z

    def get_grid_node_count(self, grid_id: int) -> int:
        return 1

    # Remaining grid methods raise NotImplementedError
    def get_grid_shape(self, grid_id: int, shape: NDArray) -> NDArray:
        raise NotImplementedError
    def get_grid_spacing(self, grid_id: int, spacing: NDArray) -> NDArray:
        raise NotImplementedError
    def get_grid_origin(self, grid_id: int, origin: NDArray) -> NDArray:
        raise NotImplementedError
    def get_grid_edge_count(self, grid_id: int) -> int:
        raise NotImplementedError
    def get_grid_face_count(self, grid_id: int) -> int:
        raise NotImplementedError
    def get_grid_edge_nodes(self, grid_id: int, edge_nodes: NDArray) -> NDArray:
        raise NotImplementedError
    def get_grid_face_edges(self, grid_id: int, face_edges: NDArray) -> NDArray:
        raise NotImplementedError
    def get_grid_face_nodes(self, grid_id: int, face_nodes: NDArray) -> NDArray:
        raise NotImplementedError
    def get_grid_nodes_per_face(self, grid_id: int, nodes_per_face: NDArray) -> NDArray:
        raise NotImplementedError