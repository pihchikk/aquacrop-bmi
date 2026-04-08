"""
Minimal BMI Demo - Shows BMI advantages with live visualization
Runs test_bmi_complete and visualizes output in real-time
"""

import subprocess
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import re
from pathlib import Path


class LiveBMIVisualizer:
    """Real-time visualization of BMI test output"""
    
    def __init__(self):
        # Create figure with dark theme
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(16, 9))
        self.fig.patch.set_facecolor('#1e1e1e')
        
        # Create 2x2 grid
        gs = self.fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # Create subplots
        self.ax1 = self.fig.add_subplot(gs[0, 0])  # Canopy Cover
        self.ax2 = self.fig.add_subplot(gs[0, 1])  # Biomass
        self.ax3 = self.fig.add_subplot(gs[1, 0])  # Soil Water
        self.ax4 = self.fig.add_subplot(gs[1, 1])  # All combined
        
        # Data storage
        self.days = []
        self.cc = []
        self.biomass = []
        self.yield_vals = []
        self.soil_water = []
        
        # Setup plots
        self.setup_plots()
        
        # Title
        self.fig.suptitle('BMI AquaCrop - Live Simulation (Step-by-Step Control)', 
                         fontsize=16, fontweight='bold', color='#4CAF50')
        
    def setup_plots(self):
        """Initialize plot styling"""
        
        # Plot 1: Canopy Cover
        self.line1, = self.ax1.plot([], [], color='#4CAF50', linewidth=3, label='Canopy Cover')
        self.ax1.set_title('🌱 Canopy Cover Development', fontsize=12, fontweight='bold')
        self.ax1.set_xlabel('Day', fontsize=10)
        self.ax1.set_ylabel('Coverage (%)', fontsize=10)
        self.ax1.grid(True, alpha=0.2, linestyle='--')
        self.ax1.set_xlim(0, 120)
        self.ax1.set_ylim(0, 100)
        self.ax1.legend()
        
        # Plot 2: Biomass
        self.line2, = self.ax2.plot([], [], color='#2196F3', linewidth=3, label='Biomass')
        self.ax2.set_title('📊 Biomass Accumulation', fontsize=12, fontweight='bold')
        self.ax2.set_xlabel('Day', fontsize=10)
        self.ax2.set_ylabel('Biomass (t/ha)', fontsize=10)
        self.ax2.grid(True, alpha=0.2, linestyle='--')
        self.ax2.set_xlim(0, 120)
        self.ax2.set_ylim(0, 20)
        self.ax2.legend()
        
        # Plot 3: Soil Water
        self.line3, = self.ax3.plot([], [], color='#00BCD4', linewidth=3, label='Soil Moisture')
        self.ax3.axhline(y=40, color='#FF5722', linestyle='--', linewidth=2, 
                        alpha=0.7, label='Stress Threshold')
        self.ax3.set_title('💧 Soil Water Content', fontsize=12, fontweight='bold')
        self.ax3.set_xlabel('Day', fontsize=10)
        self.ax3.set_ylabel('Moisture (%)', fontsize=10)
        self.ax3.grid(True, alpha=0.2, linestyle='--')
        self.ax3.set_xlim(0, 120)
        self.ax3.set_ylim(0, 100)
        self.ax3.legend()
        
        # Plot 4: Combined view
        self.line4a, = self.ax4.plot([], [], color='#4CAF50', linewidth=2, label='CC (%)')
        self.line4b, = self.ax4.plot([], [], color='#2196F3', linewidth=2, 
                                     linestyle='--', label='Biomass (×5)')
        self.line4c, = self.ax4.plot([], [], color='#FF9800', linewidth=2, 
                                     linestyle=':', label='Yield (×10)')
        self.ax4.set_title('🌾 Integrated View', fontsize=12, fontweight='bold')
        self.ax4.set_xlabel('Day', fontsize=10)
        self.ax4.set_ylabel('Normalized Values', fontsize=10)
        self.ax4.grid(True, alpha=0.2, linestyle='--')
        self.ax4.set_xlim(0, 120)
        self.ax4.set_ylim(0, 100)
        self.ax4.legend(loc='upper left')
        
        # Info box
        self.info_text = self.fig.text(
            0.5, 0.96, 
            '⏳ Starting BMI simulation...', 
            ha='center', 
            fontsize=11,
            bbox=dict(boxstyle='round', facecolor='#333333', alpha=0.8)
        )
        
    def parse_line(self, line):
        """Parse output line from Fortran test"""
        # Match pattern like: "  5 |  18.45 |   0.456 |  0.00 |    55.23"
        match = re.search(r'\s*(\d+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)', line)
        if match:
            return {
                'day': int(match.group(1)),
                'cc': float(match.group(2)),
                'biomass': float(match.group(3)),
                'yield': float(match.group(4)),
                'soil_water': float(match.group(5))
            }
        return None
        
    def update_frame(self, frame):
        """Animation update function"""
        # Try to read next line from process
        if hasattr(self, 'process') and self.process.poll() is None:
            try:
                line = self.process.stdout.readline()
                if line:
                    data = self.parse_line(line)
                    if data:
                        # Add data
                        self.days.append(data['day'])
                        self.cc.append(data['cc'])
                        self.biomass.append(data['biomass'])
                        self.yield_vals.append(data['yield'])
                        self.soil_water.append(data['soil_water'])
                        
                        # Update plots
                        self.line1.set_data(self.days, self.cc)
                        self.line2.set_data(self.days, self.biomass)
                        self.line3.set_data(self.days, self.soil_water)
                        
                        # Combined plot (normalized)
                        self.line4a.set_data(self.days, self.cc)
                        biomass_norm = [b * 5 for b in self.biomass]
                        self.line4b.set_data(self.days, biomass_norm)
                        yield_norm = [y * 10 for y in self.yield_vals]
                        self.line4c.set_data(self.days, yield_norm)
                        
                        # Update info
                        stress_status = "⚠️ STRESS" if data['soil_water'] < 40 else "✅ OK"
                        self.info_text.set_text(
                            f"Day {data['day']} | CC: {data['cc']:.1f}% | "
                            f"Biomass: {data['biomass']:.2f} t/ha | "
                            f"Soil: {data['soil_water']:.1f}% {stress_status}"
                        )
                        
                        # Highlight stress periods
                        if data['soil_water'] < 40:
                            self.info_text.get_bbox_patch().set_facecolor('#8B0000')
                        else:
                            self.info_text.get_bbox_patch().set_facecolor('#1B5E20')
                            
            except:
                pass
        else:
            if hasattr(self, 'process'):
                self.info_text.set_text('✓ Simulation Complete!')
                self.info_text.get_bbox_patch().set_facecolor('#1B5E20')
                
        return (self.line1, self.line2, self.line3, 
                self.line4a, self.line4b, self.line4c, self.info_text)
        
    def run(self):
        """Run the visualization"""
        
        # Check if executable exists
        if not Path('./test_bmi_complete').exists():
            print("\n❌ Error: test_bmi_complete not found!")
            print("\nPlease compile first:")
            print("  make bmi")
            print("  make test_bmi_complete")
            return
            
        print("\n" + "=" * 70)
        print("  BMI AquaCrop - Live Interactive Demonstration")
        print("=" * 70)
        print("\n🚀 Starting BMI simulation...")
        print("📊 Watch the real-time updates showing BMI advantages:")
        print("   • Step-by-step control (update() function)")
        print("   • Real-time data access (get_value() function)")
        print("   • Interactive monitoring of model state")
        print("\n⏱️  Each update represents ONE BMI step (one day)")
        print("=" * 70 + "\n")
        
        # Start the process
        self.process = subprocess.Popen(
            ['./test_bmi_complete'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        # Create animation
        anim = FuncAnimation(
            self.fig, 
            self.update_frame, 
            interval=100,  # Update every 100ms
            blit=True,
            cache_frame_data=False
        )
        
        plt.show()
        
        # Cleanup
        if self.process.poll() is None:
            self.process.terminate()


def main():
    """Main entry point"""
    
    print("\n" + "🌱" * 35)
    print("\n  BMI AquaCrop Interactive Visualization")
    print("  Demonstrates BMI advantages with live data\n")
    print("🌱" * 35 + "\n")
    
    visualizer = LiveBMIVisualizer()
    visualizer.run()
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
