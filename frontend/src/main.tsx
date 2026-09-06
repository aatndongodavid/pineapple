// frontend/src/main.tsx

import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import './index.css';
import { registerSW } from 'virtual:pwa-register';

// Enregistrement du Service Worker pour la PWA
registerSW({
  immediate: true,
  onNeedRefresh() {
    // Afficher une notification ou un bouton de mise à jour (optionnel)
    console.log('Nouvelle version disponible');
  },
  onOfflineReady() {
    console.log('Application prête pour une utilisation hors ligne');
  },
});

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);