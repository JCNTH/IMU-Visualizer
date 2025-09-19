"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { ChevronDown, ChevronRight, CheckCircle, Settings } from "lucide-react";
import { useIMUStore } from "@/store/imuStore";
import { cn } from "@/lib/utils";

export function IKParametersSection() {
  const { ikParameters, setIKParameters } = useIMUStore();
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Consider parameters configured if they're not all defaults
  const isCompleted = ikParameters.selected_setup !== "mm" || 
                     ikParameters.filter_type !== "Xsens" || 
                     ikParameters.dim !== "9D" || 
                     !ikParameters.remove_offset;

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
            <h3 className="font-medium text-gray-900">IK Parameters</h3>
          </div>
          {isCompleted && (
            <CheckCircle className="w-4 h-4 text-green-500" />
          )}
        </div>
        <Settings className="w-4 h-4 text-gray-400" />
      </Button>

      {/* Collapsible Content */}
      <div className={cn(
        "transition-all duration-200",
        isCollapsed ? "max-h-0 opacity-0 overflow-hidden" : "opacity-100"
      )}>
        <div className="pt-2 space-y-3">
                  {/* Sensor Setup */}
          <div className="space-y-1">
            <Label htmlFor="setup-select" className="text-xs">Sensor Setup:</Label>
          <Select 
            value={ikParameters.selected_setup} 
            onValueChange={(value) => setIKParameters({ selected_setup: value })}
          >
            <SelectTrigger id="setup-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="mm">mm (Default)</SelectItem>
              <SelectItem value="hh">hh</SelectItem>
              <SelectItem value="ll">ll</SelectItem>
              <SelectItem value="ff">ff</SelectItem>
            </SelectContent>
          </Select>
        </div>

                  {/* Filter Type */}
          <div className="space-y-1">
            <Label htmlFor="filter-select" className="text-xs">Filter Type:</Label>
          <Select 
            value={ikParameters.filter_type} 
            onValueChange={(value) => setIKParameters({ filter_type: value })}
          >
            <SelectTrigger id="filter-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Xsens">Xsens (Default)</SelectItem>
              <SelectItem value="MAH">MAH</SelectItem>
              <SelectItem value="VQF">VQF</SelectItem>
              <SelectItem value="MAD">MAD</SelectItem>
              <SelectItem value="EKF">EKF</SelectItem>
            </SelectContent>
          </Select>
        </div>

                  {/* Dimensions */}
          <div className="space-y-1">
            <Label htmlFor="dim-select" className="text-xs">Dimensions:</Label>
          <Select 
            value={ikParameters.dim} 
            onValueChange={(value) => setIKParameters({ dim: value })}
          >
            <SelectTrigger id="dim-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="9D">9D (Default)</SelectItem>
              <SelectItem value="6D">6D</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Remove Offset */}
        <div className="flex items-center space-x-2">
          <Checkbox
            id="remove-offset"
            checked={ikParameters.remove_offset}
            onCheckedChange={(checked) => setIKParameters({ remove_offset: checked as boolean })}
          />
          <Label htmlFor="remove-offset" className="text-sm font-medium">
            Remove Offset
          </Label>
        </div>

          {/* Parameter Summary */}
          <div className="bg-gray-50 p-3 rounded text-xs space-y-1">
            <p><span className="font-medium">Setup:</span> {ikParameters.selected_setup}</p>
            <p><span className="font-medium">Filter:</span> {ikParameters.filter_type}</p>
            <p><span className="font-medium">Dimensions:</span> {ikParameters.dim}</p>
            <p><span className="font-medium">Remove Offset:</span> {ikParameters.remove_offset ? "Yes" : "No"}</p>
          </div>

          {/* Completion Status */}
          {isCompleted && (
            <div className="text-xs text-green-600 bg-green-50 p-2 rounded">
              ✓ Parameters configured (non-default settings)
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 