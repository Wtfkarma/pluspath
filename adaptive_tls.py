import traci
import numpy as np
from collections import defaultdict
from sklearn.cluster import DBSCAN

class AdaptiveTrafficLight:
    def __init__(self, tls_id):
        self.tls_id = tls_id
        self.vehicles = {}  # {veh_id: {'crossings': [], 'patterns': []}}
        self.emergency_log = []
        
        # Math model parameters
        self.weights = {'frequency': 0.4, 'recency': 0.3, 'consistency': 0.3}
        self.density_weight = 0.3
        self.time_boost_factor = 0.5
        
    def detect_vehicles(self):
        vehicles = []
        for lane in traci.trafficlight.getControlledLanes(self.tls_id):
            for veh_id in traci.lane.getLastStepVehicleIDs(lane):
                if traci.vehicle.getDistance(veh_id) < 50:
                    vehicles.append(veh_id)
        return vehicles
    
    def update_vehicle_history(self, veh_id):
        direction = self.get_approach_direction(veh_id)
        time = traci.simulation.getTime()
        
        if veh_id not in self.vehicles:
            self.vehicles[veh_id] = {'crossings': [], 'patterns': None}
        
        self.vehicles[veh_id]['crossings'].append((time, direction))
        
        # Update patterns every 5 crossings
        if len(self.vehicles[veh_id]['crossings']) % 5 == 0:
            self._detect_patterns(veh_id)
    
    def _detect_patterns(self, veh_id):
        times = [t for t,_ in self.vehicles[veh_id]['crossings']]
        times = np.array(times).reshape(-1, 1)
        
        dbscan = DBSCAN(eps=300, min_samples=3).fit(times)
        clusters = [times[dbscan.labels_ == i] for i in set(dbscan.labels_) if i != -1]
        
        patterns = []
        for cluster in clusters:
            peak_start = np.min(cluster)
            peak_end = np.max(cluster)
            consistency = 1 / (np.std(cluster) + 1e-6)  
            patterns.append({
                'peak_start': peak_start,
                'peak_end': peak_end,
                'consistency': consistency
            })
        
        self.vehicles[veh_id]['patterns'] = patterns
    
    def calculate_priority(self, veh_id):
        """Compute priority score using weighted formula"""
        if veh_id not in self.vehicles or not self.vehicles[veh_id]['crossings']:
            return 0
            
        hist = self.vehicles[veh_id]
        n = len(hist['crossings'])
        
        # Frequency component (log-scaled)
        freq = np.log1p(n)
        
        # Recency (exponential decay)
        last_time = hist['crossings'][-1][0]
        current_time = traci.simulation.getTime()
        recency = 1 / (1 + (current_time - last_time)/3600)  # Hours decay
        
        # Consistency (pattern matching)
        if hist['patterns']:
            time_diffs = [abs(current_time - p['peak_start']) for p in hist['patterns']]
            consistency = max(p['consistency'] for p in hist['patterns']) / (1 + min(time_diffs))
        else:
            consistency = 0.5
            
        return (self.weights['frequency'] * freq + 
                self.weights['recency'] * recency + 
                self.weights['consistency'] * consistency)
    
    def get_direction_weight(self, direction):
        """Calculate total weight for a movement direction"""
        vehicles = self.detect_vehicles()
        total_weight = 0
        
        # Vehicle priority component
        for veh_id in vehicles:
            if self.get_approach_direction(veh_id) == direction:
                total_weight += self.calculate_priority(veh_id)
        
        # Traffic density component
        density = sum(
            1 for veh_id in vehicles 
            if self.get_approach_direction(veh_id) == direction
        )
        total_weight += self.density_weight * density
        
        # Time pattern boost
        if any(self.vehicles.get(veh_id, {}).get('patterns') 
               for veh_id in vehicles):
            total_weight *= (1 + self.time_boost_factor)
            
        return total_weight
    
    def control_logic(self):
        """Main traffic light control algorithm"""
        # Emergency vehicle handling
        for veh_id in self.detect_vehicles():
            if traci.vehicle.getTypeID(veh_id) == 'emergency':
                self.handle_emergency(veh_id)
                return
        
        # Calculate weights for all approaches
        directions = ['NS', 'EW']  # North-South, East-West
        weights = {d: self.get_direction_weight(d) for d in directions}
        total_weight = sum(weights.values())
        
        # Normalize and decide
        if total_weight > 0:
            phase_durations = {}
            for d in directions:
                normalized_weight = weights[d] / total_weight
                
                # Dynamic phase duration formula
                phase_durations[d] = max(
                    15,  # Minimum duration
                    min(
                        60,  # Maximum duration
                        30 * (0.5 + normalized_weight)  # Base 30s + adjustment
                    )
                )
            
            # Switch or extend phase
            current_phase = traci.trafficlight.getPhase(self.tls_id)
            current_direction = self.get_current_direction(current_phase)
            
            if current_direction in directions:
                remaining = traci.trafficlight.getNextSwitch(self.tls_id) - traci.simulation.getTime()
                if remaining < phase_durations[current_direction]:
                    traci.trafficlight.setPhaseDuration(
                        self.tls_id, 
                        phase_durations[current_direction] - remaining
                    )
            else:
                # Switch to highest weighted direction
                next_direction = max(weights, key=weights.get)
                self.set_phase_for_direction(next_direction)
    
