import { createContext } from 'react';

export interface ProcessingContextType {
  isProcessing: boolean;
  processingMessage: string;
  progress: number;
  startProcessing: (message?: string) => void;
  stopProcessing: () => void;
  updateProgress: (progress: number, message?: string) => void;
  cancelProcessing: () => void;
}

export const ProcessingContext = createContext<ProcessingContextType | undefined>(undefined);
