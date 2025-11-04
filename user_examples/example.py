"""Simple BMI AquaCrop example."""

from aquacrop_bmi.bmi_aquacrop import BmiAquaCrop
from pathlib import Path

model = BmiAquaCrop()
config_path = Path(__file__).parent / "config.yaml"
model.initialize(str(config_path))

print(f"Model: {model.get_component_name()}")
print(f"Time: {model.get_start_time():.0f} to {model.get_end_time():.0f} days\n")

for _ in range(10):
    model.update()
    day = int(model.get_current_time())
    yield_val = model.get_value_ptr("crop__yield")[0]
    print(f"Day {day}: Yield = {yield_val:.2f} t/ha")

model.finalize()
