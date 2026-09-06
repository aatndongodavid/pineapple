// frontend/src/components/pwa/NetworkStatus.tsx

import { useState, useEffect } from 'react';

/**
 * Hook personnalisé pour suivre l'état de connexion réseau du navigateur.
 * Retourne `true` si en ligne, `false` si hors ligne.
 */
export function useNetworkStatus(): boolean {
  const [isOnline, setIsOnline] = useState<boolean>(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}

/**
 * Petit indicateur visuel (pastille) de l'état réseau.
 * Utile pour les tests ou l'affichage dans le header.
 */
export const NetworkStatusIndicator: React.FC = () => {
  const isOnline = useNetworkStatus();
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full ${
        isOnline
          ? 'bg-emerald-100 text-emerald-700'
          : 'bg-amber-100 text-amber-700'
      }`}
    >
      <span
        className={`w-2 h-2 rounded-full ${
          isOnline ? 'bg-emerald-500' : 'bg-amber-500'
        }`}
      />
      {isOnline ? 'En ligne' : 'Hors ligne'}
    </span>
  );
};