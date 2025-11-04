cat > test_clone.PRO << 'EOF'
*-------------------------------------------------------------
* AquaCrop Model - Input file for Clone run
*-------------------------------------------------------------
  7.1       : AquaCrop Version (August 2023)
Wheat test simulation from JSON config
  1         : Daily time step
  2         : Surface drip irrigation
  0         : No subsurface irrigation
  0         : No use of groundwater
  1         : Wheat crop (using Wheat.CRO)
  1         : Develop. (days), no water stress
  1 4 2011  : Start of simulation period (day month year) - from your JSON
 15 9 2011  : End of simulation period
  1         : Initial soil water content at field capacity
  0 0 0     : No salinity stress
  9         : Fertility stress (from your JSON)
  1         : Default CO2 concentration
  0         : No soil fertility decline
/mnt/d/KNP/aquacrop-bmi/src/aquacrop_bmi/data/default/project.CLI  : Climate data file
/mnt/d/KNP/aquacrop-bmi/src/aquacrop_bmi/data/crops/Wheat.CRO      : Crop file
/mnt/d/KNP/aquacrop-bmi/aquacrop/test_soil.SOL    : Soil file
  0         : No off-season conditions
EOF