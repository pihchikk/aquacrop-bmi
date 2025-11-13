#!/usr/bin/env python3
"""
Load configuration from JSON scenario files
Allows using existing scenario definitions with the interactive BMI demo
"""

import json
from pathlib import Path
from datetime import datetime


def load_scenario_config(json_file: Path) -> dict:
    """
    Load scenario configuration from JSON file
    
    Returns dict with:
        - latitude, longitude
        - start_date, end_date, planting_date
        - crop_file or crop_ref
        - soil layers
    """
    with open(json_file) as f:
        config = json.load(f)
    
    result = {}
    
    # Location
    if 'point' in config:
        result['latitude'] = config['point']['latitude']
        result['longitude'] = config['point']['longitude']
        if 'altitude' in config['point']:
            result['altitude'] = config['point']['altitude']
    
    # Dates
    if 'seasons' in config and len(config['seasons']) > 0:
        season = config['seasons'][0]
        result['start_date'] = season['simulation_start']
        result['end_date'] = season['simulation_end']
        result['planting_date'] = season.get('planting_date', season['simulation_start'])
    
    # Crop
    if 'crop_file' in config:
        result['crop_file'] = config['crop_file']
    elif 'crop_ref' in config:
        result['crop_ref'] = config['crop_ref']
    
    # Soil
    if 'soil' in config:
        result['soil'] = config['soil']
    elif 'soils' in config and len(config['soils']) > 0:
        result['soil'] = config['soils'][0]
    
    # GWT
    if 'gwt_depth' in config:
        result['gwt_depth'] = config['gwt_depth']
    if 'gwt_ec' in config:
        result['gwt_ec'] = config['gwt_ec']
    
    return result


def print_config(config: dict):
    """Pretty print configuration"""
    print("\n" + "="*70)
    print("LOADED CONFIGURATION")
    print("="*70)
    
    if 'latitude' in config and 'longitude' in config:
        print(f"📍 Location: {config['latitude']:.4f}°N, {config['longitude']:.4f}°E")
    
    if 'start_date' in config and 'end_date' in config:
        print(f"📅 Season: {config['start_date']} to {config['end_date']}")
        if 'planting_date' in config:
            print(f"🌱 Planting: {config['planting_date']}")
    
    if 'crop_file' in config:
        print(f"🌾 Crop: {config['crop_file']}")
    elif 'crop_ref' in config:
        print(f"🌾 Crop: {config['crop_ref']}")
    
    if 'soil' in config:
        soil = config['soil']
        if isinstance(soil, dict):
            if 'sand' in soil:
                print(f"🏔️  Soil texture: Sand={soil.get('sand')}%, Silt={soil.get('silt')}%, Clay={soil.get('clay')}%")
    
    print("="*70)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python config_loader.py <scenario.json>")
        sys.exit(1)
    
    json_file = Path(sys.argv[1])
    if not json_file.exists():
        print(f"❌ File not found: {json_file}")
        sys.exit(1)
    
    config = load_scenario_config(json_file)
    print_config(config)