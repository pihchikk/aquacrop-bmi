#!/usr/bin/env python3
"""
Capture AquaCrop temp directory before it gets deleted
"""

import json
import shutil
from pathlib import Path
from aquacrop_bmi.models import ScenariosSimulationInput
from aquacrop_bmi.project import AquacropProject
from aquacrop_bmi.util import loads_crop_file, get_weather_data
from aquacrop_bmi.soil_texture import get_soil_params

# Load example config
config_file = Path('./src/aquacrop_bmi/examples/scenarios-simulation.json')
with open(config_file) as f:
    config = json.load(f)

input_data = ScenariosSimulationInput(**config)

# Get first season for example
season = input_data.seasons[0]
soil = input_data.soils[0]

# Load crop
_, crop_index, crop_params = loads_crop_file(input_data.crop_file)

# Get weather data
point = input_data.point
altitude = getattr(point, 'altitude', 0)
weather_data = get_weather_data(
    point.latitude,
    point.longitude,
    altitude,
    season.simulation_start,
    season.simulation_end,
)

# Get soil params
soil_params = get_soil_params(soil)

print("Creating AquaCrop project with all files...")

# Create project and DON'T let it exit yet!
project_ctx = AquacropProject(with_default=False)
project = project_ctx.__enter__()

try:
    # Write all files
    print(f"Temp directory: {project.root}")
    
    project.write_climate_files(season.simulation_start, weather_data)
    project.write_crop_file(crop_index, crop_params)
    project.write_fertility_management_file(input_data.fertility_stress)
    project.write_gwt_file(depth=input_data.gwt_depth, ec=input_data.gwt_ec)
    project.write_soil_file(soil_params)
    project.write_sw0_file(soil_params)
    project.write_calendar_file(season)
    project.write_project_file(season)
    project.write_daily_out_config()
    
    print("\n✅ All files written to temp directory!")
    print(f"\n📁 Temp directory location: {project.root}")
    print("\nDirectory contents:")
    
    # List all files
    for item in sorted(project.root.rglob('*')):
        if item.is_file():
            rel = item.relative_to(project.root)
            size = item.stat().st_size
            print(f"  {rel} ({size} bytes)")
    
    # Copy to permanent location
    output_dir = Path('bmi_test_data_from_python')
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    print(f"\n📦 Copying to {output_dir}...")
    shutil.copytree(project.root, output_dir)
    
    print(f"\n✅ SUCCESS! Data saved to: {output_dir.absolute()}")
    print("\nYou can now use this directory for Fortran tests:")
    print(f"  cd aquacrop/")
    print(f"  rm -rf bmi_test_data")
    print(f"  mv {output_dir} bmi_test_data")
    print(f"  ./test_bmi_complete")
    
finally:
    # Now let it clean up
    project_ctx.__exit__(None, None, None)
    print("\n🗑️  Temp directory cleaned up")