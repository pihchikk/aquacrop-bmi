"""
Demo: Using proper BMI wrapper with multiple seasons.

Shows how to:
1. Load ANY scenario type (crop-calibration, fertility-stress, scenarios-simulation, simulation-data)
2. Run through multiple seasons using reinitialize_next_season()
3. Compare with single-season baseline runner
"""

import sys
import numpy as np
from pathlib import Path

# Import proper BMI wrapper
from bmi_aquacrop_proper import BmiAquaCrop


def run_all_seasons(scenario_file: Path):
    """
    Run simulation through ALL seasons and soils in scenario.
    
    Unlike simple_baseline_runner.py which only does first season,
    this loops through all combinations.
    """
    
    print("=" * 80)
    print(" " * 20 + "MULTI-SEASON BMI DEMO")
    print("=" * 80)
    print(f"\nScenario: {scenario_file.name}\n")
    
    # Initialize BMI
    model = BmiAquaCrop()
    model.initialize(str(scenario_file))
    
    all_results = []
    season_idx = 0
    soil_idx = 0
    
    dest = np.empty(1, dtype=np.float64)
    
    while True:
        season_idx += 1
        print(f"\n{'='*80}")
        print(f"SEASON {season_idx}")
        print(f"{'='*80}")
        
        # Run current season
        start_time = model.get_start_time()
        end_time = model.get_end_time()
        n_steps = int(end_time - start_time)
        
        print(f"Days: {n_steps}, Start: {start_time}, End: {end_time}")
        
        results = {
            'season': season_idx,
            'days': [],
            'canopy_cover': [],
            'biomass': [],
            'yield': [],
            'soil_moisture': [],
        }
        
        # Step through season
        for step in range(n_steps + 1):
            current_time = model.get_current_time()
            
            # Get values
            model.get_value("crop__canopy_cover", dest)
            cc = dest[0]
            
            model.get_value("crop__biomass", dest)
            bio = dest[0]
            
            model.get_value("crop__yield", dest)
            yld = dest[0]
            
            model.get_value("soil__moisture", dest)
            moisture = dest[0]
            
            # Store
            results['days'].append(current_time)
            results['canopy_cover'].append(cc)
            results['biomass'].append(bio)
            results['yield'].append(yld)
            results['soil_moisture'].append(moisture)
            
            # Progress
            if step % 30 == 0 or step == n_steps:
                print(f"  Day {int(current_time):3d}: CC={cc:5.1f}% "
                      f"Bio={bio:5.2f}t/ha Yield={yld:5.2f}t/ha")
            
            # Update
            if current_time < end_time:
                model.update()
        
        # Save season results
        all_results.append(results)
        
        print(f"\n✓ Season {season_idx} complete:")
        print(f"  Final Yield: {results['yield'][-1]:.2f} t/ha")
        print(f"  Final Biomass: {results['biomass'][-1]:.2f} t/ha")
        print(f"  Peak CC: {max(results['canopy_cover']):.1f}%")
        
        # Try next season
        if not model.reinitialize_next_season():
            print("\n✓ All seasons complete!")
            break
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total seasons simulated: {len(all_results)}")
    
    for i, r in enumerate(all_results, 1):
        print(f"\nSeason {i}:")
        print(f"  Yield: {r['yield'][-1]:6.2f} t/ha")
        print(f"  Biomass: {r['biomass'][-1]:6.2f} t/ha")
        print(f"  Peak CC: {max(r['canopy_cover']):5.1f}%")
        print(f"  Avg Moisture: {np.mean(r['soil_moisture']):5.1f} mm")
    
    # Calculate average
    avg_yield = np.mean([r['yield'][-1] for r in all_results])
    print(f"\nAverage Yield: {avg_yield:.2f} t/ha")
    
    return all_results


def run_with_interventions(scenario_file: Path):
    """
    Demo: Apply interventions during simulation.
    
    Shows that BMI setters ACTUALLY WORK because we're using
    Fortran BMI backend, not batch processing.
    """
    
    print("\n" + "=" * 80)
    print(" " * 20 + "WITH INTERVENTIONS DEMO")
    print("=" * 80)
    print(f"\nScenario: {scenario_file.name}")
    print("Will apply irrigation on day 50\n")
    
    model = BmiAquaCrop()
    model.initialize(str(scenario_file))
    
    start_time = model.get_start_time()
    end_time = model.get_end_time()
    n_steps = int(end_time - start_time)
    
    dest = np.empty(1, dtype=np.float64)
    src = np.array([50.0], dtype=np.float64)  # 50mm irrigation
    
    irrigation_applied = False
    
    for step in range(n_steps + 1):
        current_time = model.get_current_time()
        
        # INTERVENTION: Apply irrigation on day 50
        if step == 50 and not irrigation_applied:
            print(f"\n🚿 APPLYING IRRIGATION: 50mm on day {int(current_time)}")
            model.set_value("management__irrigation_amount", src)
            irrigation_applied = True
        
        # Get values
        model.get_value("crop__yield", dest)
        yld = dest[0]
        
        model.get_value("soil__moisture", dest)
        moisture = dest[0]
        
        # Show progress
        if step % 20 == 0 or step == 50 or step == n_steps:
            mark = " 🚿" if step == 50 else ""
            print(f"  Day {int(current_time):3d}: Yield={yld:5.2f}t/ha "
                  f"Moisture={moisture:6.1f}mm{mark}")
        
        # Update
        if current_time < end_time:
            model.update()
    
    print(f"\n✓ Final Yield: {yld:.2f} t/ha")
    
    model.finalize()


def main():
    if len(sys.argv) < 2:
        print("Usage: python bmi_demo_multiseason.py <scenario.json>")
        print("\nExamples:")
        print("  python bmi_demo_multiseason.py scenarios/scenarios-simulation.json")
        print("  python bmi_demo_multiseason.py scenarios/AquacropSimulationData.json")
        return 1
    
    scenario_file = Path(sys.argv[1]).resolve()
    
    if not scenario_file.exists():
        print(f"❌ File not found: {scenario_file}")
        return 1
    
    try:
        # Demo 1: Run all seasons
        results = run_all_seasons(scenario_file)
        
        # Demo 2: Run with interventions (first season only)
        print("\n" + "=" * 80)
        input("Press Enter to run intervention demo...")
        run_with_interventions(scenario_file)
        
        print("\n✓ All demos complete!\n")
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
