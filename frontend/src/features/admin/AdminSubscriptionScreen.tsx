// frontend/src/features/admin/AdminSubscriptionScreen.tsx

import React, { useState, useEffect } from 'react';
import { CreditCard, CheckCircle2, ShieldAlert, Users, Calendar } from 'lucide-react';
import apiClient from '@/lib/api/client';
import { endpoints } from '@/lib/api/endpoints';

interface SubscriptionInfo {
  plan: string;
  status: string;
  seats_limit: number;
  seats_used: number;
  starts_at: string;
  ends_at: string;
  grace_days: number;
}

export const AdminSubscriptionScreen: React.FC = () => {
  const [sub, setSub] = useState<SubscriptionInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSubscription();
  }, []);

  const fetchSubscription = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get(endpoints.admin.subscription);
      setSub(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-gray-400 text-sm">Chargement de l'abonnement...</div>;
  }

  const isExpired = sub?.status === 'EXPIRED' || sub?.status === 'SUSPENDED';

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
          <CreditCard className="h-6 w-6 text-pineapple" />
          Abonnement de l'Établissement
        </h1>
        <p className="text-sm text-gray-500">
          Consultez l'état de la licence, la limite de sièges et la date d'échéance.
        </p>
      </div>

      {isExpired && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-600 flex items-center gap-3">
          <ShieldAlert className="h-6 w-6 flex-shrink-0" />
          <div>
            <p className="font-bold text-sm">Abonnement suspendu ou expiré</p>
            <p className="text-xs">
              Les membres de l'établissement sont actuellement en mode lecture seule. Contactez l'administrateur Pineapple pour régulariser.
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 shadow-sm space-y-2">
          <p className="text-xs text-gray-500 font-semibold uppercase">Formule Actuelle</p>
          <p className="text-2xl font-black text-gray-800 dark:text-white">{sub?.plan || 'STANDARD'}</p>
          <span
            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold uppercase ${
              sub?.status === 'ACTIVE'
                ? 'bg-emerald-500/10 text-emerald-600'
                : 'bg-amber-500/10 text-amber-600'
            }`}
          >
            <CheckCircle2 className="h-3 w-3" />
            {sub?.status || 'TRIAL'}
          </span>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 shadow-sm space-y-2">
          <p className="text-xs text-gray-500 font-semibold uppercase">Utilisation des Sièges</p>
          <div className="flex items-baseline gap-2">
            <p className="text-2xl font-black text-gray-800 dark:text-white">{sub?.seats_used || 0}</p>
            <p className="text-sm text-gray-400">/ {sub?.seats_limit || 500} autorisés</p>
          </div>
          <div className="w-full bg-gray-100 dark:bg-slate-700 rounded-full h-2 overflow-hidden">
            <div
              className="bg-pineapple h-2 rounded-full transition-all"
              style={{
                width: `${Math.min(100, ((sub?.seats_used || 0) / (sub?.seats_limit || 500)) * 100)}%`,
              }}
            />
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 shadow-sm space-y-2">
          <p className="text-xs text-gray-500 font-semibold uppercase">Date d'échéance</p>
          <p className="text-xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
            <Calendar className="h-5 w-5 text-pineapple" />
            {sub?.ends_at ? new Date(sub.ends_at).toLocaleDateString('fr-FR') : '31/12/2027'}
          </p>
          <p className="text-xs text-gray-400">Période de grâce : {sub?.grace_days || 7} jours</p>
        </div>
      </div>
    </div>
  );
};
