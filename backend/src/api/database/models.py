from sqlmodel import SQLModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str = Field(unique=True, index=True)
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Project(SQLModel, table=True):
    __tablename__ = "projects"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    description: Optional[str] = None
    user_id: str = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SensorMapping(SQLModel, table=True):
    __tablename__ = "sensor_mappings"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="projects.id")
    name: str
    mapping_data: Dict[str, Any] = Field(default_factory=dict)  # JSON field for sensor ID to name mapping
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CalibrationTask(SQLModel, table=True):
    __tablename__ = "calibration_tasks"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="projects.id")
    task_name: str
    task_type: str  # e.g., "static", "treadmill_walking"
    selected_sensors: List[str] = Field(default_factory=list)  # List of sensor names
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SensorData(SQLModel, table=True):
    __tablename__ = "sensor_data"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="projects.id")
    calibration_task_id: Optional[str] = Field(foreign_key="calibration_tasks.id", default=None)
    sensor_name: str
    sensor_id: str
    file_name: str
    file_path: str  # Path to stored file
    data_type: str  # "calibration" or "main_task"
    processed_data: Optional[Dict[str, Any]] = Field(default=None)  # JSON field for processed data
    created_at: datetime = Field(default_factory=datetime.utcnow)

class IKProcessing(SQLModel, table=True):
    __tablename__ = "ik_processing"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="projects.id")
    parameters: Dict[str, Any] = Field(default_factory=dict)  # IK parameters
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    results: Optional[Dict[str, Any]] = Field(default=None)  # JSON field for IK results
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class VideoGeneration(SQLModel, table=True):
    __tablename__ = "video_generations"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    ik_processing_id: str = Field(foreign_key="ik_processing.id")
    parameters: Dict[str, Any] = Field(default_factory=dict)  # Video generation parameters
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    video_path: Optional[str] = None
    progress: int = Field(default=0)  # 0-100
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None 