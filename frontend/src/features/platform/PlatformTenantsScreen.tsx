// frontend/src/features/platform/PlatformTenantsScreen.tsx

import React, { useState, useEffect } from 'react';
import { Building2, Plus, Shield, CheckCircle2, ShieldAlert, Mail } from 'lucide-react';
import apiClient from '@/lib/api/client';
import { endpoints } from '@/lib/api/endpoints';

interface Tenant {
  id: string;
  name: string;
  code: string;
  country: string;
  enrollment_mode: string;
  subscription_plan: string;
  subscription_status: string;
}

export const PlatformTenantsScreen: React.FC = () => {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    country: 'CM',
    contact_email: '',
    admin_email: '',
  });
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    fetchTenants();
  }, []);

  const fetchTenants = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get(endpoints.platform.tenants);
      setTenants(res.data.items || res.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTenant = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.post(endpoints.platform.tenants, formData);
      setMessage({ type: 'success', text: 'Établissement créé et invitation transmise.' });
      setShowModal(false);
      setFormData({ name: '', code: '', country: 'CM', contact_email: '', admin_email: '' });
      fetchTenants();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.message || 'Erreur de création.' });
    }
  };

  const toggleSubscription = async (tenantId: string, currentStatus: string) => {
    const newStatus = currentStatus === 'ACTIVE' ? 'SUSPENDED' : 'ACTIVE';
    try {
      await apiClient.patch(`${endpoints.platform.tenants}/${tenantId}/subscription`, {
        status: newStatus,
      });
      setMessage({ type: 'success', text: `Abonnement mis à jour en ${newStatus}.` });
      fetchTenants();
    } catch (err) {
      setMessage({ type: 'error', text: 'Erreur de mise à jour d\'abonnement.' });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
            <Building2 className="h-6 w-6 text-pineapple" />
            Gestion de la Plateforme (Super Admin)
          </h1>
          <p className="text-sm text-gray-500">
            Créez les établissements partenaires et gérez l'état de leurs abonnements SaaS.
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2.5 bg-pineapple hover:bg-pineapple-hover text-white text-sm font-semibold rounded-xl shadow-md transition flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Créer un Établissement
        </button>
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

      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-400 text-sm">Chargement des établissements...</div>
        ) : tenants.length === 0 ? (
          <div className="p-12 text-center text-gray-400 text-sm">Aucun établissement créé.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 dark:bg-slate-900/50 text-gray-500 font-semibold border-b border-gray-100 dark:border-slate-700">
                <tr>
                  <th className="p-4">Code</th>
                  <th className="p-4">Nom de l'Établissement</th>
                  <th className="p-4">Pays</th>
                  <th className="p-4">Plan & Statut</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-slate-700">
                {tenants.map((t) => (
                  <tr key={t.id} className="hover:bg-gray-50/50 dark:hover:bg-slate-700/30 transition">
                    <td className="p-4 font-mono font-bold text-pineapple">{t.code}</td>
                    <td className="p-4 font-semibold text-gray-800 dark:text-white">{t.name}</td>
                    <td className="p-4 text-gray-500">{t.country || 'CM'}</td>
                    <td className="p-4">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${
                          t.subscription_status === 'ACTIVE'
                            ? 'bg-emerald-500/10 text-emerald-600'
                            : 'bg-rose-500/10 text-rose-600'
                        }`}
                      >
                        {t.subscription_plan || 'STANDARD'} • {t.subscription_status || 'TRIAL'}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <button
                        onClick={() => toggleSubscription(t.id, t.subscription_status)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                          t.subscription_status === 'ACTIVE'
                            ? 'bg-rose-500/10 text-rose-600 hover:bg-rose-500/20'
                            : 'bg-emerald-500/10 text-emerald-600 hover:bg-emerald-500/20'
                        }`}
                      >
                        {t.subscription_status === 'ACTIVE' ? 'Suspendre' : 'Activer'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h2 className="text-lg font-bold text-gray-800 dark:text-white">Créer un Établissement</h2>
            <form onSubmit={handleCreateTenant} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300 mb-1">
                  Nom de l'école (ex. École Nationale Supérieure Polytechnique de Douala)
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-pineapple/50"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300 mb-1">
                    Code unique (ex. ENSPD)
                  </label>
                  <input
                    type="text"
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                    className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 font-mono focus:outline-none focus:ring-2 focus:ring-pineapple/50"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300 mb-1">
                    Code pays (ISO-2)
                  </label>
                  <input
                    type="text"
                    value={formData.country}
                    onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 font-mono focus:outline-none focus:ring-2 focus:ring-pineapple/50"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300 mb-1">
                  E-mail du 1er Administrateur Établissement
                </label>
                <input
                  type="email"
                  value={formData.admin_email}
                  onChange={(e) => setFormData({ ...formData, admin_email: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-pineapple/50"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-slate-700"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-pineapple text-white text-xs font-semibold rounded-xl hover:bg-pineapple-hover"
                >
                  Créer et inviter l'admin
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
