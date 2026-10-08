// frontend/src/features/admin/AdminSettingsScreen.tsx

import React, { useState, useEffect } from 'react';
import { Save, CheckCircle2, ShieldAlert, Settings } from 'lucide-react';
import apiClient from '@/lib/api/client';
import { endpoints } from '@/lib/api/endpoints';

export const AdminSettingsScreen: React.FC = () => {
  const [settings, setSettings] = useState({
    enrollment_mode: 'BOTH',
    auto_approve_claims: true,
    current_academic_year: '2026-2027',
    timezone: 'Africa/Douala',
    invitation_validity_days: 7,
    contact_email: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get(endpoints.admin.settings);
      setSettings(res.data);
    } catch (err) {
      console.error(err);
      setMessage({ type: 'error', text: 'Impossible de charger les paramètres.' });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await apiClient.patch(endpoints.admin.settings, settings);
      setMessage({ type: 'success', text: 'Paramètres enregistrés avec succès.' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.message || 'Erreur d’enregistrement.' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-gray-400 text-sm">Chargement des paramètres...</div>;
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
          <Settings className="h-6 w-6 text-pineapple" />
          Paramètres de l'Établissement
        </h1>
        <p className="text-sm text-gray-500">
          Configurez les modes de rattachement, l'année académique et la politique d'invitation.
        </p>
      </div>

      {message && (
        <div
          className={`p-4 rounded-xl text-sm font-medium flex items-center gap-2 ${
            message.type === 'success'
              ? 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20'
              : 'bg-rose-500/10 text-rose-600 border border-rose-500/20'
          }`}
        >
          {message.type === 'success' ? <CheckCircle2 className="h-5 w-5" /> : <ShieldAlert className="h-5 w-5" />}
          {message.text}
        </div>
      )}

      <form onSubmit={handleSave} className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 shadow-sm space-y-6 text-sm">
        {/* Mode de rattachement */}
        <div>
          <label className="block text-sm font-semibold text-gray-800 dark:text-white mb-2">
            Mode de rattachement des étudiants
          </label>
          <div className="space-y-2">
            {[
              { id: 'BOTH', label: 'Mode A & Mode B (Auto-rattachement par état civil + Invitation par code)' },
              { id: 'SELF_CLAIM', label: 'Mode A uniquement (Auto-rattachement par état civil)' },
              { id: 'INVITATION', label: 'Mode B uniquement (Invitation par identifiant + mot de passe par l\'admin)' },
            ].map((mode) => (
              <label key={mode.id} className="flex items-center gap-3 p-3 rounded-xl border border-gray-100 dark:border-slate-700 hover:bg-gray-50 dark:hover:bg-slate-700/50 cursor-pointer">
                <input
                  type="radio"
                  name="enrollment_mode"
                  value={mode.id}
                  checked={settings.enrollment_mode === mode.id}
                  onChange={(e) => setSettings({ ...settings, enrollment_mode: e.target.value })}
                  className="text-pineapple focus:ring-pineapple"
                />
                <span className="text-gray-700 dark:text-gray-300 font-medium">{mode.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Validation automatique Mode A */}
        <div className="pt-4 border-t border-gray-100 dark:border-slate-700 flex items-center justify-between">
          <div>
            <p className="font-semibold text-gray-800 dark:text-white">Approbation automatique des demandes</p>
            <p className="text-xs text-gray-500">
              Si activée, toute correspondance à 100% sur le registre active immédiatement le membership. Sinon, la demande passe en PENDING.
            </p>
          </div>
          <input
            type="checkbox"
            checked={settings.auto_approve_claims}
            onChange={(e) => setSettings({ ...settings, auto_approve_claims: e.target.checked })}
            className="h-5 w-5 text-pineapple focus:ring-pineapple rounded"
          />
        </div>

        {/* Année académique & Fuseau */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-100 dark:border-slate-700">
          <div>
            <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300 mb-1">
              Année académique courante
            </label>
            <input
              type="text"
              value={settings.current_academic_year}
              onChange={(e) => setSettings({ ...settings, current_academic_year: e.target.value })}
              className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-pineapple/50"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300 mb-1">
              Fuseau horaire
            </label>
            <input
              type="text"
              value={settings.timezone}
              onChange={(e) => setSettings({ ...settings, timezone: e.target.value })}
              className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-pineapple/50"
              required
            />
          </div>
        </div>

        {/* Durée invitation & Email contact */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-100 dark:border-slate-700">
          <div>
            <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300 mb-1">
              Durée de validité des invitations (jours)
            </label>
            <input
              type="number"
              value={settings.invitation_validity_days}
              onChange={(e) => setSettings({ ...settings, invitation_validity_days: parseInt(e.target.value) || 7 })}
              className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-pineapple/50"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300 mb-1">
              E-mail de contact scolarité
            </label>
            <input
              type="email"
              value={settings.contact_email}
              onChange={(e) => setSettings({ ...settings, contact_email: e.target.value })}
              className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-pineapple/50"
            />
          </div>
        </div>

        <div className="pt-4 flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 bg-pineapple hover:bg-pineapple-hover text-white text-sm font-semibold rounded-xl transition shadow-md flex items-center gap-2"
          >
            <Save className="h-4 w-4" />
            {saving ? 'Enregistrement...' : 'Enregistrer les modifications'}
          </button>
        </div>
      </form>
    </div>
  );
};
