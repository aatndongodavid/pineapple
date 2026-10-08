// frontend/src/features/admin/AdminAuditScreen.tsx

import React, { useState, useEffect } from 'react';
import { Shield, Search, FileText } from 'lucide-react';
import apiClient from '@/lib/api/client';
import { endpoints } from '@/lib/api/endpoints';

interface AuditLog {
  id: string;
  action: string;
  actor_id: string;
  actor_email?: string;
  details?: string;
  ip_address?: string;
  created_at: string;
}

export const AdminAuditScreen: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchLogs();
  }, [search]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get(endpoints.admin.audit, {
        params: { search: search || undefined },
      });
      setLogs(res.data.items || res.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
            <Shield className="h-6 w-6 text-pineapple" />
            Journal d'Audit de Sécurité
          </h1>
          <p className="text-sm text-gray-500">
            Historique complet des actions administratives et sensibles effectuées au sein de l'établissement.
          </p>
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Filtrer par action..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-pineapple/50"
          />
        </div>
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-400 text-sm">Chargement du journal d'audit...</div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-gray-400 text-sm">Aucun évènement consigné.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 dark:bg-slate-900/50 text-gray-500 font-semibold border-b border-gray-100 dark:border-slate-700">
                <tr>
                  <th className="p-4">Date & Heure</th>
                  <th className="p-4">Action</th>
                  <th className="p-4">Acteur</th>
                  <th className="p-4">Détails</th>
                  <th className="p-4">Adresse IP</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-slate-700 font-mono text-xs">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50/50 dark:hover:bg-slate-700/30 transition">
                    <td className="p-4 text-gray-500">
                      {new Date(log.created_at).toLocaleString('fr-FR')}
                    </td>
                    <td className="p-4 font-bold text-pineapple">{log.action}</td>
                    <td className="p-4 text-gray-700 dark:text-gray-300">{log.actor_email || log.actor_id}</td>
                    <td className="p-4 text-gray-600 dark:text-gray-400 max-w-xs truncate">
                      {log.details || '-'}
                    </td>
                    <td className="p-4 text-gray-400">{log.ip_address || '127.0.0.1'}</td>
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
