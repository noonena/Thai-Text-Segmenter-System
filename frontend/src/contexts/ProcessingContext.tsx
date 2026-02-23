import React, { createContext, useContext, useState, useRef } from 'react';

interface ProcessingContextType {
  isProcessing: boolean;
  processingMessage: string;
  progress: number;
  startProcessing: (message?: string) => void;
  stopProcessing: () => void;
  updateProgress: (progress: number, message?: string) => void;
  cancelProcessing: () => void;
}

const ProcessingContext = createContext<ProcessingContextType | undefined>(undefined);

export function ProcessingProvider({ children }: { children: React.ReactNode }) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingMessage, setProcessingMessage] = useState('');
  const [progress, setProgress] = useState(0);
  const abortControllerRef = useRef<AbortController | null>(null);

  const startProcessing = (message: string = 'Processing...') => {
    abortControllerRef.current = new AbortController();
    setIsProcessing(true);
    setProcessingMessage(message);
    setProgress(0);
  };

  const stopProcessing = () => {
    setIsProcessing(false);
    setProcessingMessage('');
    setProgress(0);
    abortControllerRef.current = null;
  };

  const updateProgress = (progressValue: number, message?: string) => {
    setProgress(Math.min(100, Math.max(0, progressValue)));
    if (message) {
      setProcessingMessage(message);
    }
  };

  const cancelProcessing = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    stopProcessing();
  };

  const getAbortSignal = () => {
    return abortControllerRef.current?.signal;
  };

  return (
    <ProcessingContext.Provider value={{
      isProcessing,
      processingMessage,
      progress,
      startProcessing,
      stopProcessing,
      updateProgress,
      cancelProcessing
    }}>
      {children}
    </ProcessingContext.Provider>
  );
}

export function useProcessing() {
  const context = useContext(ProcessingContext);
  if (context === undefined) {
    throw new Error('useProcessing must be used within a ProcessingProvider');
  }
  return context;
}

