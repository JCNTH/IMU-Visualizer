"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Info } from "lucide-react";
import { FileUpload } from "@/components/ui/file-upload";
import { uploadSensorMapping } from "@/lib/api";
import { useIMUStore } from "@/store/imuStore";

export function SensorMappingSection() {
  const { setSensorMapping, setError } = useIMUStore();
  const [status, setStatus] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleFilesSelected = async (files: File[]) => {
    if (files.length === 0) return;
    
    const file = files[0]; // Take the first file since multiple=false
    setIsLoading(true);
    setStatus(null);

    try {
      const response = await uploadSensorMapping(file);
      setSensorMapping(response.mapping);
      setStatus({ 
        type: "success", 
        message: `Sensor mapping loaded successfully. Found ${Object.keys(response.mapping).length} sensors.` 
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Error parsing sensor mapping file";
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

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Sensor ID Mapping
          <div title="Upload a text or CSV file (sensor_placement.txt) that maps sensor IDs (e.g., '00B4D7D3') to sensor positions.">
            <Info className="w-4 h-4 text-[#C41230] cursor-help" />
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <FileUpload
          onFilesSelected={handleFilesSelected}
          onUploadError={handleUploadError}
          accept=".csv,.txt"
          multiple={false}
          maxFiles={1}
          maxSize={10} // 10MB for mapping files
          disabled={isLoading}
          description="Upload sensor placement file that maps sensor IDs to body positions"
        />
        
        {status && (
          <Alert variant={status.type === "error" ? "destructive" : "default"}>
            <AlertDescription>{status.message}</AlertDescription>
          </Alert>
        )}
        
        {isLoading && (
          <div className="text-sm text-gray-600">
            Processing sensor mapping file...
          </div>
        )}
      </CardContent>
    </Card>
  );
} 