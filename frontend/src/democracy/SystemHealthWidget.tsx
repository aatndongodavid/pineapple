// frontend/src/features/democracy/SystemHealthWidget.tsx

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card } from '@/components/ui/Card';
import { cn } from '@/lib/utils';
import { Activity, Server, Database, Vote, Users, ShieldCheck } from 'lucide-react';

// ---------- Types ----------
interface SystemHealthData {
  infrastructure: 'HEALTHY' | 'DEGRADED' | 'DOWN';
  api: 'OPERATIONAL' | 'DEGRADED';
  database: 'OPERATIONAL' | 'DEGRADED';
  voteEngine: 'READY' | 'NOT_READY';
  storage: 'OPERATIONAL' | 'DEGRADED';
  eligibleVoters: number;
  participants: number;
  participationRate: number; // en pourcentage
}

// Données simulées
const mockHealth: SystemHealthData = {
  infrastructure: 'HEALTHY',
  api: 'OPERATIONAL',
  database: 'OPERATIONAL',
  voteEngine: 'READY',
  storage: 'OPERATIONAL',
  eligibleVoters: 4821,
  participants: 2917,
  participationRate: 60.5,
};

// Composant d'indicateur avec pastille
const HealthIndicator: React.FC<{
  label: string;
  status: string;
  isHealthy: boolean;
  icon: React.ElementType;
}> = ({ label, status, isHealthy, icon: Icon }) => {
  return (
    <div className="flex items-center gap-2 p-3 rounded-xl bg-background-light dark:bg-slate-800">
      <Icon className="h-4 w-4 text-gray-500" />
      <span className="text-sm text-gray-600 dark:text-gray-300 flex-1">{label}</span>
      <span
        className={cn(
          'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
          isHealthy ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
        )}
      >
        <span
          className={cn(
            'w-2 h-2 rounded-full',
            isHealthy ? 'bg-emerald-500' : 'bg-red-500'
          )}
        />
        {status}
      </span>
    </div>
  );
};

// ---------- Composant principal ----------
export const SystemHealthWidget: React.FC = () => {
  const [health, setHealth] = useState<SystemHealthData>(mockHealth);

  // Simule une mise à jour en temps réel toutes les 5 secondes
  useEffect(() => {
    const interval = setInterval(() => {
      // Dans une vraie implémentation, on ferait un appel API pour récupérer les stats
      setHealth((prev) => ({
        ...prev,
        participants: prev.participants + Math.floor(Math.random() * 3),
        participationRate: ((prev.participants + Math.floor(Math.random() * 3)) / prev.eligibleVoters) * 100,
      }));
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Card variant="glass" className="p-4 md:p-6">
      <div className="flex items-center gap-3 mb-4">
        <Activity className="h-6 w-6 text-pineapple" />
        <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
          System Health
        </h2>
      </div>

      {/* Indicateurs techniques */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <HealthIndicator
          label="Infrastructure"
          status="Healthy"
          isHealthy={true}
          icon={Server}
        />
        <HealthIndicator
          label="API"
          status="Operational"
          isHealthy={true}
          icon={Activity}
        />
        <HealthIndicator
          label="Base de données"
          status="Operational"
          isHealthy={true}
          icon={Database}
        />
        <HealthIndicator
          label="Moteur de vote"
          status="Ready"
          isHealthy={true}
          icon={Vote}
        />
        <HealthIndicator
          label="Stockage"
          status="Operational"
          isHealthy={true}
          icon={Database}
        />
      </div>

      {/* Statistiques de participation */}
      <div className="mt-6 grid grid-cols-2 gap-4">
        <div className="p-4 rounded-2xl bg-background-light dark:bg-slate-800">
          <span className="text-sm text-gray-500 flex items-center gap-1">
            <Users className="h-4 w-4" /> Électeurs éligibles
          </span>
          <p className="text-2xl font-bold font-mono text-gray-800 dark:text-white mt-1">
            {health.eligibleVoters}
          </p>
        </div>
        <div className="p-4 rounded-2xl bg-background-light dark:bg-slate-800">
          <span className="text-sm text-gray-500 flex items-center gap-1">
            <Vote className="h-4 w-4" /> Participation
          </span>
          <p className="text-2xl font-bold font-mono text-gray-800 dark:text-white mt-1">
            {health.participants} <span className="text-sm">({health.participationRate.toFixed(1)}%)</span>
          </p>
        </div>
      </div>
    </Card>
  );
};