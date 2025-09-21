"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertModal } from "@/components/ui/modal";
import { Info, Plus, Trash2, ChevronDown, ChevronRight, CheckCircle, Folder, Files, Eye } from "lucide-react";
import { FileUpload } from "@/components/ui/file-upload";
import { SampleModal } from "@/components/ui/sample-modal";
import { uploadCalibration } from "@/lib/api";
import { useIMUStore } from "@/store/imuStore";
import { cn } from "@/lib/utils";

interface CalibrationTask {
  id: string;
  name: string;
  selectedSensors: string[];
  files: File[];
  status: "pending" | "uploading" | "completed" | "error";
  error?: string;
}

const REQUIRED_SENSORS = ["pelvis", "thigh_l", "shank_l", "foot_l", "thigh_r", "shank_r", "foot_r"];

export function CalibrationSection() {
  const { sensorMapping, setCalibrationData } = useIMUStore();
  const [numTasks, setNumTasks] = useState(1);
  const [tasks, setTasks] = useState<CalibrationTask[]>([]);
  const [showTaskSetup, setShowTaskSetup] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [showSampleModal, setShowSampleModal] = useState(false);
  const [alertModal, setAlertModal] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    type: "info" | "warning" | "error" | "success";
  }>({ isOpen: false, title: "", message: "", type: "info" });

  const generateTasks = () => {
    if (!sensorMapping) {
      setAlertModal({
        isOpen: true,
        title: "Sensor Mapping Required",
        message: "Please upload the sensor placement file first before generating calibration tasks.",
        type: "warning"
      });
      return;
    }

    // Clear any existing calibration data to start fresh
    setCalibrationData({});

    const newTasks: CalibrationTask[] = [];
    for (let i = 0; i < numTasks; i++) {
      newTasks.push({
        id: `task_${i}`,
        name: i === 0 ? "static" : `task_${i + 1}`,
        selectedSensors: [...REQUIRED_SENSORS],
        files: [],
        status: "pending",
      });
    }
    setTasks(newTasks);
    setShowTaskSetup(true);
  };

  const updateTaskName = (taskId: string, name: string) => {
    setTasks(prev => prev.map(task => 
      task.id === taskId ? { ...task, name } : task
    ));
  };

  const updateTaskSensors = (taskId: string, sensor: string, checked: boolean) => {
    setTasks(prev => prev.map(task => {
      if (task.id !== taskId) return task;
      
      const newSensors = checked 
        ? [...task.selectedSensors, sensor]
        : task.selectedSensors.filter(s => s !== sensor);
      
      return { ...task, selectedSensors: newSensors };
    }));
  };

  const updateTaskFiles = async (taskId: string, files: File[]) => {
    // Auto-detect folder name from file paths
    let autoTaskName = "";
    if (files.length > 0) {
      // Check if files have a common folder structure
      const firstFile = files[0];
      if (firstFile.webkitRelativePath) {
        // Extract folder name from the relative path
        const pathParts = firstFile.webkitRelativePath.split('/');
        if (pathParts.length > 1) {
          autoTaskName = pathParts[0]; // Use the root folder name
        }
      }
    }

    // Update task status to uploading and set auto-detected name
    setTasks(prev => prev.map(task => 
      task.id === taskId ? { 
        ...task, 
        files, 
        status: "uploading" as const,
        name: autoTaskName || task.name // Use auto-detected name or keep existing
      } : task
    ));

    try {
      // Upload files to backend
      const response = await uploadCalibration(files, taskId);
      
      // Update task status to completed
      const updatedTasks = tasks.map(task => 
        task.id === taskId ? { 
          ...task, 
          files, 
          status: "completed" as const,
          name: autoTaskName || task.name
        } : task
      );
      setTasks(updatedTasks);
      
      // IMPORTANT: Store ONLY the actual sensor data from backend, no frontend metadata
      const { calibrationData: existingData } = useIMUStore.getState();
      
      // Create fresh calibration data object
      const cleanCalibrationData: { [key: string]: any } = {};
      
      // Copy existing data (but only if it's actual sensor data, not metadata)
      Object.keys(existingData).forEach(key => {
        const taskData = existingData[key];
        // Only copy if it looks like sensor data (has sensor IDs as keys)
        if (taskData && typeof taskData === 'object' && !taskData.hasOwnProperty('name') && !taskData.hasOwnProperty('sensors')) {
          cleanCalibrationData[key] = taskData;
        }
      });
      
      // Add new calibration data from backend response
      if (response.calibration_data && response.status === "success") {
        console.log(`Backend returned calibration data for task ${taskId}:`, response.calibration_data);
        cleanCalibrationData[taskId] = response.calibration_data;
      }
      
      console.log("Clean calibration data being stored:", cleanCalibrationData);
      setCalibrationData(cleanCalibrationData);
      
      // Auto-collapse if all tasks have files
      const allTasksHaveFiles = updatedTasks.every(task => task.files.length > 0);
      if (allTasksHaveFiles) {
        setIsCollapsed(true);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Upload failed";
      
      // Update task status to error
      setTasks(prev => prev.map(task => 
        task.id === taskId ? { 
          ...task, 
          status: "error" as const, 
          error: errorMessage
        } : task
      ));
      
      // Show error in modal
      setAlertModal({
        isOpen: true,
        title: "Upload Failed",
        message: errorMessage,
        type: "error"
      });
    }
  };

  const handleFileError = (taskId: string, error: string) => {
    setTasks(prev => prev.map(task => 
      task.id === taskId ? { ...task, status: "error" as const, error } : task
    ));
    
    // Show error in modal
    setAlertModal({
      isOpen: true,
      title: "Upload Error",
      message: error,
      type: "error"
    });
  };

  const removeTask = (taskId: string) => {
    setTasks(prev => prev.filter(task => task.id !== taskId));
    setNumTasks(prev => Math.max(1, prev - 1));
  };

  const addTask = () => {
    const newTaskId = `task_${Date.now()}`;
    setTasks(prev => [...prev, {
      id: newTaskId,
      name: `task_${prev.length + 1}`,
      selectedSensors: [...REQUIRED_SENSORS],
      files: [],
      status: "pending",
    }]);
    setNumTasks(prev => prev + 1);
  };

  const getAvailableSensors = () => {
    if (!sensorMapping) return [];
    return Object.values(sensorMapping)
      .map(name => name.toLowerCase())
      .filter(name => REQUIRED_SENSORS.includes(name));
  };

  const isCompleted = tasks.length > 0 && tasks.some(task => task.status === "completed");

  return (
    <div className="border-b border-gray-100 pb-4">
      {/* Collapsible Header */}
      <Button
        variant="ghost"
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="w-full justify-between p-0 h-auto hover:bg-transparent"
      >
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            {isCollapsed ? (
              <ChevronRight className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            )}
            <h3 className="font-medium text-gray-900">Calibration Tasks</h3>
          </div>
          <div className="flex items-center gap-2">
            {isCompleted && (
              <>
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span className="text-sm text-green-600 font-medium">
                  {tasks.filter(t => t.status === "completed").length} task(s) uploaded
                </span>
              </>
            )}
          </div>
        </div>
        <div title="For each calibration task, select multiple files containing sensor data.">
          <Info className="w-4 h-4 text-[#C41230] cursor-help" />
        </div>
      </Button>

      {/* Collapsed Summary */}
      {isCollapsed && isCompleted && (
        <div className="pt-2">
          <div className="bg-green-50 border border-green-200 rounded-md p-2">
            <div className="text-xs text-green-800 font-medium mb-2">
              Calibration Tasks ({tasks.filter(t => t.status === "completed").length} uploaded)
            </div>
            <div className="space-y-1">
              {tasks.filter(t => t.status === "completed").map((task) => (
                <div key={task.id} className="flex justify-between items-center text-xs">
                  <span className="font-medium text-gray-700">{task.name}:</span>
                  <span className="text-green-700">✓ {task.files.length} files</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Collapsible Content */}
      <div className={cn(
        "transition-all duration-200",
        isCollapsed ? "max-h-0 opacity-0 overflow-hidden" : "opacity-100"
      )}>
        <div className="pt-2 space-y-3">
          {!showTaskSetup ? (
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Label htmlFor="numTasks" className="text-xs">Tasks:</Label>
                <Input
                  id="numTasks"
                  type="number"
                  min="1"
                  max="5"
                  value={numTasks}
                  onChange={(e) => setNumTasks(parseInt(e.target.value) || 1)}
                  className="w-16 h-6 text-xs"
                />
                <Button onClick={generateTasks} size="sm" className="bg-[#C41230] hover:bg-[#a10e25] text-xs">
                  Generate
                </Button>
              </div>
              
              {!sensorMapping && (
                <Alert className="py-1">
                  <AlertDescription className="text-xs">
                    Upload sensor placement file first.
                  </AlertDescription>
                </Alert>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {/* Compact Task List */}
              <div className="space-y-2">
                {tasks.map((task, index) => (
                  <div key={task.id} className="bg-gray-50 p-2 rounded text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex-1 mr-2">
                        <Input
                          value={task.name}
                          onChange={(e) => updateTaskName(task.id, e.target.value)}
                          className="h-6 text-xs"
                          placeholder="Task name (auto-detected from folder)"
                        />
                        {task.files.length > 0 && task.files[0].webkitRelativePath && (
                          <div className="text-xs text-blue-600 mt-0.5">
                            📁 Auto-named from folder
                          </div>
                        )}
                      </div>
                      {tasks.length > 1 && (
                        <Button
                          onClick={() => removeTask(task.id)}
                          size="sm"
                          variant="ghost"
                          className="h-6 w-6 p-0 text-red-500"
                        >
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      )}
                    </div>
                    
                    {task.files.length === 0 ? (
                      <div className="space-y-2">
                        <FileUpload
                          onFilesSelected={(files) => updateTaskFiles(task.id, files)}
                          onUploadError={(error) => handleFileError(task.id, error)}
                          accept=".csv,.txt"
                          multiple={true}
                          maxFiles={0}
                          maxSize={25}
                          allowFolders={true}
                          description={`Upload calibration folder for: ${task.selectedSensors.slice(0, 3).join(", ")}${task.selectedSensors.length > 3 ? "..." : ""}`}
                        />
                        <div className="flex justify-between items-center">
                          <div className="text-xs text-gray-600 bg-blue-50 p-2 rounded border border-blue-200 flex-1">
                            💡 <strong>Folder upload recommended:</strong> Select your calibration folder and the task name will auto-update to match the folder name.
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setShowSampleModal(true)}
                            className="flex items-center gap-2 text-xs ml-2"
                          >
                            <Eye className="w-3 h-3" />
                            View Sample
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className={cn(
                        "border rounded-md p-2",
                        task.status === "completed" ? "bg-green-50 border-green-200" :
                        task.status === "uploading" ? "bg-blue-50 border-blue-200" :
                        task.status === "error" ? "bg-red-50 border-red-200" :
                        "bg-gray-50 border-gray-200"
                      )}>
                        <div className="flex justify-between items-center mb-2">
                          <span className={cn(
                            "text-sm font-medium",
                            task.status === "completed" ? "text-green-800" :
                            task.status === "uploading" ? "text-blue-800" :
                            task.status === "error" ? "text-red-800" :
                            "text-gray-800"
                          )}>
                            {task.status === "uploading" ? "⏳ Uploading..." :
                             task.status === "completed" ? "✓ Uploaded" :
                             task.status === "error" ? "❌ Error" :
                             "📁"} {task.files.length} files
                          </span>
                          <Button
                            onClick={() => updateTaskFiles(task.id, [])}
                            size="sm"
                            variant="outline"
                            className="h-6 text-xs"
                            disabled={task.status === "uploading"}
                          >
                            Change Files
                          </Button>
                        </div>
                        <div className={cn(
                          "text-xs",
                          task.status === "completed" ? "text-green-700" :
                          task.status === "uploading" ? "text-blue-700" :
                          task.status === "error" ? "text-red-700" :
                          "text-gray-700"
                        )}>
                          Sensors: {task.selectedSensors.join(", ")}
                        </div>
                        <div className="text-xs text-gray-600 mt-1">
                          Files: {task.files.map(f => f.name).join(", ").slice(0, 100)}
                          {task.files.map(f => f.name).join(", ").length > 100 ? "..." : ""}
                        </div>
                        {task.error && (
                          <div className="text-xs text-red-600 mt-1">
                            Error: {task.error}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div className="flex justify-between">
                <div className="flex gap-2">
                  <Button onClick={addTask} size="sm" variant="outline" className="text-xs">
                    <Plus className="w-3 h-3 mr-1" />
                    Add Task
                  </Button>
                  <Button onClick={() => setShowTaskSetup(false)} variant="outline" size="sm" className="text-xs">
                    Reset
                  </Button>
                </div>
                {isCompleted && (
                  <Button 
                    onClick={() => setIsCollapsed(true)} 
                    variant="outline" 
                    size="sm" 
                    className="text-xs"
                  >
                    Minimize
                  </Button>
                )}
              </div>
            </div>
          )}


        </div>
      </div>
      
      {/* Alert Modal */}
      <AlertModal
        isOpen={alertModal.isOpen}
        onClose={() => setAlertModal(prev => ({ ...prev, isOpen: false }))}
        title={alertModal.title}
        message={alertModal.message}
        type={alertModal.type}
      />
      
      {/* Sample Modal */}
      <SampleModal
        isOpen={showSampleModal}
        onClose={() => setShowSampleModal(false)}
        title="Sample Calibration Data"
        type="calibration"
      />
    </div>
  );
} 