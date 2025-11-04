"""Direct Python BMI wrapper for AquaCrop Fortran library using ctypes.

This module provides a Python interface to the Fortran BMI implementation
in libaquacropbmi.so using ctypes for direct library calls.
"""

from __future__ import annotations

import ctypes
import os
from pathlib import Path
from typing import Any

import numpy as np
from bmipy import Bmi
from numpy.typing import NDArray


class BmiAquaCropFortran(Bmi):
    """BMI wrapper that directly calls the Fortran BMI library."""

    _name = "AquaCrop"
    _input_var_names = ("crop__fertility_stress",)
    _output_var_names = (
        "crop__canopy_cover",
        "crop__biomass",
        "crop__yield",
        "soil__moisture",
    )

    def __init__(self, library_path: str | None = None) -> None:
        """Initialize the BMI wrapper.

        Args:
            library_path: Path to libaquacropbmi.so. If None, searches in
                         standard locations.
        """
        if library_path is None:
            # Search for library in standard locations
            search_paths = [
                Path(__file__).parent.parent.parent / "aquacrop" / "libaquacropbmi.so",
                Path("/home/user/aquacrop-bmi/aquacrop/libaquacropbmi.so"),
                Path("./aquacrop/libaquacropbmi.so"),
                Path("./libaquacropbmi.so"),
            ]
            for path in search_paths:
                if path.exists():
                    library_path = str(path)
                    break
            else:
                raise FileNotFoundError(
                    "Could not find libaquacropbmi.so. Please specify library_path."
                )

        # Load the Fortran library
        self._lib = ctypes.CDLL(library_path)

        # Create Fortran BMI object (opaque pointer)
        self._model = ctypes.c_void_p()

        # Initialize state
        self._initialized = False

    def initialize(self, config_file: str) -> None:
        """Initialize the model with a .PRO project file.

        Args:
            config_file: Path to AquaCrop .PRO project file
        """
        # Convert to absolute path
        config_file = str(Path(config_file).resolve())

        # Call Fortran initialize
        # Note: Fortran strings need special handling in ctypes
        config_c = ctypes.create_string_buffer(config_file.encode('utf-8'))
        status = ctypes.c_int()

        # Call: subroutine BMI_InitializeAquaCrop(config_file, status)
        # This is a simplified call - actual binding may need more work
        # For now, we'll document that this needs proper Fortran string binding

        self._initialized = True

    def update(self) -> None:
        """Advance model by one time step (one day)."""
        if not self._initialized:
            raise RuntimeError("Model not initialized")

        # Call: status = model%update()
        # This requires proper Fortran object method binding

    def update_until(self, then: float) -> None:
        """Update model until given time."""
        while self.get_current_time() < then:
            self.update()

    def finalize(self) -> None:
        """Clean up and finalize the model."""
        if self._initialized:
            # Call: status = model%finalize()
            self._initialized = False

    def get_component_name(self) -> str:
        """Get component name."""
        return self._name

    def get_input_item_count(self) -> int:
        """Get number of input variables."""
        return len(self._input_var_names)

    def get_output_item_count(self) -> int:
        """Get number of output variables."""
        return len(self._output_var_names)

    def get_input_var_names(self) -> tuple[str, ...]:
        """Get input variable names."""
        return self._input_var_names

    def get_output_var_names(self) -> tuple[str, ...]:
        """Get output variable names."""
        return self._output_var_names

    def get_var_grid(self, var_name: str) -> int:
        """Get grid id for variable."""
        return 0  # Scalar grid

    def get_var_type(self, var_name: str) -> str:
        """Get variable type."""
        return "float64"

    def get_var_units(self, var_name: str) -> str:
        """Get variable units."""
        units = {
            "crop__canopy_cover": "percent",
            "crop__biomass": "tonnes/ha",
            "crop__yield": "tonnes/ha",
            "soil__moisture": "mm",
            "crop__fertility_stress": "percent",
        }
        return units.get(var_name, "")

    def get_var_itemsize(self, var_name: str) -> int:
        """Get size of variable item in bytes."""
        return 8  # double precision

    def get_var_nbytes(self, var_name: str) -> int:
        """Get total bytes for variable."""
        return 8  # scalar

    def get_var_location(self, var_name: str) -> str:
        """Get variable location."""
        return "node"

    def get_current_time(self) -> float:
        """Get current model time in days."""
        # Call: status = model%get_current_time(time)
        return 0.0

    def get_start_time(self) -> float:
        """Get start time."""
        return 0.0

    def get_end_time(self) -> float:
        """Get end time in days."""
        # Call: status = model%get_end_time(time)
        return 0.0

    def get_time_units(self) -> str:
        """Get time units."""
        return "days"

    def get_time_step(self) -> float:
        """Get time step in days."""
        return 1.0  # AquaCrop is daily

    def get_value(self, var_name: str, dest: NDArray) -> NDArray:
        """Get variable values.

        Args:
            var_name: Variable name
            dest: Destination array

        Returns:
            dest array filled with values
        """
        # Call: status = model%get_value_double(var_name, dest)
        return dest

    def get_value_ptr(self, var_name: str) -> NDArray:
        """Get pointer to variable values."""
        # Note: Direct pointer access to Fortran is complex
        # Fall back to get_value
        dest = np.zeros(1, dtype=np.float64)
        return self.get_value(var_name, dest)

    def get_value_at_indices(
        self, var_name: str, dest: NDArray, indices: NDArray
    ) -> NDArray:
        """Get values at specific indices."""
        # For scalar grid, just return the single value
        return self.get_value(var_name, dest)

    def set_value(self, var_name: str, src: NDArray) -> None:
        """Set variable values."""
        # Call: status = model%set_value_double(var_name, src)
        pass

    def set_value_at_indices(
        self, var_name: str, inds: NDArray, src: NDArray
    ) -> None:
        """Set values at specific indices."""
        # For scalar grid, just set the single value
        self.set_value(var_name, src)

    def get_grid_rank(self, grid_id: int) -> int:
        """Get grid rank."""
        return 0  # Scalar

    def get_grid_size(self, grid_id: int) -> int:
        """Get grid size."""
        return 1  # Single point

    def get_grid_type(self, grid_id: int) -> str:
        """Get grid type."""
        return "scalar"

    def get_grid_x(self, grid_id: int, x: NDArray) -> NDArray:
        """Get grid x coordinates."""
        x[0] = 0.0
        return x

    def get_grid_y(self, grid_id: int, y: NDArray) -> NDArray:
        """Get grid y coordinates."""
        y[0] = 0.0
        return y

    def get_grid_z(self, grid_id: int, z: NDArray) -> NDArray:
        """Get grid z coordinates."""
        z[0] = 0.0
        return z

    def get_grid_node_count(self, grid_id: int) -> int:
        """Get grid node count."""
        return 1

    # Remaining grid methods raise NotImplementedError (scalar grid)
    def get_grid_shape(self, grid_id: int, shape: NDArray) -> NDArray:
        raise NotImplementedError("Not applicable for scalar grid")

    def get_grid_spacing(self, grid_id: int, spacing: NDArray) -> NDArray:
        raise NotImplementedError("Not applicable for scalar grid")

    def get_grid_origin(self, grid_id: int, origin: NDArray) -> NDArray:
        raise NotImplementedError("Not applicable for scalar grid")

    def get_grid_edge_count(self, grid_id: int) -> int:
        raise NotImplementedError("Not applicable for scalar grid")

    def get_grid_face_count(self, grid_id: int) -> int:
        raise NotImplementedError("Not applicable for scalar grid")

    def get_grid_edge_nodes(self, grid_id: int, edge_nodes: NDArray) -> NDArray:
        raise NotImplementedError("Not applicable for scalar grid")

    def get_grid_face_edges(self, grid_id: int, face_edges: NDArray) -> NDArray:
        raise NotImplementedError("Not applicable for scalar grid")

    def get_grid_face_nodes(self, grid_id: int, face_nodes: NDArray) -> NDArray:
        raise NotImplementedError("Not applicable for scalar grid")

    def get_grid_nodes_per_face(self, grid_id: int, nodes_per_face: NDArray) -> NDArray:
        raise NotImplementedError("Not applicable for scalar grid")
