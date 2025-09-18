"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Info } from "lucide-react";
import { FileUpload } from "@/components/ui/file-upload";
import { uploadMainTask } from "@/lib/api";
import { useIMUStore } from "@/store/imuStore";

export function MainTaskSection() {
  const { sensorMapping, setMainTaskData, setError } = useIMUStore();
  const [status, setStatus] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  const handleFilesSelected = async (files: File[]) => {
    if (!sensorMapping) {
      setStatus({ type: "error", message: "Please upload the sensor placement file first." });
      return;
    }

    setSelectedFiles(files);
    setIsLoading(true);
    setStatus(null);

    try {
      // Validate that we have all required sensors
      const requiredSensors = ["pelvis", "thigh_l", "shank_l", "foot_l", "thigh_r", "shank_r", "foot_r"];
      const requiredIDs = Object.keys(sensorMapping).filter(id => {
        const sensorName = sensorMapping[id].toLowerCase();
        return requiredSensors.includes(sensorName);
      });

      if (requiredIDs.length < requiredSensors.length) {
        throw new Error("The sensor placement file does not include all required lower-limb sensors.");
      }

      // Check if we have files for all required sensors
      const matchedFiles = files.filter(file => {
        const lowerName = file.name.toLowerCase();
        return requiredIDs.some(id => lowerName.includes(id.toLowerCase()));
      });

      if (matchedFiles.length < requiredIDs.length) {
        const foundIDs = matchedFiles.map(file => {
          const lowerName = file.name.toLowerCase();
          return requiredIDs.find(id => lowerName.includes(id.toLowerCase()));
        }).filter(Boolean);
        const missingIDs = requiredIDs.filter(id => !foundIDs.includes(id));
        const missingSensors = missingIDs.map(id => sensorMapping[id]);
        throw new Error(`Missing main task files for: ${missingSensors.join(", ")}`);
      }

      // Upload the files
      const response = await uploadMainTask(files);
      
      // Process the response and update store
      // Note: You'll need to implement the data processing logic here
      setStatus({ 
        type: "success", 
        message: `Main task data uploaded successfully. Processed ${files.length} files.` 
      });
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Error processing main task files";
      setStatus({ type: "error", message: errorMessage });
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUploadError = (error: string) => {
    setStatus({ type: "error", message: error });
    setError(error);
  };

  const getRequiredSensorsInfo = () => {
    if (!sensorMapping) return "Upload sensor mapping first to see required sensors.";
    
    const requiredSensors = ["pelvis", "thigh_l", "shank_l", "foot_l", "thigh_r", "shank_r", "foot_r"];
    const availableSensors = Object.values(sensorMapping).map(name => name.toLowerCase());
    const missingSensors = requiredSensors.filter(sensor => !availableSensors.includes(sensor));
    
    if (missingSensors.length > 0) {
      return `Missing sensors in mapping: ${missingSensors.join(", ")}`;
    }
    
    return `Required sensors: ${requiredSensors.join(", ")}`;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Main Task Data
          <div title="Upload the main task TXT files for running IK.">
            <Info className="w-4 h-4 text-[#C41230] cursor-help" />
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <FileUpload
          onFilesSelected={handleFilesSelected}
          onUploadError={handleUploadError}
          accept=".txt,.csv"
          multiple={true}
          maxFiles={20}
          maxSize={100}
          disabled={isLoading || !sensorMapping}
          description="Upload main task files containing IMU sensor data for all required body segments"
        />

        {/* Requirements Info */}
        <Alert>
          <AlertDescription className="text-xs">
            {getRequiredSensorsInfo()}
          </AlertDescription>
        </Alert>

        {/* Status Messages */}
        {status && (
          <Alert variant={status.type === "error" ? "destructive" : "default"}>
            <AlertDescription>{status.message}</AlertDescription>
          </Alert>
        )}
        
        {isLoading && (
          <div className="text-sm text-gray-600">
            Processing main task files...
          </div>
        )}

        {/* File Summary */}
        {selectedFiles.length > 0 && !isLoading && (
          <div className="bg-green-50 p-3 rounded border border-green-200">
            <p className="text-sm text-green-800 font-medium">
              ✓ {selectedFiles.length} main task files ready for processing
            </p>
            <div className="text-xs text-green-600 mt-1">
              {selectedFiles.map(file => file.name).join(", ")}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
} 