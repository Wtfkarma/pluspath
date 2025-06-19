#!/usr/bin/env python
import os
import traci
from adaptive_tls import AdaptiveTrafficLight
import time
from datetime import datetime
import pandas as pd
import traceback
import uuid
import json
import glob

class SimulationController:
    # Class-level constants for path management
    BASE_PATH = os.path.normpath("C:/Users/anura/OneDrive/Desktop/PLUS PATH")
    OUTPUT_SUBDIR = "output"
    CONFIG_SUBDIR = "config"
    
    def __init__(self):
        # Generate unique simulation ID and output directory
        self.simulation_id = f"simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:4]}"
        self.output_dir = os.path.join(self.BASE_PATH, self.OUTPUT_SUBDIR, self.simulation_id)
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.sumo_config = os.path.join(self.BASE_PATH, self.CONFIG_SUBDIR, "map.sumo.cfg")
        self.sumo_binary = "sumo-gui"  # Can be changed to "sumo" for faster runs
        self.tls_id = "5926433422"
        self.simulation_delay = 0.1
        self.trip_data = []  # To store trip information
        self.emission_data = []  # To store emission data
        self.simulation_steps = 0

    @classmethod
    def get_output_search_pattern(cls):
        """Returns the search pattern for finding tripinfo files from all simulations"""
        return os.path.join(cls.BASE_PATH, cls.OUTPUT_SUBDIR, "simulation_*", "tripinfo.xlsx")

    def initialize_simulation(self):
        """Start SUMO and connect TraCI with better error handling"""
        sumo_cmd = [
            self.sumo_binary,
            "-c", self.sumo_config,
            "--waiting-time-memory", "1000",
            "--time-to-teleport", "-1",
            "--random",
            "--output-prefix", os.path.join(self.output_dir, "sumo_")
        ]
        
        print(f"Starting SUMO with config: {self.sumo_config}")
        print(f"Output will be saved to: {os.path.abspath(self.output_dir)}")
        
        try:
            traci.start(sumo_cmd)
            print(f"SUMO started successfully at {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"Failed to start SUMO: {str(e)}")
            print("Please verify:")
            print(f"1. SUMO is installed and available in PATH")
            print(f"2. Config file exists at: {os.path.abspath(self.sumo_config)}")
            raise

    def collect_trip_data(self):
        """Collect data about all vehicles with validation"""
        current_time = traci.simulation.getTime()
        vehicle_ids = traci.vehicle.getIDList()
        
        if not vehicle_ids:
            print(f"No vehicles in simulation at time {current_time}")
            return
            
        for veh_id in vehicle_ids:
            try:
                vehicle_data = {
                    'time': current_time,
                    'vehicle_id': veh_id,
                    'type': traci.vehicle.getTypeID(veh_id),
                    'speed': traci.vehicle.getSpeed(veh_id),
                    'position': traci.vehicle.getLanePosition(veh_id),
                    'lane': traci.vehicle.getLaneID(veh_id),
                    'waiting_time': traci.vehicle.getWaitingTime(veh_id),
                    'co2_emission': traci.vehicle.getCO2Emission(veh_id),
                    'fuel_consumption': traci.vehicle.getFuelConsumption(veh_id),
                }
                self.trip_data.append(vehicle_data)
            except traci.TraCIException as e:
                print(f"Error collecting data for vehicle {veh_id}: {str(e)}")

    def run(self):
        """Main simulation loop with enhanced monitoring"""
        self.initialize_simulation()
        tls = AdaptiveTrafficLight(self.tls_id)
        
        try:
            while traci.simulation.getMinExpectedNumber() > 0:
                self.simulation_steps += 1
                traci.simulationStep()
                current_time = traci.simulation.getTime()
                
                # Collect data every second
                if current_time % 1 == 0:
                    self.collect_trip_data()
                
                # Adaptive control logic
                tls.control_logic()
                
                # Progress reporting every 10 seconds
                if current_time % 10 == 0:
                    print(f"\n--- Simulation Progress ---")
                    print(f"Time: {current_time}s")
                    print(f"Vehicles: {len(traci.vehicle.getIDList())}")
                    print(f"Data points collected: {len(self.trip_data)}")
                    print(f"NS Weight: {tls.get_direction_weight('NS'):.2f}")
                    print(f"EW Weight: {tls.get_direction_weight('EW'):.2f}")
                    print(f"Output Directory: {self.output_dir}")
                
                # Slow down GUI for observation
                if self.sumo_binary == "sumo-gui":
                    time.sleep(self.simulation_delay)
                    
        except traci.TraCIException as e:
            print(f"\nSimulation ended normally: {str(e)}")
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
            traceback.print_exc()
        finally:
            print("\nSimulation ending, saving data...")
            self.save_output_data()
            traci.close()
            print(f"Simulation completed after {self.simulation_steps} steps")
            print(f"All output saved to: {os.path.abspath(self.output_dir)}")

    def save_output_data(self):
        """Handle all output data saving operations"""
        self.save_to_excel()
        self.save_simulation_metadata()
        
        # Show example of how to find results
        self.show_search_example()

    def save_to_excel(self):
        """Save collected data to Excel files with verification"""
        try:
            if not self.trip_data:
                print("Warning: No trip data was collected during simulation!")
                return
                
            print(f"\nPreparing to save {len(self.trip_data)} records...")
            
            trip_df = pd.DataFrame(self.trip_data)
            trip_excel_path = os.path.join(self.output_dir, "tripinfo.xlsx")
            
            # Verify directory exists and is writable
            os.makedirs(self.output_dir, exist_ok=True)
            if not os.access(self.output_dir, os.W_OK):
                raise PermissionError(f"Cannot write to directory: {self.output_dir}")
            
            # Save to Excel
            trip_df.to_excel(trip_excel_path, index=False)
            print(f"Data saved to {trip_excel_path}")
            
        except Exception as e:
            print(f"\nFailed to save data: {str(e)}")
            traceback.print_exc()

    def save_simulation_metadata(self):
        """Save additional information about the simulation"""
        try:
            metadata = {
                'simulation_id': self.simulation_id,
                'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'duration_steps': self.simulation_steps,
                'config_file': self.sumo_config,
                'data_points': len(self.trip_data),
                'output_directory': self.output_dir,
                'search_pattern': self.get_output_search_pattern()
            }
            
            meta_path = os.path.join(self.output_dir, "simulation_meta.json")
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"Simulation metadata saved to {meta_path}")
        except Exception as e:
            print(f"Failed to save metadata: {str(e)}")

    def show_search_example(self):
        """Demonstrate how to search for simulation results"""
        search_pattern = self.get_output_search_pattern()
        print("\n" + "="*50)
        print("HOW TO FIND SIMULATION RESULTS IN THE FUTURE:")
        print("="*50)
        print("Use this code to find all simulation results:")
        print(f"import glob")
        print(f"search_pattern = r'{search_pattern}'")
        print(f"result_files = glob.glob(search_pattern)")
        print(f"print(f'Found {{len(result_files)}} simulation results')")
        
        # Actually find and display current results
        current_results = glob.glob(search_pattern)
        print("\nCurrent simulation results found:")
        for i, file in enumerate(current_results, 1):
            print(f"{i}. {file}")

    def update_visualization(self, tls):
        """Real-time GUI updates with error handling"""
        try:
            weights = {
                'NS': tls.get_direction_weight('NS'),
                'EW': tls.get_direction_weight('EW')
            }
            
            traci.gui.setZoom("View #0", 1500)
            try:
                traci.gui.remove("weight_display")
            except:
                pass
                
            traci.gui.addText("weight_display", 
                            f"NS Priority: {weights['NS']:.2f}\nEW Priority: {weights['EW']:.2f}", 
                            (10, 10), (255, 255, 255), size=40)
            
            for veh_id in traci.vehicle.getIDList():
                if traci.vehicle.getTypeID(veh_id) == "emergency":
                    traci.vehicle.setHighlight(veh_id, (255, 0, 0, 255))
                    traci.gui.trackVehicle("View #0", veh_id)
                    break
        except Exception as e:
            print(f"Visualization update failed: {str(e)}")

if __name__ == "__main__":
    print("=== SUMO Simulation Controller ===")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        controller = SimulationController()
        controller.run()
    except KeyboardInterrupt:
        print("\nSimulation stopped by user")
    except Exception as e:
        print(f"\nFailed to run simulation: {str(e)}")
        traceback.print_exc()
    finally:
        print(f"\nSimulation ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")