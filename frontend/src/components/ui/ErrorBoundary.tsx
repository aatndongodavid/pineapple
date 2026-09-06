// frontend/src/components/ui/ErrorBoundary.tsx

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from './Button';
import { Card } from './Card';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Journalisation de l'erreur (à remplacer par un service type Sentry)
    console.error('Erreur non interceptée :', error, errorInfo);
  }

  handleRefresh = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-background-light dark:bg-background-dark">
          <Card variant="neo-extruded" className="p-8 max-w-md w-full text-center">
            <AlertTriangle className="h-16 w-16 text-red-500 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-gray-800 dark:text-white">
              Oops, une erreur inattendue est survenue
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">
              Votre application a rencontré un problème. Veuillez rafraîchir la page.
            </p>
            {this.state.error && (
              <p className="text-xs text-gray-400 mt-2 font-mono">
                {this.state.error.message}
              </p>
            )}
            <Button
              variant="primary"
              className="mt-6 w-full"
              onClick={this.handleRefresh}
              icon={RefreshCw}
            >
              Rafraîchir l'application
            </Button>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}