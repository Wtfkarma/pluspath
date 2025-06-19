#!/usr/bin/env python
import os
import traci
from adaptive_tls import AdaptiveTrafficLight
import time
from datetime import datetime

CONFIG_PATH = os.path.join("C:/Users/anura/OneDrive/Desktop/PLUS PATH/config", "map.sumo.cfg")
OUTPUT_DIR = "C:/Users/anura/OneDrive/Desktop/PLUS PATH/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class SimulationController:
    def __init__(self):
        self.sumo_config = CONFIG_PATH
        self.sumo_binary = "sumo-gui" 
        self.tls_id = "5926433422" 
        self.simulation_delay = 0.1  

    def initialize_simulation(self):
        """Start SUMO and connect TraCI"""
        sumo_cmd = [
            self.sumo_binary,
            "-c", self.sumo_config,
            "--tripinfo-output", os.path.join(OUTPUT_DIR, "tripinfo2.xml"),
            "--emission-output", os.path.join(OUTPUT_DIR, "emission2.xml"),
            "--waiting-time-memory", "1000",
            "--time-to-teleport", "-1",
            "--random",  
        ]
        
        print(f"Starting SUMO with config: {self.sumo_config}")  # Debug print
        traci.start(sumo_cmd)
        print(f"Simulation started at {datetime.now().strftime('%H:%M:%S')}")

    def run(self):
        """Main simulation loop"""
        self.initialize_simulation()
        tls = AdaptiveTrafficLight(self.tls_id)
        
        try:
            while traci.simulation.getMinExpectedNumber() > 0:
                traci.simulationStep()
                current_time = traci.simulation.getTime()
                
                tls.control_logic()
                
                # Visualization updates (every 5 seconds)
                if current_time % 5 == 0:
                    self.update_visualization(tls)
                    # Debug print from working code
                    print(f"Time: {current_time}s | "
                         f"NS Weight: {tls.get_direction_weight('NS'):.2f} | "
                         f"EW Weight: {tls.get_direction_weight('EW'):.2f}")
                
                # Slow down GUI for observation
                if self.sumo_binary == "sumo-gui":
                    time.sleep(self.simulation_delay)
                    
        except traci.TraCIException as e:
            print(f"Simulation ended: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
        finally:
            traci.close()
            print(f"Output files saved to {OUTPUT_DIR}")

    def update_visualization(self, tls):
        """Real-time GUI updates"""
        try:
            # Display current weights
            weights = {
                'NS': tls.get_direction_weight('NS'),
                'EW': tls.get_direction_weight('EW')
            }
            
            traci.gui.setZoom("View #0", 1500)
            # Remove existing text before adding new one
            try:
                traci.gui.remove("weight_display")
            except:
                pass
            traci.gui.addText("weight_display", 
                            f"NS Priority: {weights['NS']:.2f}\nEW Priority: {weights['EW']:.2f}", 
                            (10, 10), (255, 255, 255), size=40)
            
            # Track only the first emergency vehicle found
            for veh_id in traci.vehicle.getIDList():
                if traci.vehicle.getTypeID(veh_id) == "emergency":
                    traci.vehicle.setHighlight(veh_id, (255, 0, 0, 255))
                    traci.gui.trackVehicle("View #0", veh_id)
                    break  # Track only one emergency vehicle
        except Exception as e:
            print(f"Visualization update failed: {str(e)}")

if __name__ == "__main__":
    try:
        controller = SimulationController()
        controller.run()
    except KeyboardInterrupt:
        print("Simulation stopped by user")
    except Exception as e:
        print(f"Failed to start simulation: {str(e)}")