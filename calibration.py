# calibration.py

import numpy as np

def parse_calibration_csv(file_content: str) -> np.ndarray:
    print(f"Parsed file {file_content})")
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
        let_parts = []
        if "," in line:
            let_parts = line.split(",")
        else:
            let_parts = line.split()
        try:
            row = [float(x) for x in let_parts]
            # Debug print: show number of columns parsed on this line
            # print(f"Parsed line {i}: {row} (columns: {len(row)})")
            data.append(row)
        except ValueError:
            # print(f"Skipping line {i} due to conversion error: {line}")
            continue
    result = np.array(data)
    print(f"Final data shape: {result.shape}")
    return result




def compute_offset(calibration_data: np.ndarray) -> np.ndarray:
    """
    Dummy offset calculation: returns the average row.
    In a real application, you’d compute the sensor-to-body transformation.
    """
    if calibration_data.size == 0:
        return np.array([])
    return np.mean(calibration_data, axis=0)

# Test the functions
if __name__ == '__main__':
    sample_csv = "w,x,y,z\n0.1,0.2,0.3,0.4\n0.2,0.3,0.4,0.5"
    data = parse_calibration_csv(sample_csv)
    offset = compute_offset(data)
    print("Calibration Data:\n", data)
    print("Computed Offset:", offset)
