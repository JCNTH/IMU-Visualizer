# MBL IMU Visualization

A comprehensive IMU (Inertial Measurement Unit) data visualization and analysis tool for motion capture and biomechanical analysis.

## Overview

This project provides a complete pipeline for processing, analyzing, and visualizing IMU sensor data. It includes inverse kinematics (IK) solving, motion capture integration, and real-time 3D visualization capabilities.

## Features

- **IMU Data Processing**: Process raw IMU sensor data from multiple sensors
- **Inverse Kinematics**: Solve for joint angles and body pose from IMU measurements
- **Motion Capture Integration**: Support for motion capture data formats
- **3D Visualization**: Real-time 3D visualization of human motion and sensor placement
- **Web Interface**: Interactive web-based interface for data analysis
- **Calibration Tools**: Sensor calibration and alignment utilities
- **Multiple Data Formats**: Support for various IMU data formats and protocols

## Project Structure

```
mbl_imuviz/
├── app.py                 # Main Flask web application
├── main.py               # Main entry point
├── calibration.py        # Sensor calibration utilities
├── generate_IK.py        # Inverse kinematics generation
├── ik_solver.py          # IK solving algorithms
├── sensor_mapping.py     # Sensor placement and mapping
├── constants/            # Configuration constants
├── imu/                  # IMU processing modules
├── imu_data/            # Sample IMU data files
├── static/              # Web interface assets
├── utils/               # Utility functions
└── scripts/             # Processing scripts
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mbl_imuviz.git
cd mbl_imuviz
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

## Usage

### Web Interface
1. Start the Flask application: `python app.py`
2. Open your browser to `http://localhost:5000`
3. Upload IMU data files through the web interface
4. View real-time 3D visualization of motion data

### Command Line
```bash
# Process IMU data
python main.py --input imu_data/sample_data.txt

# Run calibration
python calibration.py --sensors sensor_config.json

# Generate IK solutions
python generate_IK.py --data processed_data.pkl
```

## Data Formats

The system supports various IMU data formats:
- Text files with sensor readings
- Pickle files with processed data
- Motion capture formats
- Real-time streaming data

## Configuration

Edit the configuration files in the `constants/` directory:
- `constant_common.py`: General configuration
- `constant_mocap.py`: Motion capture settings
- `constant_mt.py`: MT sensor specific settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Requirements

- Python 3.7+
- NumPy
- Flask
- Quaternion
- Pandas
- Matplotlib
- Three.js (for web visualization)

## Contact

For questions or support, please open an issue on GitHub. 