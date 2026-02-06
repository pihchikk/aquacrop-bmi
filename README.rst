==================
aquacrop_bmi_babel
==================

BMI wrapper for AquaCrop - FAO's crop water productivity model with full Basic Model Interface compliance.

Features
========

* Full BMI 2.0 standard implementation
* JSON-based configuration with dict/string initialization
* Automated weather data retrieval (NASA POWER API)
* Built-in calibration tools
* 17 real-time output variables including yield, biomass, canopy cover, and soil moisture

Installation
============

System Requirements
-------------------

Ubuntu/Debian::

    sudo apt-get update
    sudo apt-get install -y gfortran cmake pkg-config make git python3-dev



Optional: Virtual Environment
------------------------------

Recommended but not required::

    # Using venv
    python3 -m venv ~/aquacrop_env
    source ~/aquacrop_env/bin/activate
    
    # Or using conda
    conda create -n aquacrop python=3.11 -y
    conda activate aquacrop


Build BMI-Fortran
-----------------

Required dependency::

    git clone https://github.com/csdms/bmi-fortran
    cd bmi-fortran
    mkdir build && cd build
    cmake .. -DCMAKE_INSTALL_PREFIX=$HOME/.local
    make && make install
    export PKG_CONFIG_PATH=$HOME/.local/lib/pkgconfig:$PKG_CONFIG_PATH

Install PyMT (for model coupling)
----------------------------------

Dev version required (conda-forge version incompatible)::

    git clone https://github.com/csdms/pymt
    cd pymt
    pip install -r requirements.txt
    pip install -e .

Install AquaCrop BMI
--------------------

From PyPI::

    pip install aquacrop-bmi-babel

From source::

    git clone https://github.com/pihchikk/aquacrop_bmi_babel.git
    cd aquacrop_bmi_babel
    pip install -e . --no-build-isolation

Development Setup
-----------------

For development with editable installations::

    # Add PyMT to PYTHONPATH (if installed with -e)
    export PYTHONPATH="/path/to/pymt:$PYTHONPATH"
        
    # Make persistent (add to ~/.bashrc):
    echo 'export PYTHONPATH="/home/jovyan/work/pymt:$PYTHONPATH"' >> ~/.bashrc
    source ~/.bashrc

Usage
=====

Direct BMI (Recommended for Interactive Use)
---------------------------------------------

::

    from aquacrop_bmi_babel import AquaCrop
    import numpy as np
    
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
            "thickness": 200.0, "sat": 0.50, "fc": 0.31, "pwp": 0.15,
            "wc": 0.31, "penetrability": 100.0, "gravel": 0.0,
            "ec": 0.5, "wp": 0.15, "ksat": 1200.0
        }]],
        "fertility_stress": 10
    }
    
    model = AquaCrop()
    model.initialize_from_dict(config)
    
    dest = np.empty(1, dtype=np.float64)
    while model.get_current_time() < model.get_end_time():
        model.update()
        model.get_value("crop__yield", dest)
    
    print(f"Final yield: {dest[0]:.2f} t/ha")
    model.finalize()

PyMT Plugin (for Model Coupling)
---------------------------------

::

    from pymt.models import AquaCrop
    import json
    
    with open('config.json', 'w') as f:
        json.dump(config, f)
    
    model = AquaCrop()
    model.initialize('config.json')
    
    while model.time < model.end_time:
        model.update()
    
    yield_val = model.get_value("crop__yield")
    model.finalize()

Configuration
=============

Required Fields
---------------

Minimum required configuration::

    {
      "gwt_depth": 5.0,              // Groundwater depth (m)
      "gwt_ec": 0.0,                 // Groundwater EC
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
        "thickness": 200.0, "sat": 0.50, "fc": 0.31,
        "pwp": 0.15, "wc": 0.31, "penetrability": 100.0,
        "gravel": 0.0, "ec": 0.5, "wp": 0.15, "ksat": 1200.0
      }]],
      "fertility_stress": 10
    }

Important: Use FLAT soil structure (all fields at top level), not nested "const" dict.

Output Variables
================

Available for real-time monitoring (17 total)::

    crop__canopy_cover, crop__biomass, crop__yield
    soil__moisture, soil__moisture_layer_1 through layer_5
    crop__water_stress, crop__temperature_stress
    crop__aeration_stress, crop__salinity_stress
    crop__rooting_depth, crop__transpiration
    crop__evapotranspiration, crop__biomass_potential

Troubleshooting
===============

pkg-config not found
--------------------

::

    export PKG_CONFIG_PATH=$HOME/.local/lib/pkgconfig:$PKG_CONFIG_PATH
    pkg-config --modversion bmif  # Should return version number