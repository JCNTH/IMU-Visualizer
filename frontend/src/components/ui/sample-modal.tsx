"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Modal, ModalHeader, ModalBody, ModalFooter } from "@/components/ui/modal";
import { Download, FileText, Folder } from "lucide-react";

interface SampleModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  type: "sensor_mapping" | "calibration" | "main_task";
}

const sampleData = {
  sensor_mapping: {
    filename: "sensor_placement.txt",
    description: "Maps sensor IDs to body positions. Each line contains: body_part sensor_id",
    content: `sensor_name id
chest   00B4D7D4
pelvis  00B4D7D3
thigh_l 00B4D7FD
shank_l 00B4D7CE
foot_l  00B4D7FF
thigh_r 00B4D6D1
shank_r 00B4D7FB
foot_r  00B4D7FE`,
    downloadUrl: "/sample_data/sensor_placement.txt"
  },
  calibration: {
    filename: "Calibration Task Folders",
    description: "Folders containing IMU data for different calibration movements. Each folder represents a calibration task (e.g., 'static_standing', 'treadmill_walking').",
    content: `Folder Structure:
├── static_standing/
│   ├── t0_static_pose_001-000_00B4D7D3.txt
│   ├── t0_static_pose_001-000_00B4D7CE.txt
│   └── ... (one file per sensor)
└── treadmill_walking/
    ├── t2_treadmill_walking_001-000_00B4D7D3.txt
    ├── t2_treadmill_walking_001-000_00B4D7CE.txt
    └── ... (one file per sensor)

File Format (each .txt file):
// Start Time: Unknown
// Update Rate: 40.0Hz
// Filter Profile: human (46.1)
// Firmware Version: 4.6.0
PacketCounter	SampleTimeFine	Acc_X	Acc_Y	Acc_Z	Gyr_X	Gyr_Y	Gyr_Z	Mag_X	Mag_Y	Mag_Z	Quat_q0	Quat_q1	Quat_q2	Quat_q3
23593	9.473106	-1.742208	-1.880188	0.007790	-0.000003	-0.007713	-0.791504	0.247559	-0.282959	0.635440	-0.163901	-0.754280	-0.020348
...`,
    downloadUrl: "/sample_data/task_calibration.zip"
  },
  main_task: {
    filename: "Main Task Folder",
    description: "Folder containing IMU data for the main movement to analyze. Same format as calibration files.",
    content: `Folder Structure:
└── task_main/
    ├── t4_lat_step_001-000_00B4D7D3.txt
    ├── t4_lat_step_001-000_00B4D7CE.txt
    └── ... (one file per sensor)

File Format (each .txt file):
// Start Time: Unknown
// Update Rate: 40.0Hz
// Filter Profile: human (46.1)
// Firmware Version: 4.6.0
PacketCounter	SampleTimeFine	Acc_X	Acc_Y	Acc_Z	Gyr_X	Gyr_Y	Gyr_Z	Mag_X	Mag_Y	Mag_Z	Quat_q0	Quat_q1	Quat_q2	Quat_q3
23593	9.473106	-1.742208	-1.880188	0.007790	-0.000003	-0.007713	-0.791504	0.247559	-0.282959	0.635440	-0.163901	-0.754280	-0.020348
...`,
    downloadUrl: "/sample_data/task_main.zip"
  }
};

export function SampleModal({ isOpen, onClose, title, type }: SampleModalProps) {
  const sample = sampleData[type];

  const handleDownload = () => {
    // Create a download link for the sample file
    const link = document.createElement('a');
    link.href = sample.downloadUrl;
    link.download = sample.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <ModalHeader>
        <div className="flex items-center gap-2">
          {type === "sensor_mapping" ? <FileText className="w-5 h-5" /> : <Folder className="w-5 h-5" />}
          {title}
        </div>
      </ModalHeader>
      
      <ModalBody>
        <div className="space-y-4">
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Expected Format:</h3>
            <p className="text-sm text-gray-600 mb-3">{sample.description}</p>
          </div>
          
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Sample Content:</h4>
            <div className="bg-gray-50 border rounded-md p-3 max-h-96 overflow-y-auto">
              <pre className="text-xs font-mono text-gray-800 whitespace-pre-wrap">
                {sample.content}
              </pre>
            </div>
          </div>
          
          {type === "sensor_mapping" && (
            <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
              <h4 className="font-medium text-blue-900 mb-2">Required Body Segments:</h4>
              <div className="text-sm text-blue-800">
                <div className="grid grid-cols-2 gap-2">
                  <span>• <code>pelvis</code> (required)</span>
                  <span>• <code>chest</code></span>
                  <span>• <code>thigh_l</code> (left thigh)</span>
                  <span>• <code>thigh_r</code> (right thigh)</span>
                  <span>• <code>shank_l</code> (left shank)</span>
                  <span>• <code>shank_r</code> (right shank)</span>
                  <span>• <code>foot_l</code> (left foot)</span>
                  <span>• <code>foot_r</code> (right foot)</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </ModalBody>
      
      <ModalFooter>
        <Button variant="outline" onClick={onClose}>
          Close
        </Button>
        <Button onClick={handleDownload} className="flex items-center gap-2">
          <Download className="w-4 h-4" />
          Download Sample
        </Button>
      </ModalFooter>
    </Modal>
  );
} 