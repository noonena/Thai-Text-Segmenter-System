import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ApiErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export class ApiErrorBoundary extends React.Component<
  React.PropsWithChildren<{}>,
  ApiErrorBoundaryState
> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ApiErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('API Error caught by boundary:', error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center p-8 text-center">
          <AlertTriangle className="w-12 h-12 text-red-500 mb-4" />
          <h3 className="text-lg font-semibold mb-2">Connection Error</h3>
          <p className="text-gray-600 mb-4">
            {this.state.error?.message || 'Failed to connect to the processing server'}
          </p>
          <div className="space-y-2">
            <p className="text-sm text-gray-500">
              Please ensure the backend server is running on localhost:8000
            </p>
            <button
              onClick={this.handleRetry}
              className="flex items-center gap-2 mx-auto px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              <RefreshCw className="w-4 h-4" />
              Retry
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}