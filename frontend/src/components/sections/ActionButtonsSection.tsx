"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Play, Download, Video, FileText, BarChart3 } from "lucide-react";
import { runIK, downloadCSV, downloadGraphsZip, createVideoStream } from "@/lib/api";
import { useIMUStore } from "@/store/imuStore";

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

  const validateInputs = (): string[] => {
    const missing = [];
    if (!sensorMapping) missing.push("Sensor Mapping file");
    if (!mainTaskData || Object.keys(mainTaskData).length === 0) missing.push("Main Task data");
    if (!calibrationData || Object.keys(calibrationData).length === 0) missing.push("Calibration Task data");
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
      });

      if (response.status === "success" && response.ik_results) {
        setIKResults(response.ik_results);
        setProcessingStatus("IK processing completed successfully!");
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
    } catch (error) {
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
    } catch (error) {
      setError("Failed to download graphs");
    }
  };

  const handleGenerateVideo = () => {
    setIsGeneratingVideo(true);
    setVideoProgress(0);

    const params = {
      modelPath: "/Users/julianng-thow-hing/Documents/GitHub/mbl_osim2obj/Motions/subject22/scaled_model.osim",
      motPath: "/Users/julianng-thow-hing/Documents/GitHub/mbl_osim2obj/Motions/subject6/ik2.mot",
      calibPath: "/Users/julianng-thow-hing/Documents/GitHub/mbl_osim2obj/Motions/subject6/calib.npz",
      subject: "subject22"
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

  return (
    <Card>
      <CardHeader>
        <CardTitle>Actions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
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
          <div className="space-y-2">
            <Button
              onClick={handleDownloadCSV}
              variant="outline"
              className="w-full flex items-center gap-2"
            >
              <FileText className="w-4 h-4" />
              Download CSV Results
            </Button>
            
            <Button
              onClick={handleDownloadGraphs}
              variant="outline"
              className="w-full flex items-center gap-2"
            >
              <BarChart3 className="w-4 h-4" />
              Download Graphs (ZIP)
            </Button>
          </div>
        )}

        {/* Generate Video Button */}
        <Button
          onClick={handleGenerateVideo}
          disabled={!canGenerateVideo}
          variant="outline"
          className="w-full flex items-center gap-2"
        >
          <Video className="w-4 h-4" />
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
          <Alert variant="destructive">
            <AlertDescription>
              Missing: {validateInputs().join(", ")}
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
} 