// frontend/src/features/settings/SettingsScreen.tsx

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Moon, Sun, Bell, Globe, Smartphone, Wifi, ChevronRight, MessageSquare } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { cn } from '@/lib/utils';
import { useTranslation } from 'react-i18next';

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
        <div className="w-9 h-9 rounded-xl bg-stone-100 dark:bg-stone-800 border border-stone-200 dark:border-stone-700 flex items-center justify-center">
          <Icon className="h-5 w-5 text-primary" />
        </div>
        <div>
          <p className="font-medium text-stone-900 dark:text-white">{label}</p>
          {description && <p className="text-xs text-stone-500 dark:text-stone-400">{description}</p>}
        </div>
      </div>
      <button
        onClick={() => onChange(!enabled)}
        className={cn(
          'relative inline-flex h-7 w-12 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary',
          enabled ? 'bg-primary' : 'bg-stone-300 dark:bg-stone-700'
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
  const { t, i18n } = useTranslation();
  const [darkMode, setDarkMode] = useState(false);
  const [pushNotifications, setPushNotifications] = useState(true);
  const [smsConsent, setSmsConsent] = useState(false);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [dataSaver, setDataSaver] = useState(false);

  const currentLanguage = i18n.language.startsWith('en') ? 'en' : 'fr';

  const handleLanguageChange = (lang: 'fr' | 'en') => {
    i18n.changeLanguage(lang);
  };

  return (
    <div className="max-w-2xl mx-auto p-4 md:p-6 pb-24 md:pb-6 space-y-6">
      <motion.h1
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-2xl font-bold text-stone-900 dark:text-white flex items-center gap-2"
      >
        <SettingsIcon className="h-7 w-7 text-primary" />
        {t('settings.title')}
      </motion.h1>

      <Card className="p-5">
        <Toggle
          enabled={darkMode}
          onChange={setDarkMode}
          icon={darkMode ? Moon : Sun}
          label={t('settings.darkMode')}
          description={t('settings.darkModeDesc')}
        />
        <div className="border-t border-stone-200 dark:border-stone-800 my-2" />
        <Toggle
          enabled={pushNotifications}
          onChange={setPushNotifications}
          icon={Bell}
          label={t('settings.pushNotifications')}
          description={t('settings.pushNotificationsDesc')}
        />
        <div className="border-t border-stone-200 dark:border-stone-800 my-2" />
        <Toggle
          enabled={smsConsent}
          onChange={setSmsConsent}
          icon={MessageSquare}
          label={t('settings.smsConsent')}
          description={t('settings.smsConsentDesc')}
        />
        {smsConsent && (
          <div className="pl-12 pr-1 pt-2 pb-3">
            <label htmlFor="settings-phone-input" className="block text-xs font-medium text-stone-600 dark:text-stone-300 mb-1">
              {t('settings.phoneNumber')} (ex: +237 6XXXXXXXX)
            </label>
            <input
              id="settings-phone-input"
              type="tel"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              placeholder="+237 670 000 000"
              className="w-full px-3 py-2 rounded-xl bg-background-light dark:bg-stone-800 border border-stone-300 dark:border-stone-700 text-sm text-stone-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        )}
        <div className="border-t border-stone-200 dark:border-stone-800 my-2" />
        <div className="flex items-center justify-between py-4 px-1">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-stone-100 dark:bg-stone-800 border border-stone-200 dark:border-stone-700 flex items-center justify-center">
              <Globe className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="font-medium text-stone-900 dark:text-white">{t('settings.interfaceLanguage')}</p>
              <p className="text-xs text-stone-500 dark:text-stone-400">{t('settings.chooseLanguage')}</p>
            </div>
          </div>
          <div className="flex rounded-xl bg-stone-100 dark:bg-stone-800 p-1 border border-stone-200 dark:border-stone-700">
            <button
              onClick={() => handleLanguageChange('fr')}
              className={cn(
                'px-3 py-1 text-sm font-medium rounded-lg transition-colors',
                currentLanguage === 'fr'
                  ? 'bg-primary text-white shadow'
                  : 'text-stone-600 dark:text-stone-300'
              )}
            >
              FR
            </button>
            <button
              onClick={() => handleLanguageChange('en')}
              className={cn(
                'px-3 py-1 text-sm font-medium rounded-lg transition-colors',
                currentLanguage === 'en'
                  ? 'bg-primary text-white shadow'
                  : 'text-stone-600 dark:text-stone-300'
              )}
            >
              EN
            </button>
          </div>
        </div>
        <div className="border-t border-stone-200 dark:border-stone-800 my-2" />
        <Toggle
          enabled={dataSaver}
          onChange={setDataSaver}
          icon={Wifi}
          label={t('settings.dataSaver')}
          description={t('settings.dataSaverDesc')}
        />
      </Card>

      <Card className="p-5">
        <button className="w-full flex items-center gap-3 py-2 hover:bg-primary/5 rounded-lg transition-colors">
          <Smartphone className="h-5 w-5 text-primary" />
          <span className="flex-1 text-left text-stone-700 dark:text-stone-200">{t('settings.connectedDevices')}</span>
          <ChevronRight className="h-5 w-5 text-stone-400" />
        </button>
      </Card>
    </div>
  );
};

const SettingsIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
);