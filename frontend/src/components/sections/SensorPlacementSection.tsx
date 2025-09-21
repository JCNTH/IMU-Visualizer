"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Info, ChevronDown, ChevronRight, CheckCircle } from "lucide-react";
import { useIMUStore } from "@/store/imuStore";
import { cn } from "@/lib/utils";

type SensorType = "pelvis" | "leftThigh" | "rightThigh" | "leftShank" | "rightShank" | "leftToes" | "rightToes";
type ViewType = "frontal" | "lateral" | "medial" | "posterior";

export function SensorPlacementSection() {
  const { 
    selectedSensorType, 
    selectedView, 
    rotationValues, 
    axisMapping,
    sensorPlacements,
    setSelectedSensorType,
    setSelectedView,
    setRotationValues,
    setAxisMapping
  } = useIMUStore();
  
  const [isCollapsed, setIsCollapsed] = useState(false);

  const sensorButtons: { type: SensorType; label: string }[] = [
    { type: "pelvis", label: "Pelvis" },
    { type: "leftThigh", label: "Left Thigh" },
    { type: "rightThigh", label: "Right Thigh" },
    { type: "leftShank", label: "Left Shank" },
    { type: "rightShank", label: "Right Shank" },
    { type: "leftToes", label: "Left Toes" },
    { type: "rightToes", label: "Right Toes" },
  ];

  const viewButtons: { type: ViewType; label: string }[] = [
    { type: "frontal", label: "Frontal" },
    { type: "lateral", label: "Lateral" },
    { type: "medial", label: "Medial" },
    { type: "posterior", label: "Posterior" },
  ];

  const handleSensorSelect = (sensorType: SensorType) => {
    if (selectedSensorType === sensorType) {
      setSelectedSensorType(null);
    } else {
      setSelectedSensorType(sensorType);
    }
  };

  const handleRotationChange = (axis: keyof typeof rotationValues, value: number) => {
    setRotationValues({ ...rotationValues, [axis]: value });
  };

  const isCompleted = Object.keys(sensorPlacements).length > 0;
  const placedSensorsCount = Object.keys(sensorPlacements).length;

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
            <h3 className="font-medium text-gray-900">IMU Sensor Placement</h3>
          </div>
          {isCompleted && (
            <CheckCircle className="w-4 h-4 text-green-500" />
          )}
        </div>
        <div title="Place IMU sensors on the 3D skeleton by selecting a sensor type and clicking on the model.">
          <Info className="w-4 h-4 text-[#C41230] cursor-help" />
        </div>
      </Button>

      {/* Collapsible Content */}
      <div className={cn(
        "transition-all duration-200",
        isCollapsed ? "max-h-0 opacity-0 overflow-hidden" : "opacity-100"
      )}>
        <div className="pt-2 space-y-3">
          {/* Sensor Type Selection */}
          <div>
            <Label className="text-xs font-medium mb-1 block">Select Sensor Type:</Label>
            <div className="grid grid-cols-2 gap-1">
              {sensorButtons.map(({ type, label }) => (
                <Button
                  key={type}
                  variant={selectedSensorType === type ? "default" : "outline"}
                  size="sm"
                  className={`text-xs ${
                    selectedSensorType === type 
                      ? "bg-[#C41230] hover:bg-[#a10e25]" 
                      : "hover:bg-gray-100"
                  }`}
                  onClick={() => handleSensorSelect(type)}
                >
                  {label}
                </Button>
              ))}
            </div>
          </div>

          {/* Placement View */}
          <div>
            <Label className="text-xs font-medium mb-1 block">Placement View</Label>
            <div className="grid grid-cols-2 gap-1">
              {viewButtons.map(({ type, label }) => (
                <Button
                  key={type}
                  variant={selectedView === type ? "default" : "outline"}
                  size="sm"
                  className={`text-xs ${
                    selectedView === type 
                      ? "bg-gray-600 hover:bg-gray-700" 
                      : "hover:bg-gray-100"
                  }`}
                  onClick={() => setSelectedView(type)}
                >
                  {label}
                </Button>
              ))}
            </div>
          </div>

          {/* Rotation Controls */}
          {selectedSensorType && (
            <div>
              <Label className="text-xs font-medium mb-1 block">Rotation (°)</Label>
              <div className="space-y-1">
                {(["x", "y", "z"] as const).map((axis) => (
                  <div key={axis} className="flex items-center space-x-2">
                    <Label className="w-3 text-xs">{axis.toUpperCase()}:</Label>
                    <input
                      type="range"
                      min="0"
                      max="360"
                      value={rotationValues[axis]}
                      onChange={(e) => handleRotationChange(axis, parseInt(e.target.value))}
                      className="flex-1 h-1 bg-gray-200 rounded appearance-none cursor-pointer"
                    />
                    <span className="w-6 text-xs text-right">{rotationValues[axis]}°</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Axis Definition */}
          <div>
            <Label className="text-xs font-medium mb-1 block">Sensor Axes</Label>
            <div className="grid grid-cols-3 gap-1 text-xs">
              <div className="flex flex-col">
                <Label className="text-xs mb-0.5">Up:</Label>
                <Select value={axisMapping.up} onValueChange={(value) => setAxisMapping({...axisMapping, up: value})}>
                  <SelectTrigger className="h-6 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="X">X</SelectItem>
                    <SelectItem value="Y">Y</SelectItem>
                    <SelectItem value="Z">Z</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex flex-col">
                <Label className="text-xs mb-0.5">Left:</Label>
                <Select value={axisMapping.left} onValueChange={(value) => setAxisMapping({...axisMapping, left: value})}>
                  <SelectTrigger className="h-6 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="X">X</SelectItem>
                    <SelectItem value="Y">Y</SelectItem>
                    <SelectItem value="Z">Z</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex flex-col">
                <Label className="text-xs mb-0.5">Out:</Label>
                <Select value={axisMapping.out} onValueChange={(value) => setAxisMapping({...axisMapping, out: value})}>
                  <SelectTrigger className="h-6 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="X">X</SelectItem>
                    <SelectItem value="Y">Y</SelectItem>
                    <SelectItem value="Z">Z</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Instructions */}
          <div className="text-xs text-gray-500 bg-gray-50 p-1.5 rounded">
            <p className="font-medium">Instructions:</p>
            <p>1. Select sensor type → 2. Click skeleton → 3. Drag to move</p>
          </div>

          {/* Status Summary */}
          {isCompleted && (
            <div className="text-xs text-green-600 bg-green-50 p-2 rounded">
              ✓ {placedSensorsCount} sensor{placedSensorsCount !== 1 ? 's' : ''} placed on skeleton
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 