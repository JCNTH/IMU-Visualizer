"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Info, ChevronDown, ChevronRight, CheckCircle, Eye } from "lucide-react";
import { FileUpload } from "@/components/ui/file-upload";
import { SampleModal } from "@/components/ui/sample-modal";
import { uploadSensorMapping } from "@/lib/api";
import { useIMUStore } from "@/store/imuStore";
import { cn } from "@/lib/utils";

export function SensorMappingSection() {
  const { sensorMapping, setSensorMapping, setError } = useIMUStore();
  const [status, setStatus] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [showSampleModal, setShowSampleModal] = useState(false);

  const handleFilesSelected = async (files: File[]) => {
    if (files.length === 0) return;
    
    const file = files[0];
    setIsLoading(true);
    setStatus(null);

    try {
      const response = await uploadSensorMapping(file);
      setSensorMapping(response.mapping);
      setStatus({ 
        type: "success", 
        message: `Sensor mapping loaded successfully. Found ${Object.keys(response.mapping).length} sensors.` 
      });
      // Auto-collapse after successful upload
      setIsCollapsed(true);
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

  const isCompleted = sensorMapping && Object.keys(sensorMapping).length > 0;

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
            <h3 className="font-medium text-gray-900">Sensor ID Mapping</h3>
          </div>
          <div className="flex items-center gap-2">
            {isCompleted && (
              <>
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span className="text-sm text-green-600 font-medium">
                  {Object.keys(sensorMapping).length} sensors mapped
                </span>
              </>
            )}
          </div>
        </div>
        <div title="Upload a text or CSV file (sensor_placement.txt) that maps sensor IDs to sensor positions.">
          <Info className="w-4 h-4 text-[#C41230] cursor-help" />
        </div>
      </Button>

      {/* Collapsed Summary */}
      {isCollapsed && isCompleted && (
        <div className="pt-2">
          <div className="bg-green-50 border border-green-200 rounded-md p-2">
            <div className="text-xs text-green-800 font-medium mb-2">
              Sensor Mappings ({Object.keys(sensorMapping).length} sensors)
            </div>
            <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-green-700">
              {Object.entries(sensorMapping).map(([sensorId, bodyPart]) => (
                <div key={sensorId} className="flex justify-between">
                  <span className="font-mono font-medium">{sensorId}:</span>
                  <span className="truncate">{bodyPart}</span>
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
        <div className="pt-2 space-y-2">
          {!isCompleted && (
            <div className="space-y-3">
              <FileUpload
                onFilesSelected={handleFilesSelected}
                onUploadError={handleUploadError}
                accept=".csv,.txt"
                multiple={false}
                maxFiles={1}
                maxSize={10}
                disabled={isLoading}
                description="Upload sensor placement file that maps sensor IDs to body positions"
              />
              
              <div className="flex justify-center">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowSampleModal(true)}
                  className="flex items-center gap-2 text-xs"
                >
                  <Eye className="w-3 h-3" />
                  View Sample Format
                </Button>
              </div>
            </div>
          )}
          
          {isCompleted && !isCollapsed && (
            <div className="space-y-3">
              <div className="bg-green-50 border border-green-200 rounded-md p-3">
                <div className="text-sm text-green-800 font-medium mb-3">
                  Sensor Mappings ({Object.keys(sensorMapping).length} sensors)
                </div>
                <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
                  {Object.entries(sensorMapping).map(([sensorId, bodyPart]) => (
                    <div key={sensorId} className="flex justify-between items-center">
                      <span className="font-mono font-medium text-gray-700">{sensorId}:</span>
                      <span className="text-green-700 font-medium">{bodyPart}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="flex justify-between items-center">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSensorMapping({});
                    setStatus(null);
                  }}
                  className="text-xs"
                >
                  Clear Mapping
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsCollapsed(true)}
                  className="text-xs"
                >
                  Minimize
                </Button>
              </div>
            </div>
          )}
          
          {status && !isCompleted && (
            <Alert variant={status.type === "error" ? "destructive" : "default"} className="py-2">
              <AlertDescription className="text-xs">{status.message}</AlertDescription>
            </Alert>
          )}
          
          {isLoading && (
            <div className="text-xs text-gray-600">
              Processing sensor mapping file...
            </div>
          )}
        </div>
      </div>
      
      <SampleModal
        isOpen={showSampleModal}
        onClose={() => setShowSampleModal(false)}
        title="Sample Sensor Mapping File"
        type="sensor_mapping"
      />
    </div>
  );
} 