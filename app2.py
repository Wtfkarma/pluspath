import os
import pandas as pd
import numpy as np
from glob import glob
import matplotlib.pyplot as plt
from sklearn.neighbors import KernelDensity
from scipy.signal import find_peaks
from collections import defaultdict

class TrafficDataAnalyzer:
    def __init__(self, base_path, output_dir="output"):
        self.base_path = base_path
        self.output_dir = os.path.join(base_path, output_dir)
        self.all_wait_times = defaultdict(list)
        self.arrival_times = []
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
    def find_tripinfo_files(self):
        """Locate all tripinfo files in output subdirectories"""
        search_path = os.path.join(self.base_path, "OUTput", "simulation_*", "tripinfo.xlsx")
        files = glob(search_path)
        
        # Also look for XML files if Excel files are empty
        if not files:
            search_path = os.path.join(self.base_path, "OUTput", "simulation_*", "tripinfo.xml")
            files = glob(search_path)
        return files

    def analyze_all_simulations(self):
        """Process all found tripinfo files"""
        tripinfo_files = self.find_tripinfo_files()
        
        if not tripinfo_files:
            raise FileNotFoundError(f"No tripinfo files found in {self.base_path}")
        
        for file_path in tripinfo_files:
            self._analyze_single_file(file_path)
        
        if not self.arrival_times:
            raise ValueError("No valid arrival time data found in any files")
        
        self._generate_optimization_report()

    def _analyze_single_file(self, file_path):
        """Process one tripinfo file"""
        try:
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:  # Assume XML
                df = pd.read_xml(file_path)
            
            # Check for required columns
            required_cols = {'route', 'waiting_time', 'fuel_consumption'}
            if not required_cols.issubset(df.columns):
                print(f"Skipping {file_path}: Missing required columns")
                return
                
            # Extract waiting times and routes
            for _, row in df.iterrows():
                try:
                    route = str(row['route'])
                    wait_time = float(row['waiting_time'])
                    self.all_wait_times[route].append(wait_time)
                    
                    # Record arrival times for KDE analysis
                    fuel_time = float(row['fuel_consumption'])
                    self.arrival_times.append(fuel_time)
                except (ValueError, KeyError) as e:
                    print(f"Error processing row in {file_path}: {e}")
                    continue
                
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")

    def _generate_optimization_report(self):
        """Create optimization recommendations"""
        if not self.all_wait_times:
            raise ValueError("No valid waiting time data found")
            
        # Calculate average wait times per route
        self.avg_waits = {route: np.mean(times) for route, times in self.all_wait_times.items()}
        
        # Identify problematic routes (top 20% worst)
        sorted_routes = sorted(self.avg_waits.items(), key=lambda x: x[1], reverse=True)
        self.problem_routes = sorted_routes[:max(1, len(sorted_routes)//5)]  # Ensure at least 1
        
        # Generate KDE plot only if we have data
        if self.arrival_times:
            self._create_kde_plot()
        
        # Print recommendations
        print("\nOptimization Recommendations:")
        print("============================")
        for route, wait in self.problem_routes:
            direction = self._get_direction(route)
            suggested_time = min(90, 30 * (1 + wait/45))  # Cap at 90 seconds
            print(f"{direction} approach: Current avg wait {wait:.1f}s → Suggest green time {suggested_time:.1f}s")

    def _get_direction(self, route):
        """Determine direction from route edges"""
        first_edge = str(route).split()[0].lower()
        if 'north' in first_edge or 'south' in first_edge:
            return "North-South"
        return "East-West"

    def _create_kde_plot(self):
        """Generate arrival time density plot"""
        plt.figure(figsize=(12, 6))
        
        # Convert to seconds in day
        times = np.array(self.arrival_times) % 86400
        
        # KDE calculation
        try:
            kde = KernelDensity(bandwidth=300, kernel='gaussian')
            kde.fit(times.reshape(-1, 1))
            x_grid = np.linspace(0, 86400, 1000)
            log_dens = kde.score_samples(x_grid.reshape(-1, 1))
            densities = np.exp(log_dens)
            
            # Find peaks
            peaks, _ = find_peaks(densities, height=0.00001, distance=3600)
            
            # Plotting
            plt.fill_between(x_grid, densities, alpha=0.3, label='Traffic Density')
            plt.plot(x_grid[peaks], densities[peaks], 'ro', label='Peak Times')
            
            # Formatting
            plt.title('Vehicle Arrival Time Distribution (KDE)')
            plt.xlabel('Time of Day')
            plt.ylabel('Density')
            hour_ticks = np.arange(0, 86401, 10800)  # Every 3 hours
            plt.xticks(hour_ticks, [f'{h//3600:02d}:00' for h in hour_ticks])
            plt.legend()
            plt.grid(alpha=0.3)
            
            # Save plot to output directory
            plot_path = os.path.join(self.output_dir, "arrival_patterns.png")
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"\nSaved KDE plot to {plot_path}")
        except Exception as e:
            print(f"Could not generate KDE plot: {str(e)}")

    def generate_tls_program(self):
        """Create SUMO-compatible TLS program"""
        if not hasattr(self, 'problem_routes'):
            raise ValueError("No optimization data available")
            
        tls_program = f"""<tlLogic id="optimized_signal" type="static" programID="optimized" offset="0">
    <phase duration="{self._get_phase_duration('North-South')}" state="GGGgrrrrGGGgrrrr"/>
    <phase duration="3" state="yyyygrrryyyygrrr"/>
    <phase duration="{self._get_phase_duration('East-West')}" state="rrrrGGGgrrrrGGGg"/>
    <phase duration="3" state="rrrryyyyrrrryyyy"/>
</tlLogic>"""
        
        output_path = os.path.join(self.output_dir, "optimized_tls.add.xml")
        with open(output_path, 'w') as f:
            f.write(tls_program)
        
        print(f"\nGenerated optimized TLS program at {output_path}")

    def _get_phase_duration(self, direction):
        """Calculate phase duration based on analysis"""
        base_time = 30
        for route, wait in self.problem_routes:
            if direction == self._get_direction(route):
                return str(min(90, base_time * (1 + wait/45)))
        return str(base_time)

if __name__ == "__main__":
    try:
        # Configure with your base path
        base_path = r"C:/Users/anura/OneDrive/Desktop/PLUS PATH"
        analyzer = TrafficDataAnalyzer(base_path, output_dir="analysis_output")
        
        # Process all simulations
        analyzer.analyze_all_simulations()
        
        # Generate outputs
        analyzer.generate_tls_program()
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Please check that:")
        print("1. Your tripinfo files exist and are accessible")
        print("2. The files contain the required columns: 'route', 'waitingTime', 'depart'")
        print("3. The files contain valid numerical data")