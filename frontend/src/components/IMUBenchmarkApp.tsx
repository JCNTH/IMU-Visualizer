"use client";

import { SensorMappingSection } from "@/components/sections/SensorMappingSection";
import { CalibrationSection } from "@/components/sections/CalibrationSection";
import { MainTaskSection } from "@/components/sections/MainTaskSection";
import { IKParametersSection } from "@/components/sections/IKParametersSection";
import { ActionButtonsSection } from "@/components/sections/ActionButtonsSection";
import { IMUVisualization } from "@/components/visualization/IMUVisualization";

export function IMUBenchmarkApp() {

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Left Panel - Controls */}
      <div className="w-[500px] bg-white p-6 overflow-y-auto border-r">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white bg-[#C41230] px-4 py-3 rounded text-center mb-6">
            MBL IMUViz
          </h1>
        </div>

        {/* Sections */}
        <div className="space-y-6">
          <SensorMappingSection />
          <CalibrationSection />
          <MainTaskSection />
          <IKParametersSection />
          <ActionButtonsSection />
        </div>
      </div>

      {/* Right Panel - Visualization */}
      <div className="flex-1 relative">
        <IMUVisualization />
      </div>
    </div>
  );
} 