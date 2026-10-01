// frontend/src/App.tsx

import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { AppRouter } from './routes/AppRouter';
import { useInitializeApp } from './hooks/useInitializeApp';

export const App: React.FC = () => {
  // Restaure la session (JWT + profil), ouvre le WebSocket et déclenche
  // la synchronisation hors-ligne avant de monter les routes.
  const isInitialized = useInitializeApp();

  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background-light dark:bg-background-dark">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <BrowserRouter>
      <AppRouter />
    </BrowserRouter>
  );
};
