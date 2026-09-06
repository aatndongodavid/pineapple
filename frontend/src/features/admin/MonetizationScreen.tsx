// frontend/src/features/admin/MonetizationScreen.tsx

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { CreditCard, Calendar, Users, Plus, TrendingUp, Building2 } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

// Types
type LicenseTier = 'BASIC' | 'STANDARD' | 'ENTERPRISE';

interface License {
  tier: LicenseTier;
  expiresAt: string;
  maxCertifiedStudents: number;
  currentCertifiedStudents: number;
}

interface Sponsorship {
  id: string;
  companyName: string;
  budget: number; // FCFA
  reach: string; // Portée (ex: "Multi-établissements")
  startDate: string;
  endDate: string;
}

const licenseData: License = {
  tier: 'STANDARD',
  expiresAt: '2027-08-31',
  maxCertifiedStudents: 5000,
  currentCertifiedStudents: 1890,
};

const mockSponsorships: Sponsorship[] = [
  {
    id: 's1',
    companyName: 'Orange Cameroun',
    budget: 2500000,
    reach: 'Multi-établissements',
    startDate: '2026-09-01',
    endDate: '2026-12-31',
  },
  {
    id: 's2',
    companyName: 'MTN Cameroun',
    budget: 1800000,
    reach: 'Local (ENSPD)',
    startDate: '2026-10-01',
    endDate: '2027-01-31',
  },
];

const tierLabels: Record<LicenseTier, string> = {
  BASIC: 'Basic',
  STANDARD: 'Standard',
  ENTERPRISE: 'Enterprise',
};

const tierVariants: Record<LicenseTier, 'default' | 'info' | 'success'> = {
  BASIC: 'default',
  STANDARD: 'info',
  ENTERPRISE: 'success',
};

export const MonetizationScreen: React.FC = () => {
  const [sponsorships, setSponsorships] = useState<Sponsorship[]>(mockSponsorships);
  const [showAddSponsor, setShowAddSponsor] = useState(false);
  const [newSponsor, setNewSponsor] = useState({
    companyName: '',
    budget: 0,
    reach: 'Local',
    startDate: '',
    endDate: '',
  });

  const usagePercentage =
    (licenseData.currentCertifiedStudents / licenseData.maxCertifiedStudents) * 100;

  const handleAddSponsor = () => {
    if (!newSponsor.companyName || !newSponsor.budget) return;
    const sponsor: Sponsorship = {
      id: `s${Date.now()}`,
      companyName: newSponsor.companyName,
      budget: newSponsor.budget,
      reach: newSponsor.reach,
      startDate: newSponsor.startDate,
      endDate: newSponsor.endDate,
    };
    setSponsorships([...sponsorships, sponsor]);
    setNewSponsor({ companyName: '', budget: 0, reach: 'Local', startDate: '', endDate: '' });
    setShowAddSponsor(false);
  };

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
          <CreditCard className="h-7 w-7 text-pineapple" />
          Monétisation & Licences
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Gérez la licence de l'établissement et les campagnes sponsorisées.
        </p>
      </motion.div>

      {/* Section Licence */}
      <Card variant="glass" className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Building2 className="h-6 w-6 text-pineapple" />
            <h2 className="text-lg font-semibold text-gray-800 dark:text-white">Campus License</h2>
          </div>
          <Badge variant={tierVariants[licenseData.tier]}>
            {tierLabels[licenseData.tier]}
          </Badge>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-background-light dark:bg-slate-800">
            <span className="text-sm text-gray-500 flex items-center gap-1">
              <Calendar className="h-4 w-4" /> Expiration
            </span>
            <p className="text-lg font-semibold text-gray-800 dark:text-white mt-1">
              {new Date(licenseData.expiresAt).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })}
            </p>
          </div>
          <div className="p-4 rounded-xl bg-background-light dark:bg-slate-800">
            <span className="text-sm text-gray-500 flex items-center gap-1">
              <Users className="h-4 w-4" /> Étudiants certifiés
            </span>
            <p className="text-lg font-semibold text-gray-800 dark:text-white mt-1">
              {licenseData.currentCertifiedStudents} / {licenseData.maxCertifiedStudents}
            </p>
          </div>
          <div className="p-4 rounded-xl bg-background-light dark:bg-slate-800">
            <span className="text-sm text-gray-500 flex items-center gap-1">
              <TrendingUp className="h-4 w-4" /> Utilisation
            </span>
            <p className="text-lg font-semibold text-gray-800 dark:text-white mt-1">
              {usagePercentage.toFixed(1)}%
            </p>
            <div className="h-1.5 bg-gray-200 dark:bg-slate-700 rounded-full mt-2">
              <div
                className="h-full bg-pineapple rounded-full"
                style={{ width: `${usagePercentage}%` }}
              />
            </div>
          </div>
        </div>
      </Card>

      {/* Section Sponsorships */}
      <Card variant="neo-extruded" className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-white">Sponsorships</h2>
          <Button variant="primary" size="sm" onClick={() => setShowAddSponsor(true)} icon={Plus}>
            Ajouter un sponsor
          </Button>
        </div>

        {sponsorships.length === 0 ? (
          <p className="text-gray-500 text-center py-6">Aucune campagne sponsorisée active.</p>
        ) : (
          <div className="space-y-3">
            {sponsorships.map((sponsor) => (
              <div
                key={sponsor.id}
                className="flex items-center justify-between p-4 rounded-xl bg-background-light dark:bg-slate-800"
              >
                <div>
                  <p className="font-medium text-gray-800 dark:text-white">{sponsor.companyName}</p>
                  <p className="text-sm text-gray-500">
                    Portée : {sponsor.reach} ·{' '}
                    {new Date(sponsor.startDate).toLocaleDateString('fr-FR')} →{' '}
                    {new Date(sponsor.endDate).toLocaleDateString('fr-FR')}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-pineapple">{sponsor.budget.toLocaleString('fr-FR')} FCFA</p>
                  <Badge variant="success">Actif</Badge>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Modale Ajouter sponsor (simple) */}
      {showAddSponsor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 w-full max-w-md shadow-neo-extruded dark:shadow-neo-dark-extruded">
            <h3 className="text-lg font-semibold mb-4">Ajouter un sponsor</h3>
            <div className="space-y-3">
              <input
                type="text"
                placeholder="Nom de l'entreprise"
                value={newSponsor.companyName}
                onChange={(e) => setNewSponsor({ ...newSponsor, companyName: e.target.value })}
                className="w-full px-4 py-2 rounded-xl bg-background-light dark:bg-slate-800 border border-white/20 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-pineapple"
              />
              <input
                type="number"
                placeholder="Budget (FCFA)"
                value={newSponsor.budget || ''}
                onChange={(e) => setNewSponsor({ ...newSponsor, budget: parseInt(e.target.value) })}
                className="w-full px-4 py-2 rounded-xl bg-background-light dark:bg-slate-800 border border-white/20 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-pineapple"
              />
              <select
                value={newSponsor.reach}
                onChange={(e) => setNewSponsor({ ...newSponsor, reach: e.target.value })}
                className="w-full px-4 py-2 rounded-xl bg-background-light dark:bg-slate-800 border border-white/20 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-pineapple"
              >
                <option value="Local">Local</option>
                <option value="Multi-établissements">Multi-établissements</option>
              </select>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="date"
                  value={newSponsor.startDate}
                  onChange={(e) => setNewSponsor({ ...newSponsor, startDate: e.target.value })}
                  className="w-full px-4 py-2 rounded-xl bg-background-light dark:bg-slate-800 border border-white/20 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-pineapple"
                />
                <input
                  type="date"
                  value={newSponsor.endDate}
                  onChange={(e) => setNewSponsor({ ...newSponsor, endDate: e.target.value })}
                  className="w-full px-4 py-2 rounded-xl bg-background-light dark:bg-slate-800 border border-white/20 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-pineapple"
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <Button variant="secondary" onClick={() => setShowAddSponsor(false)}>Annuler</Button>
              <Button variant="primary" onClick={handleAddSponsor}>Ajouter</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};