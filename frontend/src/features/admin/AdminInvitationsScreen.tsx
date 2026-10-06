// frontend/src/features/admin/AdminInvitationsScreen.tsx

import React, { useState, useEffect } from 'react';
import { Send, RefreshCw, XCircle, Search, Mail, ShieldAlert, CheckCircle2, Clock } from 'lucide-react';
import apiClient from '@/lib/api/client';
import { endpoints } from '@/lib/api/endpoints';

interface Invitation {
  id: string;
  identifier: string;
  email_sent_to: string;
  status: 'PENDING' | 'USED' | 'EXPIRED' | 'REVOKED';
  created_at: string;
  expires_at: string;
  last_sent_at?: string;
  failed_attempts: number;
}

export const AdminInvitationsScreen: React.FC = () => {
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'ALL' | 'PENDING' | 'USED' | 'EXPIRED' | 'REVOKED'>('ALL');
  const [search, setSearch] = useState('');
  const [selectedRosterId, setSelectedRosterId] = useState('');
  const [emailInput, setEmailInput] = useState('');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchInvitations = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get(endpoints.admin.invitations, {
        params: { status: filter === 'ALL' ? undefined : filter, search: search || undefined },
      });
      setInvitations(res.data.items || res.data || []);
    } catch (err: any) {
      console.error(err);
      setMessage({ type: 'error', text: 'Impossible de charger les invitations.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvitations();
  }, [filter, search]);

  const handleGenerateInvitation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRosterId || !emailInput) return;
    try {
      await apiClient.post(endpoints.admin.invitations, {
        roster_entry_id: selectedRosterId,
        email_sent_to: emailInput,
      });
      setMessage({ type: 'success', text: 'Invitation générée et envoyée avec succès.' });
      setSelectedRosterId('');
      setEmailInput('');
      fetchInvitations();
    } catch (err: any) {
      setMessage({
        type: 'error',
        text: err.response?.data?.message || 'Erreur lors de la génération.',
      });
    }
  };

  const handleBulkGenerate = async () => {
    try {
      const res = await apiClient.post(`${endpoints.admin.invitations}/bulk`);
      setMessage({
        type: 'success',
        text: `${res.data.count || 0} invitations générées et envoyées en masse.`,
      });
      fetchInvitations();
    } catch (err: any) {
      setMessage({
        type: 'error',
        text: err.response?.data?.message || 'Erreur lors du traitement en masse.',
      });
    }
  };

  const handleResend = async (id: string) => {
    try {
      await apiClient.post(endpoints.admin.resendInvitation(id));
      setMessage({ type: 'success', text: 'Invitation renvoyée.' });
      fetchInvitations();
    } catch (err: any) {
      setMessage({ type: 'error', text: 'Impossible de renvoyer l’invitation.' });
    }
  };

  const handleRevoke = async (id: string) => {
    try {
      await apiClient.post(endpoints.admin.revokeInvitation(id));
      setMessage({ type: 'success', text: 'Invitation révoquée.' });
      fetchInvitations();
    } catch (err: any) {
      setMessage({ type: 'error', text: 'Impossible de révoquer l’invitation.' });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white">
            Gestion des Invitations (Mode B)
          </h1>
          <p className="text-sm text-gray-500">
            Générez des identifiants et mots de passe temporaires uniques envoyés par e-mail.
          </p>
        </div>

        <button
          onClick={handleBulkGenerate}
          className="px-4 py-2.5 bg-pineapple hover:bg-pineapple-hover text-white text-sm font-semibold rounded-xl shadow-md transition flex items-center gap-2"
        >
          <Mail className="h-4 w-4" />
          Générer en masse pour le registre
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

      {/* Formulaire de création unitaire */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 shadow-sm">
        <h2 className="text-base font-semibold text-gray-800 dark:text-white mb-4">
          Générer une invitation unitaire
        </h2>
        <form onSubmit={handleGenerateInvitation} className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <input
            type="text"
            placeholder="ID de l'entrée du registre"
            value={selectedRosterId}
            onChange={(e) => setSelectedRosterId(e.target.value)}
            className="px-4 py-2.5 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-pineapple/50"
            required
          />
          <input
            type="email"
            placeholder="E-mail du destinataire"
            value={emailInput}
            onChange={(e) => setEmailInput(e.target.value)}
            className="px-4 py-2.5 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-pineapple/50"
            required
          />
          <button
            type="submit"
            className="px-4 py-2.5 bg-gray-900 dark:bg-slate-700 text-white text-sm font-medium rounded-xl hover:bg-black dark:hover:bg-slate-600 transition flex items-center justify-center gap-2"
          >
            <Send className="h-4 w-4" />
            Envoyer l'invitation
          </button>
        </form>
      </div>

      {/* Filtres et recherche */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto pb-2 sm:pb-0">
          {(['ALL', 'PENDING', 'USED', 'EXPIRED', 'REVOKED'] as const).map((st) => (
            <button
              key={st}
              onClick={() => setFilter(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                filter === st
                  ? 'bg-pineapple text-white'
                  : 'bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Rechercher..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-pineapple/50"
          />
        </div>
      </div>

      {/* Table des invitations */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-400 text-sm">Chargement des invitations...</div>
        ) : invitations.length === 0 ? (
          <div className="p-12 text-center text-gray-400 text-sm">Aucune invitation trouvée.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 dark:bg-slate-900/50 text-gray-500 font-semibold border-b border-gray-100 dark:border-slate-700">
                <tr>
                  <th className="p-4">Identifiant unique</th>
                  <th className="p-4">Envoyé à</th>
                  <th className="p-4">Statut</th>
                  <th className="p-4">Expiration</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-slate-700">
                {invitations.map((inv) => (
                  <tr key={inv.id} className="hover:bg-gray-50/50 dark:hover:bg-slate-700/30 transition">
                    <td className="p-4 font-mono font-semibold text-gray-800 dark:text-white">
                      {inv.identifier}
                    </td>
                    <td className="p-4 text-gray-600 dark:text-gray-300">{inv.email_sent_to}</td>
                    <td className="p-4">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${
                          inv.status === 'PENDING'
                            ? 'bg-amber-500/10 text-amber-600'
                            : inv.status === 'USED'
                            ? 'bg-emerald-500/10 text-emerald-600'
                            : inv.status === 'EXPIRED'
                            ? 'bg-gray-500/10 text-gray-600'
                            : 'bg-rose-500/10 text-rose-600'
                        }`}
                      >
                        {inv.status === 'PENDING' && <Clock className="h-3 w-3" />}
                        {inv.status === 'USED' && <CheckCircle2 className="h-3 w-3" />}
                        {inv.status}
                      </span>
                    </td>
                    <td className="p-4 text-xs text-gray-500">
                      {new Date(inv.expires_at).toLocaleDateString('fr-FR')}
                    </td>
                    <td className="p-4 text-right space-x-2">
                      {inv.status === 'PENDING' && (
                        <>
                          <button
                            onClick={() => handleResend(inv.id)}
                            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700 text-gray-600 dark:text-gray-300 transition"
                            title="Renvoyer l'e-mail"
                          >
                            <RefreshCw className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleRevoke(inv.id)}
                            className="p-1.5 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-900/20 text-rose-600 transition"
                            title="Révoquer"
                          >
                            <XCircle className="h-4 w-4" />
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
