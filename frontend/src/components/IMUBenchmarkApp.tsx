"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { AppHeader } from "@/components/layout/AppHeader";
import { SensorMappingSection } from "@/components/sections/SensorMappingSection";
import { SensorPlacementSection } from "@/components/sections/SensorPlacementSection";
import { CalibrationSection } from "@/components/sections/CalibrationSection";
import { MainTaskSection } from "@/components/sections/MainTaskSection";
import { IKParametersSection } from "@/components/sections/IKParametersSection";
import { ActionButtonsSection } from "@/components/sections/ActionButtonsSection";
import { IMUVisualization } from "@/components/visualization/IMUVisualization";

const SIDEBAR_WIDTH = "500px";
const SIDEBAR_WIDTH_COLLAPSED = "0px";

export function IMUBenchmarkApp() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div 
      className="h-screen flex flex-col bg-gray-50"
      style={{
        "--sidebar-width": sidebarCollapsed ? SIDEBAR_WIDTH_COLLAPSED : SIDEBAR_WIDTH,
      } as React.CSSProperties}
    >
      {/* App Header */}
      <AppHeader 
        onSidebarToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        sidebarCollapsed={sidebarCollapsed}
      />

      {/* Main Content */}
      <div className="flex-1 flex min-h-0">
        {/* Sidebar */}
        <aside 
          className="bg-white border-r border-gray-200 transition-all duration-300 ease-in-out relative"
          style={{ 
            width: "var(--sidebar-width)",
            minWidth: "var(--sidebar-width)",
            maxWidth: "var(--sidebar-width)"
          }}
        >
          {/* Sidebar Content */}
          <div className={`h-full overflow-hidden transition-opacity duration-300 ${
            sidebarCollapsed ? "opacity-0 pointer-events-none" : "opacity-100"
          }`}>
            <div className="h-full overflow-y-auto p-4">
              <div className="space-y-4">
                <SensorMappingSection />
                <SensorPlacementSection />
                <CalibrationSection />
                <MainTaskSection />
                <IKParametersSection />
                <ActionButtonsSection />
              </div>
            </div>
          </div>

          {/* Collapse/Expand Button */}
          <Button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            variant="ghost"
            size="sm"
            className="absolute top-4 -right-12 z-40 bg-white border border-gray-200 shadow-sm hover:bg-gray-50"
          >
            {sidebarCollapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <ChevronLeft className="w-4 h-4" />
            )}
          </Button>
        </aside>

        {/* Main Content Area - Naturally fills remaining space */}
        <main className="flex-1 min-w-0 relative transition-all duration-300 ease-in-out">
          <IMUVisualization sidebarCollapsed={sidebarCollapsed} />
        </main>
      </div>
    </div>
  );
} 