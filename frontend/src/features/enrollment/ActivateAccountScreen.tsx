// frontend/src/features/enrollment/ActivateAccountScreen.tsx

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { KeyRound, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import apiClient from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import { useAuthStore } from '@/lib/store/authStore';

export const ActivateAccountScreen: React.FC = () => {
  const navigate = useNavigate();
  const { setAuthData } = useAuthStore();

  const [identifier, setIdentifier] = useState('');
  const [tempPassword, setTempPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activated, setActivated] = useState(false);

  const handleActivate = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (newPassword && newPassword !== confirmPassword) {
      setErrorMsg('Les mots de passe ne correspondent pas.');
      return;
    }

    setLoading(true);

    try {
      const resp = await apiClient.post(API_ENDPOINTS.enrollment.activate, {
        identifier,
        temp_password: tempPassword,
        new_password: newPassword || undefined,
      });

      const data = resp.data;
      setActivated(true);

      if (data.token) {
        const meResp = await apiClient.get(API_ENDPOINTS.identity.me, {
          headers: { Authorization: `Bearer ${data.token}` },
        });
        setAuthData(data.token, meResp.data);
      }
    } catch (err: any) {
      if (err.response?.status === 429) {
        setErrorMsg('Nombre maximal de tentatives atteint. Réessayez plus tard.');
      } else {
        setErrorMsg('Code d\'invitation ou mot de passe temporaire invalide.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto p-6 space-y-6">
      <div className="text-center space-y-2">
        <div className="w-12 h-12 bg-amber-100 dark:bg-amber-900/30 text-amber-500 rounded-2xl flex items-center justify-center mx-auto">
          <KeyRound className="w-6 h-6" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Activation par invitation
        </h1>
        <p className="text-sm text-gray-500">
          Entrez les identifiants reçus par e-mail de votre établissement.
        </p>
      </div>

      {activated ? (
        <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl border border-gray-200 dark:border-gray-700 text-center space-y-4 shadow-lg">
          <CheckCircle2 className="w-16 h-16 text-emerald-500 mx-auto" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Compte activé avec succès !
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            Votre compte est à présent rattaché à votre établissement.
          </p>
          <button
            onClick={() => navigate('/feed')}
            className="w-full py-3 bg-amber-500 hover:bg-amber-600 text-white font-bold rounded-xl shadow-md transition"
          >
            Accéder à l'application
          </button>
        </div>
      ) : (
        <form onSubmit={handleActivate} className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm space-y-4">
          {errorMsg && (
            <div className="p-4 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-xl border border-red-200 dark:border-red-900/50 flex items-center gap-3 text-sm">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
              Identifiant unique d'invitation *
            </label>
            <input
              type="text"
              required
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white font-mono"
              placeholder="ex. PNL-ENSPD-XXXXXX"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
              Mot de passe temporaire *
            </label>
            <input
              type="password"
              required
              value={tempPassword}
              onChange={(e) => setTempPassword(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white"
            />
          </div>

          <div className="pt-2 border-t border-gray-200 dark:border-gray-700 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-gray-500">
              Définir votre nouveau mot de passe (Recommandé)
            </h3>

            <div>
              <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                Nouveau mot de passe
              </label>
              <input
                type="password"
                minLength={8}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white"
                placeholder="Au moins 8 caractères"
              />
            </div>

            {newPassword && (
              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Confirmer le mot de passe
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white"
                />
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-white font-bold rounded-xl transition shadow-md flex items-center justify-center gap-2"
          >
            {loading && <Loader2 className="w-5 h-5 animate-spin" />}
            Activer mon compte
          </button>
        </form>
      )}
    </div>
  );
};
