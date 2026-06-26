import { create } from "zustand";
import type {
  AppState,
  UploadResponse,
  PipelineResult,
} from "./types";

interface AppStore {
  state: AppState;
  file: File | null;
  uploadResponse: UploadResponse | null;
  result: PipelineResult | null;
  currentStep: number;
  error: string | null;
  progress: number;

  setState: (state: AppState) => void;
  setFile: (file: File | null) => void;
  setUploadResponse: (response: UploadResponse | null) => void;
  setResult: (result: PipelineResult | null) => void;
  setCurrentStep: (step: number) => void;
  setError: (error: string | null) => void;
  setProgress: (progress: number) => void;
  reset: () => void;
}

const initialState = {
  state: "idle" as AppState,
  file: null,
  uploadResponse: null,
  result: null,
  currentStep: 0,
  error: null,
  progress: 0,
};

export const useAppStore = create<AppStore>((set) => ({
  ...initialState,

  setState: (state) => set({ state }),
  setFile: (file) => set({ file }),
  setUploadResponse: (response) => set({ uploadResponse: response }),
  setResult: (result) => set({ result }),
  setCurrentStep: (step) => set({ currentStep: step }),
  setError: (error) => set({ error }),
  setProgress: (progress) => set({ progress }),
  reset: () => set(initialState),
}));
