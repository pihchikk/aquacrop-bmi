import os
os.environ['OPEN_ELEVATION_URL'] = 'https://api.esoil.ru/open-elevation/v1/lookup'
os.environ['ROSETTA_URL'] = 'https://api.esoil.ru/rosetta/3'

from src.aquacrop_bmi.bmi_aquacrop import BmiAquaCrop
from aquacrop_bmi.bmi_aquacrop import BmiAquaCrop
from aquacrop_bmi.data import specs
    
model = BmiAquaCrop()
model.initialize("src/aquacrop_bmi/examples/scenarios-simulation.json")

from aquacrop_bmi.bmi_aquacrop import BmiAquaCrop

print(f"Simulating {model.get_end_time():.0f} days...")

# Run full simulation
while model.get_current_time() < model.get_end_time():
    model.update()
    
    # Print progress every 30 days
    if int(model.get_current_time()) % 30 == 0:
        day = int(model.get_current_time())
        canopy = model.get_value_ptr('crop__canopy_cover')[0]
        biomass = model.get_value_ptr('crop__biomass')[0]
        print(f"Day {day}: Canopy={canopy:.1f}%, Biomass={biomass:.2f} t/ha")

# Final results
print(f"\n=== Final Results ===")
print(f"Yield: {model.get_value_ptr('crop__yield')[0]:.2f} t/ha")
print(f"Biomass: {model.get_value_ptr('crop__biomass')[0]:.2f} t/ha")
print(f"Canopy: {model.get_value_ptr('crop__canopy_cover')[0]:.1f}%")

model.finalize()