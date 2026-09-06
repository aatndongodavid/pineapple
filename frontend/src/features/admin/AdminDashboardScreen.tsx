// frontend/src/features/admin/AdminDashboardScreen.tsx

import React from 'react';
import { motion } from 'framer-motion';
import {
  Users,
  UserCheck,
  Clock,
  Flag,
  ShieldCheck,
  Activity,
  TrendingUp,
  Award,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';

// Types simulés
interface Stats {
  certifiedStudents: number;
  pendingCertifications: number;
  unresolvedReports: number;
  licenseTier: 'BASIC' | 'STANDARD' | 'ENTERPRISE';
}

const mockStats: Stats = {
  certifiedStudents: 1890,
  pendingCertifications: 212,
  unresolvedReports: 7,
  licenseTier: 'STANDARD',
};

const licenseLabels: Record<Stats['licenseTier'], string> = {
  BASIC: 'Basic',
  STANDARD: 'Standard',
  ENTERPRISE: 'Enterprise',
};

export const AdminDashboardScreen: React.FC = () => {
  const participationRate = 64; // pourcentage simulé

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Dashboard</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Vue d'ensemble de l'établissement
          </p>
        </div>
        <Badge variant="info" className="text-sm">
          <ShieldCheck className="h-4 w-4 mr-1" />
          {licenseLabels[mockStats.licenseTier]} License
        </Badge>
      </motion.div>

      {/* Cartes de statistiques */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Carte 1 : Certification */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
        >
          <Card variant="neo-extruded" className="p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl bg-blue-900/10 flex items-center justify-center">
                <UserCheck className="h-6 w-6 text-blue-900 dark:text-blue-300" />
              </div>
              <div>
                <span className="text-sm text-gray-500">Certification</span>
                <p className="text-xl font-bold text-gray-800 dark:text-white">
                  {mockStats.certifiedStudents}{' '}
                  <span className="text-sm font-normal text-gray-500">certifiés</span>
                </p>
              </div>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500 flex items-center gap-1">
                <Clock className="h-4 w-4 text-amber-500" />
                {mockStats.pendingCertifications} en attente
              </span>
              <span className="text-emerald-600 font-medium">
                {((mockStats.certifiedStudents / (mockStats.certifiedStudents + mockStats.pendingCertifications)) * 100).toFixed(1)}%
              </span>
            </div>
          </Card>
        </motion.div>

        {/* Carte 2 : Signalements */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card variant="neo-extruded" className="p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
                <Flag className="h-6 w-6 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <span className="text-sm text-gray-500">Modération</span>
                <p className="text-xl font-bold text-gray-800 dark:text-white">
                  {mockStats.unresolvedReports}{' '}
                  <span className="text-sm font-normal text-gray-500">signalements ouverts</span>
                </p>
              </div>
            </div>
            <div className="mt-2">
              <div className="h-2 bg-gray-200 dark:bg-slate-700 rounded-full">
                <div
                  className="h-full bg-red-500 rounded-full"
                  style={{ width: `${Math.min(mockStats.unresolvedReports * 10, 100)}%` }}
                />
              </div>
            </div>
          </Card>
        </motion.div>

        {/* Carte 3 : Licence */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <Card variant="neo-extruded" className="p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-900/20 flex items-center justify-center">
                <Award className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div>
                <span className="text-sm text-gray-500">Licence Campus</span>
                <p className="text-xl font-bold text-gray-800 dark:text-white">
                  {licenseLabels[mockStats.licenseTier]}
                </p>
              </div>
            </div>
            <div className="text-sm text-gray-500">
              Jusqu'à 5 000 étudiants certifiés
            </div>
          </Card>
        </motion.div>
      </div>

      {/* Graphique d'activité (placeholder) */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card variant="neo-inset" className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-800 dark:text-white flex items-center gap-2">
              <Activity className="h-5 w-5 text-pineapple" />
              Activité du réseau
            </h2>
            <span className="text-sm text-gray-500 flex items-center gap-1">
              <TrendingUp className="h-4 w-4" />
              +12% cette semaine
            </span>
          </div>
          {/* Placeholder pour un futur graphique Recharts ou autre */}
          <div className="h-40 bg-background-light dark:bg-slate-800 rounded-xl flex items-end justify-around p-4">
            {/* Barres simulées */}
            {[35, 52, 41, 68, 55, 74, 63].map((height, index) => (
              <div key={index} className="flex flex-col items-center gap-1">
                <div
                  className="w-8 bg-gradient-to-t from-blue-900 to-blue-500 dark:from-blue-700 dark:to-blue-300 rounded-t"
                  style={{ height: `${height}px` }}
                />
                <span className="text-xs text-gray-500">{['L', 'M', 'M', 'J', 'V', 'S', 'D'][index]}</span>
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-3">
            Graphique indicatif — Intégration Recharts prévue
          </p>
        </Card>
      </motion.div>

      {/* Section rapide : participation */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card variant="neo-extruded" className="p-5">
          <div className="flex items-center gap-2 mb-2">
            <Users className="h-5 w-5 text-blue-900 dark:text-blue-300" />
            <h3 className="font-semibold text-gray-800 dark:text-white">Participation électorale</h3>
          </div>
          <p className="text-3xl font-bold text-gray-800 dark:text-white">{participationRate}%</p>
          <p className="text-sm text-gray-500">Taux de participation global</p>
        </Card>
        <Card variant="neo-extruded" className="p-5">
          <div className="flex items-center gap-2 mb-2">
            <ShieldCheck className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
            <h3 className="font-semibold text-gray-800 dark:text-white">Sécurité</h3>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            Tous les scrutins sont audités et conformes.
          </p>
        </Card>
      </div>
    </div>
  );
};