CLI_SUB_HEADER = """project
1       : Daily records (1=daily, 2=10-daily and 3=monthly data)
{first_day:<8}: First day of record (1, 11 or 21 for 10-day or 1 for months)
{first_month:<8}: First month of record
{first_year:<8}: First year of record (1901 if not linked to a specific year))

  {{columns:<21}}
=======================
"""


SOL_CONTENT = """project
        7.1                 : AquaCrop Version (August 2023)
{curve_number:<28}: CN (Curve Number)
{rew:<28}: Readily evaporable water from top layer (mm)
{horizon_count:<28}: number of soil horizons
       -9                   : variable no longer applicable
  Thickness  Sat   FC    WP     Ksat   Penetrability  Gravel  CRa       CRb           description
  ---(m)-   ----(vol %)-----  (mm/day)      (%)        (%)    -----------------------------------------
"""


GWT_CONTENT = """project
     7.1   : AquaCrop Version (August 2023)
     1     : groundwater table at fixed depth and with constant salinity

   Day    Depth (m)    ECw (dS/m)
====================================
     1      {depth:.2f}          {ec:.1f}"""


CAL_CONTENT = """project
         7.1  : AquaCrop Version (August 2023)
         0    : The onset of the growing period is fixed on a specific date
        -9    : Day-number (1 ... 366) of the Start of the time window for the onset criterion: Not applicable
        -9    : Length (days) of the time window for the onset criterion: Not applicable
{growing_season_start_doy:<14}: Day-number (1 ... 366) for the onset of the growing period
        -9    : Number of successive days: Not applicable
        -9    : Number of occurrences: Not applicable"""


SW0_CONTENT = """project
    7.1   : AquaCrop Version (August 2023)
   -9.00  : initial canopy cover that can be reached without water stress will be used as default
    0.000 : biomass (ton/ha) produced before the start of the simulation period
   -9.00  : initial effective rooting depth that can be reached without water stress will be used as default
    0.0   : water layer (mm) stored between soil bunds (if present)
    0.00  : electrical conductivity (dS/m) of water layer stored between soil bunds (if present)
    0     : soil water content specified for specific layers
{horizon_count:<10}: number of layers considered

Thickness layer (m)     Water content (vol%)     ECe(dS/m)
==============================================================
"""


MAN_CONTENT = """Soil fertility stress
     7.1       : AquaCrop Version (August 2023)
     0         : percentage (%) of ground surface covered by mulches IN growing period
    50         : effect (%) of mulches on reduction of soil evaporation
{fertility_stress:<15.0f}: Degree of soil fertility stress (%) - Effect is crop specific
     0.00      : height (m) of soil bunds
     0         : surface runoff NOT affected by field surface practices
     0         : N/A (surface runoff is not affected or completely prevented)
     0         : relative cover of weeds at canopy closure (%)
     0         : increase of relative cover of weeds in mid-season (+%)
   100.00      : shape factor of the CC expansion function in a weed infested field
   100         : replacement (%) by weeds of the self-thinned part of the CC - only for perennials
     0         : Multiple cuttings are not considered
    30         : Canopy cover (%) after cutting - not considered
    20         : Increase (%) of Canopy Growth Coefficient (CGC) after cutting - not considered
     1         : First day of window for multiple cuttings (1 = start of growth cycle)
    -9         : Number of days in window for multiple cuttings (-9 = total growth cycle)
    -9         : Timing of multiple cuttings: Not Applicable
     0         : Time criterion: Not Applicable
     0         : final harvest at crop maturity is not considered
    -9         : Start of the growing cycle is Day 1 in list of cuttings"""


PRO_CONTENT = """project
      7.1       : AquaCrop Version (August 2023)
      1         : Year number of cultivation (Seeding/planting year)
{simulation_start:<16}: First day of simulation period
{simulation_end:<16}: Last day of simulation period
{growing_season_start:<16}: First day of cropping period
{growing_season_end:<16}: Last day of cropping period
-- 1. Climate (CLI) file
   project.CLI
   './'
   1.1 Temperature (Tnx or TMP) file
   project.Tnx
   './'
   1.2 Reference ET (ETo) file
   project.ETo
   './'
   1.3 Rain (PLU) file
   project.PLU
   './'
   1.4 Atmospheric CO2 concentration (CO2) file
   MaunaLoa.CO2
   'SIMUL/'
-- 2. Calendar (CAL) file
   project.CAL
   './'
-- 3. Crop (CRO) file
   project.CRO
   './'
-- 4. Irrigation management (IRR) file
   (None)
   (None)
-- 5. Field management (MAN) file
   project.MAN
   './'
-- 6. Soil profile (SOL) file
   project.SOL
   './'
-- 7. Groundwater table (GWT) file
   project.GWT
   './'
-- 8. Initial conditions (SW0) file
   project.SW0
   './'
-- 9. Off-season conditions (OFF) file
   (None)
   (None)
-- 10. Field data (OBS) file
   (None)
   (None)
"""

OUT_DAILY_CONTENT = """ 1 : Various parameters of the soil water balance
 2 : Crop development and production
 3 : Soil water content in the soil profile and root zone
 4 : Soil salinity in the soil profile and root zone
 5 : Soil water content at various depths of the soil profile
 6 : Soil salinity at various depths of the soil profile
 7 : Climate input parameters
"""
