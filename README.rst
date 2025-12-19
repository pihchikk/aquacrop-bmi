==================
aquacrop_bmi_babel
==================

BMI wrapper for AquaCrop - FAO's crop water productivity model with full Basic Model Interface compliance and Windows Subsystem for Linux (WSL) support.

Features
========

* Full BMI 2.0 standard implementation
* Windows WSL support
* JSON-based configuration
* Initialize from JSON string or Python dict
* Automated weather data retrieval (NASA POWER API)
* Built-in calibration tools
* 11 input variables, 17 output variables

Installation
============

System Requirements (Ubuntu/Debian)
------------------------------------

First, install system dependencies::

    sudo apt-get update
    sudo apt-get install -y gfortran cmake pkg-config make git python3-dev python3-venv

Python Environment Setup
-------------------------

Option 1: Using venv (Recommended for testing)::

    python3 -m venv ~/aquacrop_env
    source ~/aquacrop_env/bin/activate

Option 2: Using conda (Recommended for production)::

    conda create -n aquacrop python=3.11 -y
    conda activate aquacrop

Build BMI-Fortran from Source
------------------------------

Required dependency that must be built before installing aquacrop-bmi-babel::

    # Clone repository
    git clone https://github.com/csdms/bmi-fortran
    cd bmi-fortran
    
    # Build and install
    mkdir build && cd build
    cmake .. -DCMAKE_INSTALL_PREFIX=$HOME/.local
    make && make install
    
    # Set pkg-config path
    export PKG_CONFIG_PATH=$HOME/.local/lib/pkgconfig:$PKG_CONFIG_PATH
    
    # For conda environments, use:
    # cmake .. -DCMAKE_INSTALL_PREFIX=$CONDA_PREFIX

Install PyMT from Source (Required for Plugin Usage)
-----------------------------------------------------

The stable PyMT from conda-forge is not compatible. You must use the development version::

    git clone https://github.com/csdms/pymt
    cd pymt
    
    # Install dependencies
    pip install -r requirements.txt
    
    # Install in development mode
    pip install -e .

Install AquaCrop BMI Babel
---------------------------

From PyPI::

    pip install aquacrop-bmi-babel

From source (for development)::

    git clone https://github.com/pihchikk/aquacrop_bmi_babel.git
    cd aquacrop_bmi_babel
    pip install -e . --no-build-isolation

Complete Installation Script
-----------------------------

For a fresh Ubuntu/Debian system::

    # 1. System packages
    sudo apt-get update
    sudo apt-get install -y gfortran cmake pkg-config make git python3-dev python3-venv
    
    # 2. Python environment
    python3 -m venv ~/aquacrop_env
    source ~/aquacrop_env/bin/activate
    
    # 3. Build BMI-Fortran
    cd ~
    git clone https://github.com/csdms/bmi-fortran
    cd bmi-fortran
    mkdir build && cd build
    cmake .. -DCMAKE_INSTALL_PREFIX=$HOME/.local
    make && make install
    export PKG_CONFIG_PATH=$HOME/.local/lib/pkgconfig:$PKG_CONFIG_PATH
    
    # 4. Install PyMT
    cd ~
    git clone https://github.com/csdms/pymt
    cd pymt
    pip install -r requirements.txt
    pip install -e .
    
    # 5. Install AquaCrop BMI
    pip install aquacrop-bmi-babel

Usage
=====

Direct BMI Usage
----------------

Import directly for programmatic use with JSON initialization::

    from aquacrop_bmi_babel import AquaCrop
    import numpy as np

    # Initialize from dict (no file needed!)
    config = {
        "gwt_depth": 5.0,
        "gwt_ec": 0.0,
        "point": {"latitude": 39.9, "longitude": -105.2},
        "seasons": [{
            "planting_date": "2020-05-01",
            "simulation_start": "2020-04-15",
            "simulation_end": "2020-09-20",
            "growing_season_start": "2020-04-15",
            "growing_season_end": "2020-09-20"
        }],
        "crop_file": "MaizeGDD",
        "soils": [[{
            "thickness": 200.0,
            "sat": 0.50,
            "fc": 0.31,
            "pwp": 0.15,
            "wc": 0.31,
            "penetrability": 100.0,
            "gravel": 0.0,
            "ec": 0.5,
            "wp": 0.15,
            "ksat": 1200.0
        }]],
        "fertility_stress": 10
    }
    
    model = AquaCrop()
    model.initialize_from_dict(config)
    
    # Run simulation step by step
    dest = np.empty(1, dtype=np.float64)
    while model.get_current_time() < model.get_end_time():
        model.update()
        model.get_value("crop__yield", dest)
        print(f"Yield: {dest[0]:.2f} t/ha")
    
    model.finalize()

PyMT Plugin Usage
-----------------

Use PyMT wrapper for model coupling scenarios::

    from pymt.models import AquaCrop
    import json
    
    # PyMT requires file-based initialization
    with open('config.json', 'w') as f:
        json.dump(config, f)
    
    model = AquaCrop()
    model.initialize('config.json')
    
    # Access BMI functions as properties
    print(model.component_name)
    print(model.output_var_names)
    
    # Run simulation
    while model.time < model.end_time:
        model.update()
    
    yield_val = model.get_value("crop__yield")
    print(f"Final yield: {yield_val[0]:.2f} t/ha")
    
    model.finalize()

Note on PyMT Installation
^^^^^^^^^^^^^^^^^^^^^^^^^^

The stable PyMT from conda-forge is not compatible with this package. You must use the development version from source as shown in the installation steps above.

New in v0.2.1
=============

JSON String Initialization
---------------------------

Initialize directly from JSON string or Python dict without creating files::

    from aquacrop_bmi_babel import AquaCrop
    
    # From dict (recommended)
    model = AquaCrop()
    model.initialize_from_dict(config_dict)
    
    # Or from JSON string
    import json
    model.initialize_from_json(json.dumps(config_dict))

Windows WSL Support
-------------------

Full support for Windows Subsystem for Linux with automatic path handling::

    # Works with Windows paths in WSL
    model.initialize("/mnt/d/projects/scenario.json")

Available Output Variables
===========================

The model provides 17 output variables for real-time monitoring::

    crop__canopy_cover
    crop__biomass
    crop__yield
    soil__moisture
    crop__water_stress
    crop__temperature_stress
    crop__aeration_stress
    crop__salinity_stress
    crop__rooting_depth
    crop__transpiration
    crop__evapotranspiration
    crop__biomass_potential
    soil__moisture_layer_1
    soil__moisture_layer_2
    soil__moisture_layer_3
    soil__moisture_layer_4
    soil__moisture_layer_5

Configuration Format
====================

Required Fields
---------------

All JSON configurations must include::

    {
      "gwt_depth": 5.0,                    // Groundwater table depth (m)
      "gwt_ec": 0.0,                       // Groundwater electrical conductivity
      "point": {
        "latitude": 39.9,
        "longitude": -105.2
      },
      "seasons": [{
        "planting_date": "2020-05-01",
        "simulation_start": "2020-04-15",
        "simulation_end": "2020-09-20",
        "growing_season_start": "2020-04-15",    // Required
        "growing_season_end": "2020-09-20"       // Required
      }],
      "crop_file": "MaizeGDD",
      "soils": [[{
        // Use FLAT structure (not nested)
        "thickness": 200.0,
        "sat": 0.50,
        "fc": 0.31,
        "pwp": 0.15,
        "wc": 0.31,
        "penetrability": 100.0,
        "gravel": 0.0,
        "ec": 0.5,
        "wp": 0.15,
        "ksat": 1200.0
      }]],
      "fertility_stress": 10
    }

Soil Structure
--------------

Use FLAT structure for soil layers. Do NOT use nested "const" dict::

    // Correct (FLAT):
    {
      "thickness": 200.0,
      "sat": 0.50,
      "wc": 0.31,
      "ec": 0.5
    }
    
    // Incorrect (NESTED):
    {
      "const": {
        "wc": 0.31,
        "ec": 0.5
      }
    }

Troubleshooting
===============

Network Timeouts
----------------

If NASA POWER API times out during weather data retrieval, use cached data::

    # Skip preprocessing, use existing preprocessed data
    model.initialize("/path/to/outputs/simulation-data_XXX/LIST/project.PRO")

pkg-config Not Found
--------------------

If installation fails with "Dependency aquacropbmi not found"::

    # Ensure BMI-Fortran is installed
    pkg-config --modversion bmif
    
    # If not found, check PKG_CONFIG_PATH
    export PKG_CONFIG_PATH=$HOME/.local/lib/pkgconfig:$PKG_CONFIG_PATH
    
    # Or for conda:
    export PKG_CONFIG_PATH=$CONDA_PREFIX/lib/pkgconfig:$PKG_CONFIG_PATH

Second Initialize Fails
------------------------

If second model initialization fails with path errors, ensure you have v0.2.1 or later which fixes critical working directory management bug.

Links
=====

* GitHub: https://github.com/pihchikk/aquacrop_bmi_babel
* Documentation: https://aquacrop-bmi-babel.readthedocs.io
* PyPI: https://pypi.org/project/aquacrop-bmi-babel/
* Issues: https://github.com/pihchikk/aquacrop_bmi_babel/issues

License
=======

MIT License

Contributing
============

Contributions welcome! Please submit pull requests to the GitHub repository.

For bug reports, use GitHub Issues and include:
- Python version
- Operating system
- Installation method (pip/source)
- Minimal reproducible example