# sensor_mapping.py

def parse_sensor_mapping(file_content: str) -> dict:
    """
    Parse the sensor mapping file.
    Each line should have the format: sensor_id: body_part
    For example: "00B4D7CE: thigh"
    """
    mapping = {}
    for line in file_content.strip().splitlines():
        if ":" in line:
            sensor_id, body_part = line.split(":", 1)
            mapping[sensor_id.strip()] = body_part.strip()
    return mapping

# Test the function
if __name__ == '__main__':
    sample = """00B4D7CE: thigh
00B4D7FE: shank"""
    mapping = parse_sensor_mapping(sample)
    print("Sensor Mapping:", mapping)
