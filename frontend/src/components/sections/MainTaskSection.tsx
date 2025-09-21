"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertModal } from "@/components/ui/modal";
import { Info, ChevronDown, ChevronRight, CheckCircle, Folder, Files, Eye } from "lucide-react";
import { FileUpload } from "@/components/ui/file-upload";
import { SampleModal } from "@/components/ui/sample-modal";
import { uploadMainTask } from "@/lib/api";
import { useIMUStore } from "@/store/imuStore";
import { cn } from "@/lib/utils";

export function MainTaskSection() {
  const { sensorMapping, setMainTaskData, setError } = useIMUStore();
  const [status, setStatus] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [showSampleModal, setShowSampleModal] = useState(false);
  const [alertModal, setAlertModal] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    type: "info" | "warning" | "error" | "success";
  }>({ isOpen: false, title: "", message: "", type: "info" });

  const handleFilesSelected = async (files: File[]) => {
    if (!sensorMapping) {
      setAlertModal({
        isOpen: true,
        title: "Sensor Mapping Required",
        message: "Please upload the sensor placement file first before uploading main task data.",
        type: "warning"
      });
      return;
    }

    setSelectedFiles(files);
    setIsLoading(true);
    setStatus(null);

    try {
      const requiredSensors = ["pelvis", "thigh_l", "shank_l", "foot_l", "thigh_r", "shank_r", "foot_r"];
      const requiredIDs = Object.keys(sensorMapping).filter(id => {
        const sensorName = sensorMapping[id].toLowerCase();
        return requiredSensors.includes(sensorName);
      });

      if (requiredIDs.length < requiredSensors.length) {
        throw new Error("The sensor placement file does not include all required lower-limb sensors.");
      }

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

      const response = await uploadMainTask(files);
      console.log("Main task upload response:", response);
      console.log("Main task data:", response.main_task_data);
      
      setMainTaskData(response.main_task_data);
      setStatus({ 
        type: "success", 
        message: `Main task data uploaded successfully. Processed ${files.length} files.` 
      });
      
      // Auto-collapse after successful upload
      setIsCollapsed(true);
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Error processing main task files";
      setStatus({ type: "error", message: errorMessage });
      setError(errorMessage);
      
      // Show error in modal
      setAlertModal({
        isOpen: true,
        title: "Upload Failed",
        message: errorMessage,
        type: "error"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleUploadError = (error: string) => {
    setStatus({ type: "error", message: error });
    setError(error);
    
    // Show error in modal
    setAlertModal({
      isOpen: true,
      title: "Upload Error",
      message: error,
      type: "error"
    });
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

  const isCompleted = selectedFiles.length > 0 && status?.type === "success";

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
            <h3 className="font-medium text-gray-900">Main Task Data</h3>
          </div>
          <div className="flex items-center gap-2">
            {isCompleted && (
              <>
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span className="text-sm text-green-600 font-medium">
                  {selectedFiles.length} files uploaded
                </span>
              </>
            )}
          </div>
        </div>
        <div title="Upload the main task TXT files for running IK.">
          <Info className="w-4 h-4 text-[#C41230] cursor-help" />
        </div>
      </Button>

      {/* Collapsed Summary */}
      {isCollapsed && isCompleted && (
        <div className="pt-2">
          <div className="bg-green-50 border border-green-200 rounded-md p-2">
            <div className="text-xs text-green-800 font-medium mb-2">
              Main Task Data ({selectedFiles.length} files)
            </div>
            <div className="text-xs text-green-700">
              Required sensors: {getRequiredSensorsInfo().replace("Required sensors: ", "")}
            </div>
            <div className="text-xs text-gray-600 mt-1">
              Files: {selectedFiles.map(f => f.name).join(", ").slice(0, 100)}
              {selectedFiles.map(f => f.name).join(", ").length > 100 ? "..." : ""}
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
          {!isCompleted ? (
            <>
              <div className="space-y-2">
                <FileUpload
                  onFilesSelected={handleFilesSelected}
                  onUploadError={handleUploadError}
                  accept=".txt,.csv"
                  multiple={true}
                  maxFiles={50}
                  maxSize={100}
                  allowFolders={true}
                  disabled={isLoading || !sensorMapping}
                  description="Upload main task folder containing IMU sensor data for all required body segments"
                />
                <div className="flex justify-between items-center">
                  <div className="text-xs text-gray-600 bg-blue-50 p-2 rounded border border-blue-200 flex-1">
                    💡 <strong>Folder upload recommended:</strong> Select your main task folder containing all IMU data files.
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

              {/* Requirements Info */}
              <Alert className="py-2">
                <AlertDescription className="text-xs">
                  {getRequiredSensorsInfo()}
                </AlertDescription>
              </Alert>
            </>
          ) : (
            <div className="space-y-3">
              <div className="bg-green-50 border border-green-200 rounded-md p-3">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-green-800 font-medium">
                    ✓ {selectedFiles.length} files uploaded successfully
                  </span>
                  <Button
                    onClick={() => {
                      setSelectedFiles([]);
                      setStatus(null);
                      setIsCollapsed(false);
                    }}
                    size="sm"
                    variant="outline"
                    className="h-6 text-xs"
                  >
                    Change Files
                  </Button>
                </div>
                <div className="text-xs text-green-700 mb-1">
                  Required sensors: {getRequiredSensorsInfo().replace("Required sensors: ", "")}
                </div>
                <div className="text-xs text-gray-600">
                  Files: {selectedFiles.map(f => f.name).join(", ")}
                </div>
              </div>
              
              <div className="flex justify-end">
                <Button 
                  onClick={() => setIsCollapsed(true)} 
                  variant="outline" 
                  size="sm" 
                  className="text-xs"
                >
                  Minimize
                </Button>
              </div>
            </div>
          )}

          {/* Status Messages */}
          {status && !isCompleted && (
            <Alert variant={status.type === "error" ? "destructive" : "default"} className="py-2">
              <AlertDescription className="text-xs">{status.message}</AlertDescription>
            </Alert>
          )}
          
          {isLoading && (
            <div className="text-xs text-gray-600">
              Processing main task files...
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
        title="Sample Main Task Data"
        type="main_task"
      />
    </div>
  );
} 