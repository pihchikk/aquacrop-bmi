==================
aquacrop_bmi_babel
==================

BMI wrapper for AquaCrop - FAO's crop water productivity model with full Basic Model Interface compliance

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

From Source (Development)::

    git clone https://github.com/pihchikk/aquacrop_bmi_babel.git
    cd aquacrop_bmi_babel
    pip install -e . --no-build-isolation

From Source::

    git clone https://github.com/pihchikk/aquacrop_bmi_babel.git
    cd aquacrop_bmi_babel
    pip install .

System Requirements
-------------------

Linux/WSL::

    sudo apt-get install gfortran
    conda install -c conda-forge bmi-fortran
    pip install aquacrop-bmi-babel

Usage
=====

Basic Example::

    from aquacrop_bmi_babel import AquaCrop
    import numpy as np

    model = AquaCrop()
    model.initialize("scenario.json")
    
    while model.get_current_time() < model.get_end_time():
        model.update()
    
    yield_data = np.empty(1, dtype=np.float64)
    model.get_value("crop__yield", yield_data)
    print(f"Yield: {yield_data[0]:.2f} t/ha")
    
    model.finalize()

New in v0.2.1
=============

Initialize from JSON string::

    import json
    from aquacrop_bmi_babel import AquaCrop
    
    config = {
        "gwt_depth": 5.0,
        "point": {"latitude": 39.9, "longitude": -105.2},
        "seasons": [{"planting_date": "2020-05-01"}],
        "crop_file": "MaizeGDD",
        "soils": [[{"thickness": 200.0, "sat": 0.50}]]
    }
    
    model = AquaCrop()
    model.initialize_from_dict(config)

WSL Support::

    # Works with Windows paths in WSL
    model.initialize("/mnt/d/projects/scenario.json")

Links
=====

* GitHub: https://github.com/pihchikk/aquacrop_bmi_babel
* Documentation: https://aquacrop-bmi-babel.readthedocs.io
* PyPI: https://pypi.org/project/aquacrop-bmi-babel/

License
=======

MIT License