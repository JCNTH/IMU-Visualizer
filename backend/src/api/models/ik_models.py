from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field

class CalibrationData(BaseModel):
    """Model for calibration data structure"""
    task_data: Dict[str, Dict[str, Any]] = Field(
        description="Calibration data organized by task and sensor"
    )

class IKRequest(BaseModel):
    """Request model for IK processing"""
    subject: int = Field(default=1, description="Subject ID")
    task: str = Field(default="treadmill_walking", description="Task name")
    selected_setup: str = Field(default="mm", description="Sensor setup configuration")
    filter_type: str = Field(default="Xsens", description="Filter type for processing")
    dim: str = Field(default="9D", description="Dimensions for processing")
    remove_offset: bool = Field(default=True, description="Whether to remove offset")
    main_task_data: Dict[str, Any] = Field(description="Main task sensor data")
    calibration_data: Dict[str, Dict[str, Any]] = Field(description="Calibration data by task")

class IKResponse(BaseModel):
    """Response model for IK processing"""
    status: str = Field(description="Status of the IK processing")
    ik_results: Optional[Dict[str, Any]] = Field(default=None, description="IK processing results")
    message: Optional[str] = Field(default=None, description="Error message if failed")
    details: Optional[str] = Field(default=None, description="Detailed error information")

class SensorMapping(BaseModel):
    """Model for sensor mapping data"""
    mapping: Dict[str, str] = Field(description="Mapping from sensor ID to sensor name")

class VideoGenerationRequest(BaseModel):
    """Request model for video generation"""
    model_path: str = Field(description="Path to the OpenSim model file")
    mot_path: str = Field(description="Path to the motion file")
    calib_path: str = Field(description="Path to the calibration file")
    subject: str = Field(default="subject", description="Subject identifier")

class UploadResponse(BaseModel):
    """Generic response model for file uploads"""
    status: str = Field(description="Upload status")
    message: Optional[str] = Field(default=None, description="Response message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data") 