#!/usr/bin/env python
"""
AquaCrop BMI Simulation Visualization
Runs full simulation and plots crop development over time
"""

import numpy as np
import matplotlib.pyplot as plt
from aquacrop_bmi_babel import AquaCrop

def run_and_visualize():
    """Run AquaCrop simulation and visualize results"""
    
    print("Initializing AquaCrop BMI model...")
    model = AquaCrop()
    config_file = "/mnt/d/KNP/aquacrop-bmi/aquacrop/bmi_test_data/LIST/project.PRO"
    model.initialize(config_file)
    
    # Get simulation info
    start_time = model.get_start_time()
    end_time = model.get_end_time()
    time_step = model.get_time_step()
    n_steps = int((end_time - start_time) / time_step)
    
    print(f"Simulation period: {n_steps} days (Day {start_time:.0f} to {end_time:.0f})")
    print("Running simulation...")
    
    # Storage arrays
    time = []
    canopy_cover = []
    biomass = []
    yield_data = []
    soil_moisture = []
    
    # Run simulation
    dest = np.empty(1, dtype=np.float64)
    
    for step in range(n_steps + 1):
        current_time = model.get_current_time()
        
        # Get current values
        model.get_value("crop__canopy_cover", dest)
        cc = dest[0]
        
        model.get_value("crop__biomass", dest)
        bio = dest[0]
        
        model.get_value("crop__yield", dest)
        yld = dest[0]
        
        model.get_value("soil__moisture", dest)
        sm = dest[0]
        
        # Store results
        time.append(current_time)
        canopy_cover.append(cc)
        biomass.append(bio)
        yield_data.append(yld)
        soil_moisture.append(sm)
        
        # Progress indicator
        if step % 20 == 0:
            print(f"  Day {current_time:.0f}/{end_time:.0f} - CC: {cc:.1f}%, Biomass: {bio:.1f} ton/ha")
        
        # Update to next time step
        if current_time < end_time:
            model.update()
    
    model.finalize()
    print("✓ Simulation complete\n")
    
    # Convert to numpy arrays
    time = np.array(time)
    canopy_cover = np.array(canopy_cover)
    biomass = np.array(biomass)
    yield_data = np.array(yield_data)
    soil_moisture = np.array(soil_moisture)
    
    # Print final statistics
    print("="*60)
    print("FINAL RESULTS")
    print("="*60)
    print(f"Maximum canopy cover:  {np.max(canopy_cover):.2f}%")
    print(f"Final biomass:         {biomass[-1]:.2f} ton/ha")
    print(f"Final yield:           {yield_data[-1]:.2f} ton/ha")
    print(f"Average soil moisture: {np.mean(soil_moisture):.2f}%")
    print()
    
    # Create visualization
    print("Creating plots...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('AquaCrop BMI Simulation Results', fontsize=16, fontweight='bold')
    
    # Plot 1: Canopy Cover
    ax1 = axes[0, 0]
    ax1.plot(time, canopy_cover, 'g-', linewidth=2, label='Canopy Cover')
    ax1.set_xlabel('Time (days)', fontsize=11)
    ax1.set_ylabel('Canopy Cover (%)', fontsize=11)
    ax1.set_title('Crop Canopy Development', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(bottom=0)
    
    # Plot 2: Biomass
    ax2 = axes[0, 1]
    ax2.plot(time, biomass, 'b-', linewidth=2, label='Biomass')
    ax2.set_xlabel('Time (days)', fontsize=11)
    ax2.set_ylabel('Biomass (ton/ha)', fontsize=11)
    ax2.set_title('Biomass Accumulation', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(bottom=0)
    
    # Plot 3: Yield
    ax3 = axes[1, 0]
    ax3.plot(time, yield_data, 'orange', linewidth=2, label='Yield')
    ax3.set_xlabel('Time (days)', fontsize=11)
    ax3.set_ylabel('Yield (ton/ha)', fontsize=11)
    ax3.set_title('Crop Yield Development', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(bottom=0)
    
    # Plot 4: Soil Moisture
    ax4 = axes[1, 1]
    ax4.plot(time, soil_moisture, 'brown', linewidth=2, label='Soil Moisture')
    ax4.set_xlabel('Time (days)', fontsize=11)
    ax4.set_ylabel('Soil Moisture (%)', fontsize=11)
    ax4.set_title('Root Zone Soil Moisture', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim(bottom=0)
    
    plt.tight_layout()
    
    # Save figure
    output_file = 'aquacrop_simulation_results.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Plot saved to: {output_file}")
    
    # Show plot
    plt.show()
    
    return time, canopy_cover, biomass, yield_data, soil_moisture


if __name__ == "__main__":
    try:
        results = run_and_visualize()
        print("\n✅ Visualization complete!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()