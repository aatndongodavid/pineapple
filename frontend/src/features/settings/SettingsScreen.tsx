// frontend/src/features/settings/SettingsScreen.tsx

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Moon, Sun, Bell, Globe, Smartphone, Wifi, ChevronRight } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { cn } from '@/lib/utils';

interface ToggleProps {
  enabled: boolean;
  onChange: (value: boolean) => void;
  icon: React.ElementType;
  label: string;
  description?: string;
}

const Toggle: React.FC<ToggleProps> = ({ enabled, onChange, icon: Icon, label, description }) => {
  return (
    <div className="flex items-center justify-between py-4 px-1">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-background-light dark:bg-slate-800 flex items-center justify-center shadow-neo-inset dark:shadow-neo-dark-inset">
          <Icon className="h-5 w-5 text-pineapple" />
        </div>
        <div>
          <p className="font-medium text-gray-800 dark:text-white">{label}</p>
          {description && <p className="text-xs text-gray-500 dark:text-gray-400">{description}</p>}
        </div>
      </div>
      <button
        onClick={() => onChange(!enabled)}
        className={cn(
          'relative inline-flex h-7 w-12 items-center rounded-full transition-colors',
          enabled ? 'bg-pineapple' : 'bg-gray-300 dark:bg-slate-700'
        )}
        role="switch"
        aria-checked={enabled}
      >
        <span
          className={cn(
            'inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform',
            enabled ? 'translate-x-6' : 'translate-x-1'
          )}
        />
      </button>
    </div>
  );
};

export const SettingsScreen: React.FC = () => {
  const [darkMode, setDarkMode] = useState(false);
  const [pushNotifications, setPushNotifications] = useState(true);
  const [language, setLanguage] = useState<'fr' | 'en'>('fr');
  const [dataSaver, setDataSaver] = useState(false);

  // Simule le changement de langue (en production, on utiliserait un store ou i18n)
  const handleLanguageChange = (lang: 'fr' | 'en') => {
    setLanguage(lang);
    // Ici on pourrait appeler une fonction pour changer la langue de l'application
  };

  return (
    <div className="max-w-2xl mx-auto p-4 md:p-6 pb-24 md:pb-6 space-y-6">
      <motion.h1
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-2"
      >
        <SettingsIcon className="h-7 w-7 text-pineapple" />
        Paramètres
      </motion.h1>

      <Card variant="neo-extruded" className="p-5">
        <Toggle
          enabled={darkMode}
          onChange={setDarkMode}
          icon={darkMode ? Moon : Sun}
          label="Mode Sombre"
          description="Activer le thème sombre"
        />
        <div className="border-t border-gray-200 dark:border-slate-700 my-2" />
        <Toggle
          enabled={pushNotifications}
          onChange={setPushNotifications}
          icon={Bell}
          label="Notifications Push"
          description="Recevoir les alertes de vote et de certification"
        />
        <div className="border-t border-gray-200 dark:border-slate-700 my-2" />
        <div className="flex items-center justify-between py-4 px-1">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-background-light dark:bg-slate-800 flex items-center justify-center shadow-neo-inset dark:shadow-neo-dark-inset">
              <Globe className="h-5 w-5 text-pineapple" />
            </div>
            <div>
              <p className="font-medium text-gray-800 dark:text-white">Langue de l'interface</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Choisir la langue</p>
            </div>
          </div>
          <div className="flex rounded-xl bg-background-light dark:bg-slate-800 p-1 shadow-neo-inset dark:shadow-neo-dark-inset">
            <button
              onClick={() => handleLanguageChange('fr')}
              className={cn(
                'px-3 py-1 text-sm font-medium rounded-lg transition-colors',
                language === 'fr'
                  ? 'bg-pineapple text-white shadow'
                  : 'text-gray-600 dark:text-gray-300'
              )}
            >
              FR
            </button>
            <button
              onClick={() => handleLanguageChange('en')}
              className={cn(
                'px-3 py-1 text-sm font-medium rounded-lg transition-colors',
                language === 'en'
                  ? 'bg-pineapple text-white shadow'
                  : 'text-gray-600 dark:text-gray-300'
              )}
            >
              EN
            </button>
          </div>
        </div>
        <div className="border-t border-gray-200 dark:border-slate-700 my-2" />
        <Toggle
          enabled={dataSaver}
          onChange={setDataSaver}
          icon={Wifi}
          label="Économie de données"
          description="Ne pas charger les images du feed automatiquement"
        />
      </Card>

      <Card variant="neo-extruded" className="p-5">
        <button className="w-full flex items-center gap-3 py-2 hover:bg-pineapple/5 rounded-lg transition-colors">
          <Smartphone className="h-5 w-5 text-pineapple" />
          <span className="flex-1 text-left text-gray-700 dark:text-gray-200">Gérer les appareils connectés</span>
          <ChevronRight className="h-5 w-5 text-gray-400" />
        </button>
      </Card>
    </div>
  );
};

// Petit composant utilitaire pour l'icône de paramètres (évite l'import manquant)
const SettingsIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
);