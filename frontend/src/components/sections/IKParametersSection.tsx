"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { useIMUStore } from "@/store/imuStore";

export function IKParametersSection() {
  const { ikParameters, setIKParameters } = useIMUStore();

  return (
    <Card>
      <CardHeader>
        <CardTitle>IK Parameters</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Sensor Setup */}
        <div className="space-y-2">
          <Label htmlFor="setup-select">Sensor Setup:</Label>
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
        <div className="space-y-2">
          <Label htmlFor="filter-select">Filter Type:</Label>
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
        <div className="space-y-2">
          <Label htmlFor="dim-select">Dimensions:</Label>
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
      </CardContent>
    </Card>
  );
} 