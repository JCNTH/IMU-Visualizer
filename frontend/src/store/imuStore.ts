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

interface IMUStore {
  // State
  sensorMapping: SensorMapping | null;
  calibrationData: CalibrationTaskData;
  mainTaskData: TaskSensorData;
  ikParameters: IKParameters;
  ikResults: IKResults | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setSensorMapping: (mapping: SensorMapping) => void;
  setCalibrationData: (data: CalibrationTaskData) => void;
  setMainTaskData: (data: TaskSensorData) => void;
  setIKParameters: (params: Partial<IKParameters>) => void;
  setIKResults: (results: IKResults) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
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
  
  reset: () =>
    set({
      sensorMapping: null,
      calibrationData: {},
      mainTaskData: {},
      ikParameters: initialIKParameters,
      ikResults: null,
      isLoading: false,
      error: null,
    }),
})); 