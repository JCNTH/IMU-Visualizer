import numpy as np
from typing import Dict, Any

class CalibrationService:
    """Service for handling calibration data processing"""
    
    def parse_calibration_csv(self, file_content: str) -> np.ndarray:
        """Parse calibration CSV content into numpy array"""
        print(f"Parsing calibration file content")
        lines = file_content.strip().splitlines()
        data = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            # Skip empty or comment lines
            if not line or line.startswith("//"):
                continue
            # Skip header lines (assuming they contain specific keywords)
            if "PacketCounter" in line or "Acc_X" in line:
                continue
                
            # Determine delimiter: comma if present, otherwise use whitespace
            parts = []
            if "," in line:
                parts = line.split(",")
            else:
                parts = line.split()
                
            try:
                row = [float(x) for x in parts]
                data.append(row)
            except ValueError:
                continue
                
        result = np.array(data)
        print(f"Final calibration data shape: {result.shape}")
        return result
    
    def compute_offset(self, calibration_data: np.ndarray) -> np.ndarray:
        """
        Compute offset from calibration data.
        Returns the average row as a simple offset calculation.
        In a real application, you'd compute the sensor-to-body transformation.
        """
        if calibration_data.size == 0:
            return np.array([])
        return np.mean(calibration_data, axis=0) 