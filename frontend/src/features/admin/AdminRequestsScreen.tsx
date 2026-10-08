// frontend/src/features/admin/AdminRequestsScreen.tsx

import React, { useState, useEffect } from 'react';
import { CheckCircle2, XCircle, ShieldAlert, Clock, UserCheck } from 'lucide-react';
import apiClient from '@/lib/api/client';
import { endpoints } from '@/lib/api/endpoints';

interface MembershipRequest {
  id: string;
  user_id: string;
  user_name: string;
  user_email: string;
  matricule?: string;
  class_group_name?: string;
  joined_via: string;
  created_at: string;
}

export const AdminRequestsScreen: React.FC = () => {
  const [requests, setRequests] = useState<MembershipRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchRequests = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get(endpoints.admin.memberships, {
        params: { status: 'PENDING' },
      });
      setRequests(res.data.items || res.data || []);
    } catch (err: any) {
      console.error(err);
      setMessage({ type: 'error', text: 'Impossible de charger les demandes en attente.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, []);

  const handleApprove = async (id: string) => {
    try {
      await apiClient.post(endpoints.admin.approveMembership(id));
      setMessage({ type: 'success', text: 'Rattachement approuvé avec succès.' });
      fetchRequests();
    } catch (err: any) {
      setMessage({ type: 'error', text: 'Erreur lors de l’approbation.' });
    }
  };

  const handleReject = async (id: string) => {
    try {
      await apiClient.post(endpoints.admin.rejectMembership(id));
      setMessage({ type: 'success', text: 'Rattachement refusé.' });
      fetchRequests();
    } catch (err: any) {
      setMessage({ type: 'error', text: 'Erreur lors du refus.' });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">
          Demandes de Rattachement en Attente
        </h1>
        <p className="text-sm text-gray-500">
          Validez les demandes d'auto-rattachement d'étudiants lorsque l'approbation automatique est désactivée.
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

      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-400 text-sm">Chargement des demandes...</div>
        ) : requests.length === 0 ? (
          <div className="p-12 text-center text-gray-400 text-sm flex flex-col items-center gap-2">
            <UserCheck className="h-8 w-8 text-gray-300" />
            <span>Aucune demande en attente d'approbation.</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 dark:bg-slate-900/50 text-gray-500 font-semibold border-b border-gray-100 dark:border-slate-700">
                <tr>
                  <th className="p-4">Utilisateur</th>
                  <th className="p-4">Matricule</th>
                  <th className="p-4">Classe</th>
                  <th className="p-4">Date de demande</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-slate-700">
                {requests.map((req) => (
                  <tr key={req.id} className="hover:bg-gray-50/50 dark:hover:bg-slate-700/30 transition">
                    <td className="p-4">
                      <p className="font-semibold text-gray-800 dark:text-white">{req.user_name || 'Utilisateur'}</p>
                      <p className="text-xs text-gray-500">{req.user_email}</p>
                    </td>
                    <td className="p-4 font-mono text-gray-700 dark:text-gray-300">{req.matricule || 'N/A'}</td>
                    <td className="p-4 text-gray-600 dark:text-gray-300">{req.class_group_name || 'Non assigné'}</td>
                    <td className="p-4 text-xs text-gray-500">
                      {new Date(req.created_at).toLocaleDateString('fr-FR')}
                    </td>
                    <td className="p-4 text-right space-x-2">
                      <button
                        onClick={() => handleApprove(req.id)}
                        className="px-3 py-1.5 bg-emerald-500 text-white text-xs font-semibold rounded-lg hover:bg-emerald-600 transition inline-flex items-center gap-1"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Approuver
                      </button>
                      <button
                        onClick={() => handleReject(req.id)}
                        className="px-3 py-1.5 bg-rose-500 text-white text-xs font-semibold rounded-lg hover:bg-rose-600 transition inline-flex items-center gap-1"
                      >
                        <XCircle className="h-3.5 w-3.5" />
                        Refuser
                      </button>
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
