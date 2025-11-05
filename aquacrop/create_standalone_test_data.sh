#!/bin/bash
# Standalone BMI Test Data Generator
# No Python required - pure bash script to create AquaCrop data files

TESTDIR="bmi_standalone_test"
cd "$(dirname "$0")"

echo "Creating standalone BMI test data in $TESTDIR/"

# Create directory structure
mkdir -p "$TESTDIR"/{LIST,OUTP,SIMUL}

# Copy existing files
cp ../src/aquacrop_bmi/data/crops/Maize.CRO "$TESTDIR/"
cp ../src/aquacrop_bmi/data/default/SIMUL/* "$TESTDIR/SIMUL/"

# Calculate dates (days since 1900-12-31)
# April 1, 2024 = 45017
# July 30, 2024 = 45137
START_DAY=45017
END_DAY=45137
GROW_START=45026  # April 10
GROW_END=45132    # July 25
DAYS=$((END_DAY - START_DAY + 1))  # 121 days

echo "Simulation: $DAYS days (April 1 - July 30, 2024)"

# Create climate file header
cat > "$TESTDIR/project.CLI" << 'EOF'
project
       7.1  : AquaCrop Version (August 2023)
project.Tnx
project.ETo
project.PLU
MaunaLoa.CO2
EOF

# Create temperature file (Tnx)
cat > "$TESTDIR/project.Tnx" << 'EOF'
project
1       : Daily records
1       : First day
4       : First month (April)
2024    : First year

  Tmin   Tmax
  (C)    (C)
=================
EOF

# Generate 121 days of temperature data
for i in $(seq 1 $DAYS); do
    TMIN=$(echo "scale=1; 10 + ($i * 0.1)" | bc)
    TMAX=$(echo "scale=1; 20 + ($i * 0.1)" | bc)
    echo "$TMIN  $TMAX" >> "$TESTDIR/project.Tnx"
done

# Create ETo file
cat > "$TESTDIR/project.ETo" << 'EOF'
project
1       : Daily records
1       : First day
4       : First month (April)
2024    : First year

  ETo
 (mm/day)
=========
EOF

for i in $(seq 1 $DAYS); do
    ETO=$(echo "scale=1; 4 + ($i * 0.02)" | bc)
    echo "$ETO" >> "$TESTDIR/project.ETo"
done

# Create rainfall file
cat > "$TESTDIR/project.PLU" << 'EOF'
project
1       : Daily records
1       : First day
4       : First month (April)
2024    : First year

 Rainfall
   (mm)
==========
EOF

for i in $(seq 1 $DAYS); do
    # Random rain every 10 days
    if [ $((i % 10)) -eq 0 ]; then
        echo "15.0" >> "$TESTDIR/project.PLU"
    else
        echo "0.0" >> "$TESTDIR/project.PLU"
    fi
done

# Create soil file
cat > "$TESTDIR/project.SOL" << 'EOF'
project
        7.1                 : AquaCrop Version (August 2023)
61                          : CN (Curve Number)
9                           : Readily evaporable water (mm)
3                           : number of soil horizons
       -9                   : variable no longer applicable
  Thickness  Sat   FC    WP     Ksat   Penetrability  Gravel  CRa       CRb           description
  ---(m)-   ----(vol %)-----  (mm/day)      (%)        (%)    -----------------------------------------
  0.30      48.0  30.0  15.0   500.0         100         0    0.048129  0.132845   SandyLoam
  0.50      46.0  28.0  14.0   400.0         100         0    0.048129  0.132845   SandyLoam
  1.20      44.0  26.0  13.0   300.0         100         0    0.048129  0.132845   SandyLoam
EOF

# Create initial water content file
cat > "$TESTDIR/project.SW0" << 'EOF'
project
    7.1   : AquaCrop Version (August 2023)
   -9.00  : initial canopy cover (default)
    0.000 : biomass (ton/ha)
   -9.00  : initial rooting depth (default)
    0.0   : water layer between bunds (mm)
    0.00  : EC water layer (dS/m)
    0     : soil water content for specific layers
3         : number of layers

Thickness (m)     WC (vol%)     ECe(dS/m)
==========================================
         0.30                30.00                  0.00
         0.50                28.00                  0.00
         1.20                26.00                  0.00
EOF

# Create groundwater table file
cat > "$TESTDIR/project.GWT" << 'EOF'
project
     7.1   : AquaCrop Version (August 2023)
     1     : fixed depth, constant salinity

   Day    Depth (m)    ECw (dS/m)
====================================
     1      10.00          0.0
EOF

# Create management file
cat > "$TESTDIR/project.MAN" << 'EOF'
project
     7.1       : AquaCrop Version (August 2023)
     0         : mulches cover (%)
    50         : mulch effect on evaporation (%)
0              : fertility stress (%)
     0.00      : bund height (m)
     0         : surface runoff affected
     0         : N/A
     0         : weed cover at canopy closure (%)
     0         : weed increase mid-season (%)
   100.00      : CC expansion weed factor
   100         : weed replacement of thinned CC (%)
     0         : multiple cuttings
    30         : CC after cutting (%)
    20         : CGC increase after cutting (%)
     1         : first day cutting window
    -9         : days in cutting window
    -9         : cutting timing
     0         : time criterion
     0         : final harvest at maturity
    -9         : start growing cycle
EOF

# Create calendar file
cat > "$TESTDIR/project.CAL" << 'EOF'
project
         7.1  : AquaCrop Version (August 2023)
         0    : fixed date onset
        -9    : start time window
        -9    : length time window
100           : onset day number (April 10 = day 100)
        -9    : successive days
        -9    : occurrences
EOF

# Create daily output configuration
cat > "$TESTDIR/SIMUL/DailyResults.SIM" << 'EOF'
 1 : Various parameters of the soil water balance
 2 : Crop development and production
 3 : Soil water content in the soil profile and root zone
 4 : Soil salinity in the soil profile and root zone
 5 : Soil water content at various depths
 6 : Soil salinity at various depths
 7 : Climate input parameters
EOF

# Create main project file in LIST directory
cat > "$TESTDIR/LIST/project.PRO" << EOF
project
      7.1       : AquaCrop Version (August 2023)
      1         : Year 1
$START_DAY    : First day simulation ($START_DAY = April 1, 2024)
$END_DAY      : Last day simulation ($END_DAY = July 30, 2024)
$GROW_START   : First day cropping ($GROW_START = April 10, 2024)
$GROW_END     : Last day cropping ($GROW_END = July 25, 2024)
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
   1.4 CO2 file
   MaunaLoa.CO2
   'SIMUL/'
-- 2. Calendar (CAL) file
   project.CAL
   './'
-- 3. Crop (CRO) file
   Maize.CRO
   './'
-- 4. Irrigation (IRR) file
   (None)
   (None)
-- 5. Management (MAN) file
   project.MAN
   './'
-- 6. Soil (SOL) file
   project.SOL
   './'
-- 7. Groundwater (GWT) file
   project.GWT
   './'
-- 8. Initial conditions (SW0) file
   project.SW0
   './'
-- 9. Off-season (OFF) file
   (None)
   (None)
-- 10. Field data (OBS) file
   (None)
   (None)
EOF

# Create list of projects
cat > "$TESTDIR/LIST/ListProjects.txt" << 'EOF'
project.PRO
EOF

echo "✅ Created all data files ($DAYS days of climate data)"
echo ""
echo "Files created in $TESTDIR/:"
find "$TESTDIR" -type f | sort

echo ""
echo "✅ Ready for BMI testing!"
echo "   Test program should use: $TESTDIR/LIST/project.PRO"
