"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Info, Plus, Trash2 } from "lucide-react";
import { FileUpload } from "@/components/ui/file-upload";
import { useIMUStore } from "@/store/imuStore";

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

  const generateTasks = () => {
    if (!sensorMapping) {
      alert("Please upload the sensor placement file first.");
      return;
    }

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

  const updateTaskFiles = (taskId: string, files: File[]) => {
    setTasks(prev => prev.map(task => 
      task.id === taskId ? { ...task, files, status: "pending" as const } : task
    ));
  };

  const handleFileError = (taskId: string, error: string) => {
    setTasks(prev => prev.map(task => 
      task.id === taskId ? { ...task, status: "error" as const, error } : task
    ));
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

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Calibration Tasks & Body Alignment
          <div title="For each calibration task, select multiple files containing sensor data.">
            <Info className="w-4 h-4 text-[#C41230] cursor-help" />
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {!showTaskSetup ? (
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              <Label htmlFor="numTasks">Number of Tasks:</Label>
              <Input
                id="numTasks"
                type="number"
                min="1"
                max="10"
                value={numTasks}
                onChange={(e) => setNumTasks(parseInt(e.target.value) || 1)}
                className="w-20"
              />
              <Button onClick={generateTasks} className="bg-[#C41230] hover:bg-[#a10e25]">
                Generate Tasks
              </Button>
            </div>
            
            {!sensorMapping && (
              <Alert>
                <AlertDescription>
                  Please upload the sensor placement file first to configure calibration tasks.
                </AlertDescription>
              </Alert>
            )}
          </div>
        ) : (
          <div className="space-y-6">
            {/* Sensor Selection Table */}
            <div>
              <Label className="text-sm font-medium mb-2 block">Sensor Selection for Tasks</Label>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse border border-gray-300 text-sm">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="border border-gray-300 p-2 text-left">Sensor</th>
                      {tasks.map((task, index) => (
                        <th key={task.id} className="border border-gray-300 p-2 text-center">
                          Task {index + 1}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {getAvailableSensors().map((sensor) => (
                      <tr key={sensor}>
                        <td className="border border-gray-300 p-2 font-medium">{sensor}</td>
                        {tasks.map((task) => (
                          <td key={`${task.id}-${sensor}`} className="border border-gray-300 p-2 text-center">
                            <Checkbox
                              checked={task.selectedSensors.includes(sensor)}
                              onCheckedChange={(checked) => 
                                updateTaskSensors(task.id, sensor, checked as boolean)
                              }
                            />
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Individual Task Configuration */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-medium">Calibration Tasks</Label>
                <Button 
                  onClick={addTask} 
                  size="sm" 
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Add Task
                </Button>
              </div>

              {tasks.map((task, index) => (
                <Card key={task.id} className="border-l-4 border-l-[#C41230]">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base">Calibration Task {index + 1}</CardTitle>
                      {tasks.length > 1 && (
                        <Button
                          onClick={() => removeTask(task.id)}
                          size="sm"
                          variant="ghost"
                          className="text-red-500 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Task Name */}
                    <div>
                      <Label htmlFor={`task-name-${task.id}`} className="text-sm">Task Name:</Label>
                      <Input
                        id={`task-name-${task.id}`}
                        value={task.name}
                        onChange={(e) => updateTaskName(task.id, e.target.value)}
                        placeholder="e.g., static, treadmill_walking, cmj"
                        className="mt-1"
                      />
                    </div>

                    {/* File Upload */}
                    <div>
                      <Label className="text-sm font-medium mb-2 block">Upload Calibration Files:</Label>
                      <FileUpload
                        onFilesSelected={(files) => updateTaskFiles(task.id, files)}
                        onUploadError={(error) => handleFileError(task.id, error)}
                        accept=".csv,.txt"
                        multiple={true}
                        maxFiles={20}
                        maxSize={50}
                        description={`Upload files for sensors: ${task.selectedSensors.join(", ")}`}
                      />
                    </div>

                    {/* Task Status */}
                    {task.status === "error" && task.error && (
                      <Alert variant="destructive">
                        <AlertDescription>{task.error}</AlertDescription>
                      </Alert>
                    )}
                    
                    {task.files.length > 0 && (
                      <div className="text-sm text-green-600">
                        ✓ {task.files.length} file(s) selected for {task.name}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Reset Button */}
            <div className="flex justify-end">
              <Button 
                onClick={() => setShowTaskSetup(false)}
                variant="outline"
                size="sm"
              >
                Reset Configuration
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
} 