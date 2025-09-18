from typing import Dict, Any

class DataProcessor:
    """Utility class for data processing operations"""
    
    def parse_sensor_mapping(self, content: str) -> Dict[str, str]:
        """Parse sensor mapping text content"""
        mapping = {}
        lines = content.split('\n')
        
        # Assumes first line is a header; process remaining lines
        for i in range(1, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                sensor_name = parts[0].lower()
                sensor_id = parts[1]
                mapping[sensor_id] = sensor_name
        
        return mapping 