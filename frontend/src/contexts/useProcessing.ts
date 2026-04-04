import { useContext } from 'react';
import { ProcessingContext, type ProcessingContextType } from './processingStore';

export function useProcessing(): ProcessingContextType {
  const context = useContext(ProcessingContext);
  if (context === undefined) {
    throw new Error('useProcessing must be used within a ProcessingProvider');
  }
  return context;
}
