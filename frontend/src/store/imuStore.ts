import { create } from "zustand";
import type { 
  SensorMapping, 
  SensorData as APISensorData, 
  TaskSensorData, 
  CalibrationTaskData 
} from "@/lib/api";

export interface SensorData {
  id: string;
  fileName: string;
  content: string;
}

export interface IKParameters {
  subject: number;
  task: string;
  selected_setup: string;
  filter_type: string;
  dim: string;
  remove_offset: boolean;
}

export interface IKResults {
  joint_angles?: { [joint: string]: number[] };
  time?: number[];
  [key: string]: unknown;
}

export interface SensorPlacement {
  type: string;
  position: { x: number; y: number; z: number };
  rotation: { x: number; y: number; z: number };
  placementView: string;
}

interface IMUStore {
  // State
  sensorMapping: SensorMapping | null;
  calibrationData: CalibrationTaskData;
  mainTaskData: TaskSensorData;
  ikParameters: IKParameters;
  ikResults: IKResults | null;
  isLoading: boolean;
  error: string | null;
  
  // Sensor placement state
  selectedSensorType: string | null;
  selectedView: string;
  rotationValues: { x: number; y: number; z: number };
  axisMapping: { up: string; left: string; out: string };
  sensorPlacements: { [sensorType: string]: SensorPlacement };

  // Actions
  setSensorMapping: (mapping: SensorMapping) => void;
  setCalibrationData: (data: CalibrationTaskData) => void;
  setMainTaskData: (data: TaskSensorData) => void;
  setIKParameters: (params: Partial<IKParameters>) => void;
  setIKResults: (results: IKResults) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // Sensor placement actions
  setSelectedSensorType: (type: string | null) => void;
  setSelectedView: (view: string) => void;
  setRotationValues: (values: { x: number; y: number; z: number }) => void;
  setAxisMapping: (mapping: { up: string; left: string; out: string }) => void;
  setSensorPlacement: (sensorType: string, placement: SensorPlacement) => void;
  
  reset: () => void;
}

const initialIKParameters: IKParameters = {
  subject: 1,
  task: "treadmill_walking",
  selected_setup: "mm",
  filter_type: "Xsens",
  dim: "9D",
  remove_offset: true,
};

export const useIMUStore = create<IMUStore>((set) => ({
  // Initial state
  sensorMapping: null,
  calibrationData: {},
  mainTaskData: {},
  ikParameters: initialIKParameters,
  ikResults: null,
  isLoading: false,
  error: null,
  
  // Sensor placement initial state
  selectedSensorType: null,
  selectedView: "lateral",
  rotationValues: { x: 0, y: 0, z: 0 },
  axisMapping: { up: "X", left: "Y", out: "Z" },
  sensorPlacements: {},

  // Actions
  setSensorMapping: (mapping) => set({ sensorMapping: mapping }),
  setCalibrationData: (data) => set({ calibrationData: data }),
  setMainTaskData: (data) => set({ mainTaskData: data }),
  setIKParameters: (params) =>
    set((state) => ({
      ikParameters: { ...state.ikParameters, ...params },
    })),
  setIKResults: (results) => set({ ikResults: results }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  
  // Sensor placement actions
  setSelectedSensorType: (type) => set({ selectedSensorType: type }),
  setSelectedView: (view) => set({ selectedView: view }),
  setRotationValues: (values) => set({ rotationValues: values }),
  setAxisMapping: (mapping) => set({ axisMapping: mapping }),
  setSensorPlacement: (sensorType, placement) => 
    set((state) => ({
      sensorPlacements: { ...state.sensorPlacements, [sensorType]: placement }
    })),
  
  reset: () =>
    set({
      sensorMapping: null,
      calibrationData: {},
      mainTaskData: {},
      ikParameters: initialIKParameters,
      ikResults: null,
      isLoading: false,
      error: null,
      selectedSensorType: null,
      selectedView: "lateral",
      rotationValues: { x: 0, y: 0, z: 0 },
      axisMapping: { up: "X", left: "Y", out: "Z" },
      sensorPlacements: {},
    }),
})); 