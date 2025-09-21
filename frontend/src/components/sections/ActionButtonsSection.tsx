"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Play, Video, FileText, BarChart3, ChevronDown, ChevronRight, CheckCircle, Zap } from "lucide-react";
import { runIK, downloadCSV, downloadGraphsZip, createVideoStream } from "@/lib/api";
import { UnmappedSensorsAlert } from "@/components/ui/unmapped-sensors-alert";
import { useIMUStore } from "@/store/imuStore";
import { cn } from "@/lib/utils";

export function ActionButtonsSection() {
  const { 
    sensorMapping, 
    calibrationData, 
    mainTaskData, 
    ikParameters, 
    ikResults,
    setIKResults, 
    setLoading,
    setError 
  } = useIMUStore();
  
  const [isProcessing, setIsProcessing] = useState(false);
  const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);
  const [videoProgress, setVideoProgress] = useState(0);
  const [processingStatus, setProcessingStatus] = useState<string>("");
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [unmappedSensors, setUnmappedSensors] = useState<Array<{file: string; sensor_id: string}>>([]);

  const validateInputs = (): string[] => {
    const missing = [];
    console.log("Validation check - Store state:", { sensorMapping, mainTaskData, calibrationData });
    
    if (!sensorMapping) missing.push("Sensor Mapping file");
    if (!mainTaskData || Object.keys(mainTaskData).length === 0) missing.push("Main Task data");
    if (!calibrationData || Object.keys(calibrationData).length === 0) missing.push("Calibration Task data");
    
    console.log("Missing inputs:", missing);
    return missing;
  };

  const handleRunIK = async () => {
    const missingInputs = validateInputs();
    if (missingInputs.length > 0) {
      setError(`Missing required inputs: ${missingInputs.join(", ")}`);
      return;
    }

    setIsProcessing(true);
    setLoading(true);
    setProcessingStatus("Running inverse kinematics calculation...");

    try {
      const response = await runIK({
        ...ikParameters,
        main_task_data: mainTaskData,
        calibration_data: calibrationData,
        sensor_mapping: sensorMapping || {},
      });

      if (response.status === "success" && response.ik_results) {
        setIKResults(response.ik_results);
        
        // Check for unmapped sensors and show warning
        if (response.unmapped_sensors && response.unmapped_sensors.length > 0) {
          const unmappedCount = response.unmapped_sensors.length;
          setUnmappedSensors(response.unmapped_sensors);
          setProcessingStatus(`IK processing completed successfully! (${unmappedCount} unmapped sensors were skipped)`);
          
          // Show detailed warning about unmapped sensors
          const unmappedList = response.unmapped_sensors.map(s => s.sensor_id).join(", ");
          console.warn(`Unmapped sensors skipped: ${unmappedList}`);
        } else {
          setUnmappedSensors([]);
          setProcessingStatus("IK processing completed successfully!");
        }
      } else {
        throw new Error(response.message || "IK processing failed");
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to run inverse kinematics";
      setError(errorMessage);
      setProcessingStatus("");
    } finally {
      setIsProcessing(false);
      setLoading(false);
    }
  };

  const handleDownloadCSV = async () => {
    try {
      const blob = await downloadCSV();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "ik_results.csv";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch {
      setError("Failed to download CSV file");
    }
  };

  const handleDownloadGraphs = async () => {
    try {
      const blob = await downloadGraphsZip();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "ik_results_graphs.zip";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch {
      setError("Failed to download graphs");
    }
  };

  const handleGenerateVideo = () => {
    setIsGeneratingVideo(true);
    setVideoProgress(0);

    // Provide dummy paths (backend will ignore these and use local files)
    const params = {
      modelPath: "dummy_model.osim",  // Backend ignores this
      motPath: "dummy_motion.mot",    // Backend ignores this  
      calibPath: "dummy_calib.npz",   // Backend ignores this
      subject: "frontend_demo"        // Only this matters
    };

    const eventSource = createVideoStream(params);

    eventSource.onmessage = (event) => {
      console.log("Video generation:", event.data);
    };

    eventSource.addEventListener("progress", (event) => {
      const progress = parseInt(event.data, 10);
      setVideoProgress(progress);
    });

    eventSource.addEventListener("done", (event) => {
      if (event.data === "success") {
        setVideoProgress(100);
        setProcessingStatus("Video generation completed!");
      }
      setIsGeneratingVideo(false);
      eventSource.close();
    });

    eventSource.onerror = () => {
      setError("Video generation failed");
      setIsGeneratingVideo(false);
      eventSource.close();
    };
  };

  const canRunIK = !isProcessing && validateInputs().length === 0;
  const canGenerateVideo = !isGeneratingVideo && ikResults;
  const canDownload = ikResults && !isProcessing;
  const isCompleted = ikResults !== null;

  return (
    <div className="pb-4">
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
            <h3 className="font-medium text-gray-900">Actions</h3>
          </div>
          {isCompleted && (
            <CheckCircle className="w-4 h-4 text-green-500" />
          )}
        </div>
        <Zap className="w-4 h-4 text-gray-400" />
      </Button>

      {/* Collapsible Content */}
      <div className={cn(
        "transition-all duration-200",
        isCollapsed ? "max-h-0 opacity-0 overflow-hidden" : "opacity-100"
      )}>
        <div className="pt-2 space-y-2">
          {/* Run IK Button */}
          <Button
            onClick={handleRunIK}
            disabled={!canRunIK}
            className="w-full bg-[#C41230] hover:bg-[#a10e25] flex items-center gap-2"
          >
            <Play className="w-4 h-4" />
            {isProcessing ? "Processing..." : "Run IK"}
          </Button>

          {/* Processing Status */}
          {processingStatus && (
            <Alert>
              <AlertDescription>{processingStatus}</AlertDescription>
            </Alert>
          )}

          {/* Download Buttons */}
          {canDownload && (
            <div className="grid grid-cols-2 gap-1">
              <Button
                onClick={handleDownloadCSV}
                variant="outline"
                size="sm"
                className="flex items-center gap-1 text-xs"
              >
                <FileText className="w-3 h-3" />
                CSV
              </Button>
              
              <Button
                onClick={handleDownloadGraphs}
                variant="outline"
                size="sm"
                className="flex items-center gap-1 text-xs"
              >
                <BarChart3 className="w-3 h-3" />
                Graphs
              </Button>
            </div>
          )}

          {/* Generate Video Button */}
          <Button
            onClick={handleGenerateVideo}
            disabled={!canGenerateVideo}
            variant="outline"
            size="sm"
            className="w-full flex items-center gap-1 text-xs"
          >
            <Video className="w-3 h-3" />
            {isGeneratingVideo ? "Generating..." : "Generate Video"}
          </Button>

          {/* Video Generation Progress */}
          {isGeneratingVideo && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Generating Video</span>
                <span>{videoProgress}%</span>
              </div>
              <Progress value={videoProgress} className="h-2" />
            </div>
          )}

          {/* Validation Messages */}
          {validateInputs().length > 0 && (
            <Alert variant="destructive" className="py-2">
              <AlertDescription className="text-xs">
                Missing: {validateInputs().join(", ")}
                <div className="mt-1 text-xs opacity-75">
                  Debug: Sensor mapping: {sensorMapping ? "✓" : "❌"}, 
                  Main task: {mainTaskData && Object.keys(mainTaskData).length > 0 ? "✓" : "❌"}, 
                  Calibration: {calibrationData && Object.keys(calibrationData).length > 0 ? "✓" : "❌"}
                </div>
              </AlertDescription>
            </Alert>
          )}

          {/* Unmapped Sensors Warning */}
          <UnmappedSensorsAlert 
            unmappedSensors={unmappedSensors}
            className="mt-2"
          />

          {/* Completion Status */}
          {isCompleted && (
            <div className="text-xs text-green-600 bg-green-50 p-2 rounded">
              ✓ IK processing completed successfully
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 