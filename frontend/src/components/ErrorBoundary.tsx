import { Component, ReactNode } from 'react';
import { logger } from '../utils/logger';
import { Button } from './ui/button';
import { Card } from './ui/card';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: any;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    // Log error to our logger
    logger.error('app', 'React Error Boundary caught error', {
      error: error.toString(),
      stack: error.stack,
      componentStack: errorInfo.componentStack,
    });

    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    logger.info('app', 'User clicked reset after error');
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
    window.location.reload();
  };

  handleDownloadLogs = () => {
    logger.info('app', 'User downloading logs after error');
    logger.downloadLogs();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
          <Card className="max-w-2xl w-full p-8">
            <div className="text-center mb-6">
              <h1 className="text-3xl font-bold text-red-600 mb-2">
                Something went wrong
              </h1>
              <p className="text-gray-600">
                The application encountered an unexpected error.
              </p>
            </div>

            {this.state.error && (
              <div className="mb-6 p-4 bg-red-50 rounded-lg">
                <p className="font-mono text-sm text-red-800 mb-2">
                  {this.state.error.toString()}
                </p>
                {this.state.error.stack && (
                  <details className="text-xs text-gray-600">
                    <summary className="cursor-pointer">Stack trace</summary>
                    <pre className="mt-2 overflow-auto">
                      {this.state.error.stack}
                    </pre>
                  </details>
                )}
              </div>
            )}

            <div className="flex gap-4 justify-center">
              <Button onClick={this.handleReset} variant="default">
                Reload Application
              </Button>
              <Button onClick={this.handleDownloadLogs} variant="outline">
                Download Logs
              </Button>
            </div>

            <p className="text-xs text-gray-500 text-center mt-6">
              Error logged to console and localStorage. Use "Download Logs" to save
              for debugging.
            </p>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

