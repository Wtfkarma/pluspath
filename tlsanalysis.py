import os
import xml.etree.ElementTree as ET
from glob import glob
from datetime import datetime

class TLSConfigurationAnalyzer:
    def __init__(self, analysis_outputs_root):
        self.analysis_outputs_root = analysis_outputs_root
        self.all_configurations = []

    def find_optimized_configs(self):
        """Find all optimized TLS config files in analysis outputs"""
        search_path = os.path.join(self.analysis_outputs_root, "analysis_*", "optimized_tls.add.xml")
        config_files = glob(search_path)

        if not config_files:
            raise FileNotFoundError(f"No optimized TLS configs found in {self.analysis_outputs_root}")

        return config_files

    def analyze_configurations(self):
        """Analyze all found configurations"""
        config_files = self.find_optimized_configs()

        for config_file in config_files:
            try:
                config_data = self._parse_config_file(config_file)
                self.all_configurations.append(config_data)
            except Exception as e:
                print(f"Error processing {config_file}: {str(e)}")
                continue

        if not self.all_configurations:
            raise ValueError("No valid configurations found to analyze")

        return self._select_best_configuration()

    def _parse_config_file(self, file_path):
        """Parse a single TLS config file and extract metrics"""
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Extract phase durations
        phases = root.findall('phase')
        if len(phases) < 3:
            raise ValueError(f"Invalid phase data in {file_path}")
        ns_duration = float(phases[0].attrib['duration'])
        ew_duration = float(phases[2].attrib['duration'])

        # Calculate balance score (closer to 1:1 is better)
        balance_score = min(ns_duration, ew_duration) / max(ns_duration, ew_duration)

        # Get the analysis timestamp from folder name
        folder_name = os.path.basename(os.path.dirname(file_path))  # e.g. 'analysis_20250612_144000'
        timestamp_str = folder_name.replace("analysis_", "")         # -> '20250612_144000'
        timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

        return {
            'file_path': file_path,
            'timestamp': timestamp,
            'ns_duration': ns_duration,
            'ew_duration': ew_duration,
            'total_cycle': ns_duration + ew_duration + 6,  # Including yellow phases
            'balance_score': balance_score,
            'folder': os.path.dirname(file_path)
        }

    def _select_best_configuration(self):
        """Select the best configuration based on multiple criteria"""
        sorted_configs = sorted(self.all_configurations,
                                key=lambda x: (-x['balance_score'], x['total_cycle']))
        best_config = sorted_configs[0]

        recommendations = {
            'best_config': best_config,
            'all_configs': sorted_configs,
            'suggested_phases': {
                'North-South': best_config['ns_duration'],
                'East-West': best_config['ew_duration']
            },
            'performance_metrics': {
                'balance_ratio': f"{best_config['ns_duration']/best_config['ew_duration']:.2f}:1",
                'total_cycle_time': best_config['total_cycle'],
                'balance_score': f"{best_config['balance_score']*100:.1f}%"
            }
        }

        return recommendations

    def generate_adaptive_tls_recommendation(self, recommendations):
        """Generate adaptive TLS recommendation based on analysis"""
        best = recommendations['best_config']

        adaptive_tls_template = f"""<!-- Best Adaptive TLS Configuration Recommendation -->
<!-- Selected from analysis on {best['timestamp']} -->
<!-- Source: {best['file_path']} -->

<tlLogic id="adaptive_signal" type="actuated" programID="adaptive">
    <param key="max-gap" value="3.0"/>
    <param key="detector-gap" value="2.0"/>
    <param key="passing-time" value="2.0"/>
    
    <phase duration="{best['ns_duration']}" minDur="20" maxDur="90" state="GGGgrrrrGGGgrrrr"/>
    <phase duration="3" state="yyyygrrryyyygrrr"/>
    <phase duration="{best['ew_duration']}" minDur="20" maxDur="90" state="rrrrGGGgrrrrGGGg"/>
    <phase duration="3" state="rrrryyyyrrrryyyy"/>
</tlLogic>

<!-- Performance Metrics -->
<!-- Balance Ratio: {recommendations['performance_metrics']['balance_ratio']} -->
<!-- Total Cycle Time: {recommendations['performance_metrics']['total_cycle_time']}s -->
<!-- Balance Score: {recommendations['performance_metrics']['balance_score']} -->"""

        # Make timestamped output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(
            r"C:/Users/anura/OneDrive/Desktop/PLUS PATH/final xml",
            f"adaptive_tls_recommendation_{timestamp}"
        )
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, "adaptive_tls_recommendation.add.xml")
        with open(output_path, 'w') as f:
            f.write(adaptive_tls_template)

        print(f"\n✅ Generated adaptive TLS recommendation at:\n{output_path}")
        return output_path

if __name__ == "__main__":
    try:
        analysis_root = r"C:/Users/anura/OneDrive/Desktop/PLUS PATH/analysis outputs"
        analyzer = TLSConfigurationAnalyzer(analysis_root)

        recommendations = analyzer.analyze_configurations()

        print("\n📊 Analysis of All Optimized Configurations:")
        print("=======================================")
        for i, config in enumerate(recommendations['all_configs'], 1):
            print(f"\nConfiguration #{i} ({config['timestamp']}):")
            print(f"  NS Duration: {config['ns_duration']}s")
            print(f"  EW Duration: {config['ew_duration']}s")
            print(f"  Total Cycle: {config['total_cycle']}s")
            print(f"  Balance Score: {config['balance_score']*100:.1f}%")
            print(f"  Location: {config['folder']}")

        print("\n🏆 Best Configuration Selected:")
        print("==========================")
        print(f"North-South Phase: {recommendations['suggested_phases']['North-South']}s")
        print(f"East-West Phase: {recommendations['suggested_phases']['East-West']}s")
        print(f"Balance Ratio: {recommendations['performance_metrics']['balance_ratio']}")
        print(f"Total Cycle Time: {recommendations['performance_metrics']['total_cycle_time']}s")

        analyzer.generate_adaptive_tls_recommendation(recommendations)

    except Exception as e:
        print(f"Error: {str(e)}")
