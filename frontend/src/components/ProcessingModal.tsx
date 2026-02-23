import React from 'react';
import { X } from 'lucide-react';
import { useProcessing } from '../contexts/ProcessingContext';

export function ProcessingModal() {
  const { isProcessing, processingMessage, progress, cancelProcessing } = useProcessing();

  if (!isProcessing) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-10 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Processing</h3>
          <button
            onClick={cancelProcessing}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="space-y-4">
          <div className="text-sm text-gray-600">
            {processingMessage}
          </div>
          
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          
          <div className="flex justify-between items-center">
            <div className="text-xs text-gray-500">
              {progress}% Complete
            </div>
            <button
              onClick={cancelProcessing}
              className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}