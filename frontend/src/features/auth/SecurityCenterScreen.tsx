// frontend/src/features/auth/SecurityCenterScreen.tsx

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Monitor,
  Smartphone,
  Tablet,
  MapPin,
  Clock,
  ShieldCheck,
  KeyRound,
  Lock,
  LogOut,
  CheckCircle,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusPill } from '@/components/ui/StatusPill';
import { cn } from '@/lib/utils';

interface Session {
  id: string;
  device: string;
  browser: string;
  location: string;
  ip: string;
  isCurrent: boolean;
  icon: React.ElementType;
}

const sessions: Session[] = [
  {
    id: '1',
    device: 'MacBook Pro',
    browser: 'Chrome',
    location: 'Douala, Cameroun',
    ip: '154.72.168.1',
    isCurrent: true,
    icon: Monitor,
  },
  {
    id: '2',
    device: 'iPhone 13',
    browser: 'Safari',
    location: 'Yaoundé, Cameroun',
    ip: '102.244.10.5',
    isCurrent: false,
    icon: Smartphone,
  },
  {
    id: '3',
    device: 'iPad',
    browser: 'Safari',
    location: 'Douala, Cameroun',
    ip: '154.72.168.10',
    isCurrent: false,
    icon: Tablet,
  },
];

const loginHistory = [
  {
    id: '1',
    date: '2026-09-05 08:23',
    ip: '154.72.168.1',
    location: 'Douala, Cameroun',
    device: 'MacBook Pro',
  },
  {
    id: '2',
    date: '2026-09-04 22:15',
    ip: '102.244.10.5',
    location: 'Yaoundé, Cameroun',
    device: 'iPhone 13',
  },
  {
    id: '3',
    date: '2026-09-03 13:45',
    ip: '154.72.168.10',
    location: 'Douala, Cameroun',
    device: 'iPad',
  },
];

export const SecurityCenterScreen: React.FC = () => {
  const [twoFAEnabled, setTwoFAEnabled] = useState(false);
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPasswordForm({ ...passwordForm, [e.target.name]: e.target.value });
  };

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError(null);
    setPasswordMessage(null);

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setPasswordError('Les nouveaux mots de passe ne correspondent pas.');
      return;
    }
    if (passwordForm.newPassword.length < 8) {
      setPasswordError('Le nouveau mot de passe doit contenir au moins 8 caractères.');
      return;
    }

    // Simulation de changement réussi
    setPasswordMessage('Mot de passe mis à jour avec succès.');
    setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
  };

  const handleLogoutSession = (sessionId: string) => {
    // Simulation de déconnexion d'une session
    console.log('Déconnexion de la session', sessionId);
  };

  return (
    <div className="max-w-3xl mx-auto p-4 md:p-6 space-y-6 pb-24 md:pb-6">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
          <ShieldCheck className="h-7 w-7 text-pineapple" />
          Security Center
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Gérez la sécurité de votre compte Pineapple ID
        </p>
      </motion.div>

      {/* Sessions actives */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
        <Card variant="flat" className="p-5">
          <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">Sessions actives</h2>
          <div className="space-y-3">
            {sessions.map((session) => (
              <div
                key={session.id}
                className="flex items-center justify-between p-3 rounded-xl bg-background-light dark:bg-slate-800"
              >
                <div className="flex items-center gap-3">
                  <session.icon className="h-6 w-6 text-pineapple" />
                  <div>
                    <p className="font-medium text-gray-800 dark:text-white">
                      {session.device} <span className="text-xs text-gray-500">({session.browser})</span>
                      {session.isCurrent && <span className="ml-2 text-xs text-pineapple">Session actuelle</span>}
                    </p>
                    <p className="text-xs text-gray-500 flex items-center gap-1">
                      <MapPin className="h-3 w-3" /> {session.location} · {session.ip}
                    </p>
                  </div>
                </div>
                {!session.isCurrent && (
                  <Button variant="ghost" size="sm" onClick={() => handleLogoutSession(session.id)} icon={LogOut}>
                    Déconnecter
                  </Button>
                )}
              </div>
            ))}
          </div>
        </Card>
      </motion.div>

      {/* Historique des connexions */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <Card variant="flat" className="p-5">
          <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">Connexions récentes</h2>
          <div className="space-y-2">
            {loginHistory.map((log) => (
              <div key={log.id} className="flex items-center justify-between py-2 border-b border-gray-200 dark:border-slate-700 last:border-0">
                <div className="flex items-center gap-3">
                  <Clock className="h-4 w-4 text-gray-400" />
                  <span className="text-sm text-gray-700 dark:text-gray-300">{log.date}</span>
                </div>
                <div className="text-xs text-gray-500 flex items-center gap-3">
                  <span className="flex items-center gap-1"><MapPin className="h-3 w-3" /> {log.location}</span>
                  <span>{log.ip}</span>
                  <span>{log.device}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </motion.div>

      {/* Double authentification */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
        <Card variant="flat" className="p-5">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-800 dark:text-white">Double authentification (2FA)</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Sécurisez votre compte avec une vérification supplémentaire.
              </p>
            </div>
            <button
              onClick={() => setTwoFAEnabled(!twoFAEnabled)}
              className={cn(
                'relative inline-flex h-7 w-12 items-center rounded-full transition-colors',
                twoFAEnabled ? 'bg-pineapple' : 'bg-gray-300 dark:bg-slate-700'
              )}
            >
              <span
                className={cn(
                  'inline-block h-5 w-5 transform rounded-full bg-white transition-transform',
                  twoFAEnabled ? 'translate-x-6' : 'translate-x-1'
                )}
              />
            </button>
          </div>
          {twoFAEnabled && (
            <p className="mt-3 text-sm text-emerald-600 flex items-center gap-2">
              <CheckCircle className="h-4 w-4" /> Double authentification activée.
            </p>
          )}
        </Card>
      </motion.div>

      {/* Changement de mot de passe */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
        <Card variant="flat" className="p-5">
          <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white flex items-center gap-2">
            <KeyRound className="h-5 w-5 text-pineapple" />
            Changer le mot de passe
          </h2>
          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Mot de passe actuel
              </label>
              <input
                type="password"
                name="currentPassword"
                value={passwordForm.currentPassword}
                onChange={handlePasswordChange}
                required
                className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Nouveau mot de passe
              </label>
              <input
                type="password"
                name="newPassword"
                value={passwordForm.newPassword}
                onChange={handlePasswordChange}
                required
                minLength={8}
                className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Confirmer le nouveau mot de passe
              </label>
              <input
                type="password"
                name="confirmPassword"
                value={passwordForm.confirmPassword}
                onChange={handlePasswordChange}
                required
                minLength={8}
                className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
              />
            </div>
            {passwordError && (
              <div className="p-3 rounded-lg bg-red-100 text-red-700 text-sm">{passwordError}</div>
            )}
            {passwordMessage && (
              <div className="p-3 rounded-lg bg-emerald-100 text-emerald-700 text-sm">{passwordMessage}</div>
            )}
            <Button type="submit" variant="primary" icon={Lock}>
              Mettre à jour
            </Button>
          </form>
        </Card>
      </motion.div>
    </div>
  );
};