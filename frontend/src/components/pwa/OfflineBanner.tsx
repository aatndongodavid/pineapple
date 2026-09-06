// frontend/src/components/pwa/OfflineBanner.tsx

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { WifiOff } from 'lucide-react';
import { useNetworkStatus } from './NetworkStatus';

/**
 * Bandeau sticky affiché en bas de l'écran lorsque l'utilisateur est hors ligne.
 * Utilise le hook useNetworkStatus pour réagir aux changements de connexion.
 */
export const OfflineBanner: React.FC = () => {
  const isOnline = useNetworkStatus();

  return (
    <AnimatePresence>
      {!isOnline && (
        <motion.div
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 100, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className="fixed bottom-0 left-0 right-0 z-50 flex justify-center p-4 pointer-events-none"
        >
          <div className="pointer-events-auto flex items-center gap-2 px-4 py-3 rounded-2xl bg-amber-100 dark:bg-amber-900/30 border border-amber-300 dark:border-amber-700 shadow-neo-extruded dark:shadow-neo-dark-extruded backdrop-blur-sm">
            <WifiOff className="h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0" />
            <span className="text-sm font-medium text-amber-800 dark:text-amber-200">
              Vous êtes hors-ligne. Certaines fonctionnalités sont restreintes.
            </span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};