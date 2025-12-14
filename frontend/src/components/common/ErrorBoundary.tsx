import React, { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
          <div className="text-center">
            <div className="mb-4">
              <div className="medical-cross text-red-500 text-4xl mx-auto mb-4"></div>
              <h1 className="text-2xl font-bold text-red-500 mb-2">
                System Error
              </h1>
              <p className="text-gray-400 mb-4">
                EDFlow AI Dashboard encountered an unexpected error
              </p>
            </div>
            <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 mb-4 text-left">
              <p className="text-sm text-gray-300 font-mono">
                {this.state.error?.message || "Unknown error occurred"}
              </p>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              Reload Dashboard
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
