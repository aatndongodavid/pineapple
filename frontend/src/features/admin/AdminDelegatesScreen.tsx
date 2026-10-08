// frontend/src/features/admin/AdminDelegatesScreen.tsx

import React, { useState, useEffect } from 'react';
import { UserCheck, Shield, UserX, CheckCircle2, ShieldAlert } from 'lucide-react';
import apiClient from '@/lib/api/client';
import { endpoints } from '@/lib/api/endpoints';

interface Delegate {
  id: string;
  class_group_id: string;
  class_group_name: string;
  user_id: string;
  user_name: string;
  user_email: string;
  kind: 'TITULAIRE' | 'SUPPLEANT';
  appointed_at: string;
}

interface ClassGroup {
  id: string;
  name: string;
  code: string;
}

interface Member {
  id: string;
  user_id: string;
  user_name: string;
  user_email: string;
  matricule?: string;
}

export const AdminDelegatesScreen: React.FC = () => {
  const [classes, setClasses] = useState<ClassGroup[]>([]);
  const [selectedClassId, setSelectedClassId] = useState('');
  const [delegates, setDelegates] = useState<Delegate[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [delegateKind, setDelegateKind] = useState<'TITULAIRE' | 'SUPPLEANT'>('TITULAIRE');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    fetchClasses();
  }, []);

  const fetchClasses = async () => {
    try {
      const res = await apiClient.get(endpoints.admin.classes);
      const items = res.data.items || res.data || [];
      setClasses(items);
      if (items.length > 0) {
        setSelectedClassId(items[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (selectedClassId) {
      fetchClassDetails(selectedClassId);
    }
  }, [selectedClassId]);

  const fetchClassDetails = async (classId: string) => {
    setLoading(true);
    try {
      const [delRes, memRes] = await Promise.all([
        apiClient.get(endpoints.admin.classDelegates(classId)),
        apiClient.get(endpoints.admin.memberships, { params: { class_group_id: classId, status: 'ACTIVE' } }),
      ]);
      setDelegates(delRes.data.items || delRes.data || []);
      setMembers(memRes.data.items || memRes.data || []);
    } catch (err: any) {
      console.error(err);
      setMessage({ type: 'error', text: 'Impossible de charger les données de la classe.' });
    } finally {
      setLoading(false);
    }
  };

  const handleAppoint = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClassId || !selectedUserId) return;
    try {
      await apiClient.put(endpoints.admin.classDelegates(selectedClassId), {
        user_id: selectedUserId,
        kind: delegateKind,
      });
      setMessage({ type: 'success', text: `Délégué ${delegateKind.toLowerCase()} désigné avec succès.` });
      setSelectedUserId('');
      fetchClassDetails(selectedClassId);
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.message || 'Erreur lors de la désignation.' });
    }
  };

  const handleRevoke = async (classId: string, delegateId: string) => {
    if (!confirm('Voulez-vous vraiment révoquer ce délégué ?')) return;
    try {
      await apiClient.delete(`${endpoints.admin.classDelegates(classId)}/${delegateId}`);
      setMessage({ type: 'success', text: 'Délégué révoqué.' });
      fetchClassDetails(classId);
    } catch (err: any) {
      setMessage({ type: 'error', text: 'Erreur lors de la révocation.' });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Désignation des Délégués</h1>
        <p className="text-sm text-gray-500">
          Nommez un délégué titulaire et un suppléant par classe. Leurs permissions sont strictement limitées à leur classe.
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

      {/* Sélection de classe */}
      <div className="flex items-center gap-4 bg-white dark:bg-slate-800 p-4 rounded-2xl border border-gray-100 dark:border-slate-700 shadow-sm">
        <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">
          Sélectionner la classe :
        </label>
        <select
          value={selectedClassId}
          onChange={(e) => setSelectedClassId(e.target.value)}
          className="px-4 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-pineapple/50"
        >
          {classes.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name} ({c.code})
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Formulaire de nomination */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 shadow-sm space-y-4">
          <h2 className="text-base font-semibold text-gray-800 dark:text-white flex items-center gap-2">
            <UserCheck className="h-5 w-5 text-pineapple" />
            Désigner / Remplacer un Délégué
          </h2>

          <form onSubmit={handleAppoint} className="space-y-4 text-sm">
            <div>
              <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300 mb-1">
                Étudiant membre de la classe
              </label>
              <select
                value={selectedUserId}
                onChange={(e) => setSelectedUserId(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-pineapple/50"
                required
              >
                <option value="">-- Choisir un étudiant --</option>
                {members.map((m) => (
                  <option key={m.user_id} value={m.user_id}>
                    {m.user_name} ({m.user_email}) {m.matricule ? `- ${m.matricule}` : ''}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300 mb-1">
                Rôle de délégué
              </label>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="kind"
                    checked={delegateKind === 'TITULAIRE'}
                    onChange={() => setDelegateKind('TITULAIRE')}
                    className="text-pineapple focus:ring-pineapple"
                  />
                  <span>Titulaire</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="kind"
                    checked={delegateKind === 'SUPPLEANT'}
                    onChange={() => setDelegateKind('SUPPLEANT')}
                    className="text-pineapple focus:ring-pineapple"
                  />
                  <span>Suppléant</span>
                </label>
              </div>
            </div>

            <button
              type="submit"
              className="w-full px-4 py-2.5 bg-pineapple hover:bg-pineapple-hover text-white text-sm font-semibold rounded-xl transition shadow-md flex items-center justify-center gap-2"
            >
              <Shield className="h-4 w-4" />
              Confirmer la désignation
            </button>
          </form>
        </div>

        {/* Délégués actuels */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 shadow-sm space-y-4">
          <h2 className="text-base font-semibold text-gray-800 dark:text-white">
            Délégués Actifs de la Classe
          </h2>

          {loading ? (
            <div className="p-8 text-center text-gray-400 text-sm">Chargement...</div>
          ) : delegates.length === 0 ? (
            <div className="p-8 text-center text-gray-400 text-sm">Aucun délégué désigné pour cette classe.</div>
          ) : (
            <div className="space-y-3">
              {delegates.map((d) => (
                <div
                  key={d.id}
                  className="p-4 rounded-xl border border-gray-100 dark:border-slate-700 bg-gray-50/50 dark:bg-slate-900/50 flex items-center justify-between"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          d.kind === 'TITULAIRE'
                            ? 'bg-pineapple/10 text-pineapple'
                            : 'bg-blue-500/10 text-blue-600'
                        }`}
                      >
                        {d.kind}
                      </span>
                      <p className="font-semibold text-gray-800 dark:text-white text-sm">{d.user_name}</p>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{d.user_email}</p>
                  </div>

                  <button
                    onClick={() => handleRevoke(selectedClassId, d.id)}
                    className="p-2 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-900/20 text-rose-600 transition"
                    title="Révoquer le délégué"
                  >
                    <UserX className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
