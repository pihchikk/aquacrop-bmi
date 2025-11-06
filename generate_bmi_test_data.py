#!/usr/bin/env python3
"""
Generate BMI test data for Fortran test_bmi_complete.f90
This replicates the Python preprocessing from project.py
"""

from datetime import date, timedelta
from pathlib import Path
import numpy as np

# Configuration
OUTPUT_DIR = Path("bmi_test_data")
START_DATE = date(2024, 4, 1)  # April 1, 2024
END_DATE = date(2024, 7, 29)   # July 29, 2024 (120 days)
GROWING_START = date(2024, 4, 15)  # Planting date
GROWING_END = date(2024, 7, 15)    # Harvest date

def create_directory_structure():
    """Create the required directory structure"""
    dirs = [
        OUTPUT_DIR / "LIST",
        OUTPUT_DIR / "OUTP",
        OUTPUT_DIR / "SIMUL",
    ]
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created directory structure in {OUTPUT_DIR}")


def write_climate_files():
    """Generate synthetic climate data files"""
    
    # Generate 120 days of synthetic climate data
    n_days = (END_DATE - START_DATE).days + 1
    
    # Synthetic data patterns
    np.random.seed(42)
    
    # Temperature: seasonal pattern
    day_of_year = np.array([(START_DATE + timedelta(i)).timetuple().tm_yday for i in range(n_days)])
    tmin = 15 + 5 * np.sin(2 * np.pi * day_of_year / 365) + np.random.normal(0, 2, n_days)
    tmax = 25 + 8 * np.sin(2 * np.pi * day_of_year / 365) + np.random.normal(0, 2, n_days)
    
    # Rainfall: occasional events
    rainfall = np.random.exponential(2.5, n_days)
    rainfall[np.random.rand(n_days) > 0.3] = 0  # 30% chance of rain
    
    # ET0: correlated with temperature
    et0 = 3.0 + 0.1 * tmax + np.random.normal(0, 0.3, n_days)
    et0 = np.clip(et0, 1.0, 8.0)
    
    # Write Tnx file (Temperature)
    header = f"""  AquaCrop {START_DATE.day:02d}/{START_DATE.month:02d}/{START_DATE.year}  -  Daily File
   1 : Daily Tnx (C) observations
     ==========================================
      Day  Month   Year   Tmin (C)   TMax (C)
"""
    with (OUTPUT_DIR / "project.Tnx").open('w') as f:
        f.write(header)
        current = START_DATE
        for i in range(n_days):
            f.write(f"     {current.day:2d}     {current.month:2d}   {current.year}    {tmin[i]:5.1f}      {tmax[i]:5.1f}\n")
            current += timedelta(days=1)
    
    # Write PLU file (Precipitation)
    header = f"""  AquaCrop {START_DATE.day:02d}/{START_DATE.month:02d}/{START_DATE.year}  -  Daily File
   2 : Daily Rainfall (mm) observations
     ==========================================
      Day  Month   Year   Total Rain (mm)
"""
    with (OUTPUT_DIR / "project.PLU").open('w') as f:
        f.write(header)
        current = START_DATE
        for i in range(n_days):
            f.write(f"     {current.day:2d}     {current.month:2d}   {current.year}    {rainfall[i]:6.1f}\n")
            current += timedelta(days=1)
    
    # Write ETo file (Reference Evapotranspiration)
    header = f"""  AquaCrop {START_DATE.day:02d}/{START_DATE.month:02d}/{START_DATE.year}  -  Daily File
   3 : Daily ETo (mm/day) observations
     ==========================================
      Day  Month   Year   Average ETo (mm/day)
"""
    with (OUTPUT_DIR / "project.ETo").open('w') as f:
        f.write(header)
        current = START_DATE
        for i in range(n_days):
            f.write(f"     {current.day:2d}     {current.month:2d}   {current.year}    {et0[i]:6.2f}\n")
            current += timedelta(days=1)
    
    print(f"✅ Generated {n_days} days of climate data (Tnx, PLU, ETo)")


def write_soil_file():
    """Write soil profile file"""
    content = """  AquaCrop (Version 7.1 - August 2023) - Soil Profile
       12.00  : AquaCrop Version (March 2017)
       90  : CN (Curve Number)
        9  : Readily evaporable water from top layer (mm)
        5  : number of soil horizons
       -9  : variable no longer applicable
  Thickness  Sat   FC    WP     Ksat    Penetrability  Gravel  CRa       CRb           description
     (m)   (vol%) (vol%) (vol%)  (mm/day)      (%)        (%)
  ==============================================================================================
    0.20    50.0  30.0  15.0    1000.0        100         0    -0.586600   0.286000   sandy loam
    0.30    50.0  30.0  15.0    1000.0        100         0    -0.586600   0.286000   sandy loam
    0.30    50.0  30.0  15.0    1000.0        100         0    -0.586600   0.286000   sandy loam
    0.40    45.0  28.0  14.0     800.0        100         0    -0.586600   0.286000   sandy loam
    0.50    45.0  28.0  14.0     800.0        100         0    -0.586600   0.286000   sandy loam
"""
    (OUTPUT_DIR / "project.SOL").write_text(content)
    print("✅ Generated soil file (SOL)")


def write_initial_conditions():
    """Write initial soil water content file"""
    content = """  AquaCrop (Version 7.1 - August 2023) - Soil Water Content
       12.00  : AquaCrop Version (March 2017)
        5  : number of soil layers with WC measurements
  Thickness    WC (vol%)    ECe (dS/m)
     (m)
  ==========================================
         0.20                28.00                  0.00
         0.30                28.00                  0.00
         0.30                28.00                  0.00
         0.40                26.00                  0.00
         0.50                26.00                  0.00
"""
    (OUTPUT_DIR / "project.SW0").write_text(content)
    print("✅ Generated initial conditions (SW0)")


def write_groundwater_file():
    """Write groundwater table file"""
    content = """  AquaCrop (Version 7.1 - August 2023) - Groundwater Table
       12.00  : AquaCrop Version (March 2017)
    2  : Type of groundwater table (fixed (1), or variable (2))
    2.00  : Groundwater table depth (m below surface) at start
    0.00  : Groundwater quality (ECe in dS/m)
"""
    (OUTPUT_DIR / "project.GWT").write_text(content)
    print("✅ Generated groundwater table (GWT)")


def write_management_file():
    """Write field management file"""
    content = """  AquaCrop (Version 7.1 - August 2023) - Field Management
       12.00  : AquaCrop Version (March 2017)
    0.00  : Soil fertility stress (%) - 0% means no fertility stress
"""
    (OUTPUT_DIR / "project.MAN").write_text(content)
    print("✅ Generated management file (MAN)")


def write_calendar_file():
    """Write crop calendar file"""
    growing_doy = GROWING_START.timetuple().tm_yday
    content = f"""  AquaCrop (Version 7.1 - August 2023) - Crop Calendar
       12.00  : AquaCrop Version (March 2017)
    1  : Calendar Type (1 = Time criteria, 2 = GDD criteria)
  {growing_doy}  : Day of year for start of growing season
"""
    (OUTPUT_DIR / "project.CAL").write_text(content)
    print(f"✅ Generated calendar file (CAL) - planting on day {growing_doy}")


def write_crop_file():
    """Write Maize crop parameters"""
    content = """AquaCrop 7.1 (August 2023) - Crop parameters for Maize (grain)
       12.00  : AquaCrop Version (March 2017)
    1  : file type  (1 = crop, 2 = weed)
Maize : Crop name
    1  : Crop type (0 = Leafy, 1 = Fruit/Grain, 2 = Root/Tuber, 3 = Forage)
    1  : Planting method (0 = Sowing, 1 = Transplanting)
   11  : Transfer (days to recover)
   12  : Time from sowing to maximum rooting depth (days)
   13  : Time from sowing to senescence (days)
   14  : Time from sowing to maturity (harvest) (days)
   15  : Length of flowering stage (days)
  -9.000000  : HI building up during flowering stage (days)
  -9.000000  : HI building up during yield formation (days)
  -9.000000  : Duration of linear HI growth (days)
  -9.000000  : Water stress threshold for inhibition of vegetative growth (p)
  -9.000000  : Water stress threshold for inhibition of stomatal conductance (p)
  -9.000000  : Negative effect of water stress on crop growth (% day-1)
  -9.000000  : Positive effect of water stress on crop growth during recovery (% day-1)
  -9.000000  : Adjustment coefficient for calibration of negative water stress (-)
  -9.000000  : Adjustment coefficient for calibration of positive water stress (-)
  -9.000000  : Shape factor for water stress coefficient curve (-)
  -9.000000  : Soil water depletion at full canopy cover (%TAW)
  -9.000000  : Soil water depletion at start of canopy decline (%TAW)
  -9.000000  : Soil water depletion below which yield starts declining (%TAW)
  -9.000000  : Minimum temperature (°C) for crop development
   30.0  : Maximum temperature (°C) for crop development
   12.0  : Base temperature (°C) for crop development
   30.0  : Upper threshold temperature (°C) for crop development
   -9  : Total GDD from sowing to maturity (°C day)
  -9.000000  : Calibration factor for GDD calculation (default = 12.0 °C)
    6.5  : Minimum growing degree days for full canopy development (°C day per day)
  -9.000000  : CGC: relative increase in canopy cover (per day)
    0.98  : Maximum canopy cover (fraction)
    0.30  : Canopy decline coefficient (fraction day-1)
   12.00  : Crop coefficient at maximum canopy cover
    0.15  : Crop coefficient at start of canopy decline
    0.50  : Decline of crop coefficient due to ageing (%/day)
  -9.000000  : Minimum effective rooting depth (m)
    2.30  : Maximum rooting depth (m)
   13  : Number of days from sowing to maximum rooting depth
    0.030  : Shape factor for root zone expansion
    0.050  : Starting depth of root zone (m)
   34.0  : Maximum water extraction by crop per day (mm/day)
    3.00  : Water productivity (WP*) normalized for CO2 and ET0 (gram/m2)
  100  : Adjustment of WP* for atmospheric CO2 concentration (%)
   25  : Reference concentration of CO2 (ppm) - 369 for now, 350 before
   50  : Water productivity during yield formation relative to biomass development (%)
   48  : Harvest Index (reference)
  -9.000000  : Adjustment coefficient for calibration of Harvest Index
   10.00  : Potential size of individual tubers (g)
  -9.000000  : Shape factor of negative water stress on HI
   15.0  : Allowable soil fertility stress (%) for no effect on HI
  -9.000000  : coefficient for translocation of assimilates to grain (%)
  -9.000000  : Adjustment coefficient of HI for restricted vegetative growth (-)
  -9.000000  : percentage of total flowering at which peak flowering occurs
  -9.000000  : percentage of total flowering at which yield formation starts
  -9.000000  : percentage effect on HI of a premature canopy decline
  -9.000000  : percentage of biomass produced in flowering that goes into HI
  -9.000000  : GDD from sowing to anthesis (°C day)
  -9.000000  : GDD from anthesis to HI0 (°C day)
  -9.000000  : Duration of flowering (GDD °C day)
  -9.000000  : CGC (relative increase in canopy cover per growing degree day)
  -9.000000  : CDC (canopy decline coefficient per growing degree day)
  -9.000000  : Extra correction for GDD calculation
"""
    (OUTPUT_DIR / "project.CRO").write_text(content)
    print("✅ Generated crop file (CRO) - Maize")


def write_climate_config():
    """Write main climate configuration file"""
    content = f"""AquaCrop 7.1 (August 2023) - Climate (project)
       12.00  : AquaCrop Version (March 2017)
    1  : Daily records (1 = daily, 2 = 10-daily, 3 = monthly)
    {START_DATE.day}  : First day of simulation
    {START_DATE.month}  : First month of simulation
    {START_DATE.year}  : First year of simulation (1901 if not linked)
    2  : Source of temperature file (1 = *.Tnx, 2 = simulation)
    2  : Source of ETo file (1 = *.ETo, 2 = simulation)
    2  : Source of Rain file (1 = *.PLU, 2 = simulation)
    1  : Method for ETo calculation (1 = FAO Penman-Monteith, 2 = from pan)
project.Tnx
project.ETo
project.PLU
"""
    (OUTPUT_DIR / "project.CLI").write_text(content)
    print("✅ Generated climate config (CLI)")


def write_project_file():
    """Write main project file in LIST directory"""
    sim_start = (START_DATE - date(1901, 1, 1)).days + 1
    sim_end = (END_DATE - date(1901, 1, 1)).days + 1
    grow_start = (GROWING_START - date(1901, 1, 1)).days + 1
    grow_end = (GROWING_END - date(1901, 1, 1)).days + 1
    
    content = f"""AquaCrop 7.1 (August 2023) - project
       12.00  : AquaCrop Version (March 2017)
    {sim_start}  : First day of simulation period - {START_DATE.strftime('%d %b %Y')}
    {sim_end}  : Last day of simulation period - {END_DATE.strftime('%d %b %Y')}
    {grow_start}  : First day of cropping period - {GROWING_START.strftime('%d %b %Y')}
    {grow_end}  : Last day of cropping period - {GROWING_END.strftime('%d %b %Y')}
../project.CLI
../project.Tnx
../project.ETo
../project.PLU
../project.CRO
../project.CAL
../project.SOL
../project.SW0
../project.GWT
../project.MAN
../SIMUL/MaunaLoa.CO2
../SIMUL/DailyResults.SIM
"""
    (OUTPUT_DIR / "LIST" / "project.PRO").write_text(content)
    print(f"✅ Generated project file (PRO)")
    print(f"   Simulation: {START_DATE} to {END_DATE}")
    print(f"   Growing season: {GROWING_START} to {GROWING_END}")


def write_co2_file():
    """Write CO2 concentration file"""
    content = """AquaCrop 7.1 (August 2023) - CO2 Concentration - Mauna Loa
       12.00  : AquaCrop Version (March 2017)
  Year    CO2 (ppm)
  ====================
  2023    419.0
  2024    421.0
  2025    423.0
"""
    (OUTPUT_DIR / "SIMUL" / "MaunaLoa.CO2").write_text(content)
    print("✅ Generated CO2 file")


def write_daily_output_config():
    """Write daily output configuration"""
    content = """AquaCrop 7.1 (August 2023) - Specification of Daily Outputs
       12.00  : AquaCrop Version (March 2017)
    1  : Daily outputs (1 = yes, 0 = no)
"""
    (OUTPUT_DIR / "SIMUL" / "DailyResults.SIM").write_text(content)
    print("✅ Generated daily output config")


def write_list_projects():
    """Write ListProjects.txt file"""
    content = """AquaCrop 7.1 (August 2023) - List of Projects
project.PRO
"""
    (OUTPUT_DIR / "LIST" / "ListProjects.txt").write_text(content)
    print("✅ Generated ListProjects.txt")


def copy_default_files():
    """Copy default simulation files"""
    # DEFAULT.CRO - default crop
    default_cro = """AquaCrop 7.1 (August 2023) - Default Crop
       12.00  : AquaCrop Version (March 2017)
    1  : file type  (1 = crop, 2 = weed)
Default : Crop name
"""
    (OUTPUT_DIR / "SIMUL" / "DEFAULT.CRO").write_text(default_cro)
    
    # DEFAULT.SOL - default soil
    default_sol = """AquaCrop 7.1 (August 2023) - Default Soil
       12.00  : AquaCrop Version (March 2017)
   80  : CN (Curve Number)
    9  : REW (readily evaporable water from top layer, mm)
    1  : number of soil horizons
  Thickness  Sat   FC    WP     Ksat    Penetrability  Gravel  CRa       CRb           description
     (m)   (vol%) (vol%) (vol%)  (mm/day)      (%)        (%)
  ==============================================================================================
    4.00    50.0  30.0  15.0    1000.0        100         0    -0.586600   0.286000   default
"""
    (OUTPUT_DIR / "SIMUL" / "DEFAULT.SOL").write_text(default_sol)
    
    print("✅ Generated default simulation files")


def main():
    """Generate all test data files"""
    print("\n" + "="*70)
    print("  GENERATING BMI TEST DATA FOR FORTRAN TEST")
    print("="*70 + "\n")
    
    create_directory_structure()
    write_climate_files()
    write_soil_file()
    write_initial_conditions()
    write_groundwater_file()
    write_management_file()
    write_calendar_file()
    write_crop_file()
    write_climate_config()
    write_co2_file()
    write_daily_output_config()
    copy_default_files()
    write_list_projects()
    write_project_file()
    
    print("\n" + "="*70)
    print("  ✅ ALL FILES GENERATED SUCCESSFULLY!")
    print("="*70)
    print(f"\nTest data directory: {OUTPUT_DIR.absolute()}")
    print("\nDirectory structure:")
    print("  bmi_test_data/")
    print("  ├── LIST/")
    print("  │   ├── project.PRO")
    print("  │   └── ListProjects.txt")
    print("  ├── OUTP/          (will be created by AquaCrop)")
    print("  ├── SIMUL/")
    print("  │   ├── MaunaLoa.CO2")
    print("  │   ├── DailyResults.SIM")
    print("  │   ├── DEFAULT.CRO")
    print("  │   └── DEFAULT.SOL")
    print("  ├── project.CLI")
    print("  ├── project.Tnx")
    print("  ├── project.ETo")
    print("  ├── project.PLU")
    print("  ├── project.CRO")
    print("  ├── project.SOL")
    print("  ├── project.SW0")
    print("  ├── project.GWT")
    print("  ├── project.MAN")
    print("  └── project.CAL")
    print("\nYou can now run: ./test_bmi_complete")
    print()


if __name__ == "__main__":
    main()
