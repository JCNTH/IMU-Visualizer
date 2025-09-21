"use client";

import React from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertTriangle, FileX } from "lucide-react";

interface UnmappedSensorsAlertProps {
  unmappedSensors: Array<{file: string; sensor_id: string}>;
  className?: string;
}

export function UnmappedSensorsAlert({ unmappedSensors, className }: UnmappedSensorsAlertProps) {
  if (!unmappedSensors || unmappedSensors.length === 0) {
    return null;
  }

  const uniqueSensorIds = [...new Set(unmappedSensors.map(s => s.sensor_id))];

  return (
    <Alert variant="destructive" className={className}>
      <AlertTriangle className="h-4 w-4" />
      <AlertDescription>
        <div className="space-y-2">
          <div className="font-medium">
            {unmappedSensors.length} sensor files were skipped (no mapping provided)
          </div>
          <div className="text-sm">
            <div className="font-medium mb-1">Unmapped Sensor IDs:</div>
            <div className="font-mono text-xs bg-yellow-50 p-2 rounded border">
              {uniqueSensorIds.join(", ")}
            </div>
          </div>
          <div className="text-sm text-gray-600">
            💡 To include these sensors, update your sensor mapping file to specify which body parts these sensor IDs represent.
          </div>
        </div>
      </AlertDescription>
    </Alert>
  );
} 