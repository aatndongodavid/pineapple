// frontend/src/features/democracy/ElectionRoomScreen.tsx

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Home,
  Users,
  Megaphone,
  CheckCircle2,
  BarChart3,
  ScrollText,
  Clock,
  AlertTriangle,
  CheckCircle,
  Lock,
  Eye,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';

// ---------- Types ----------
type ElectionStatus = 'DRAFT' | 'CAMPAIGN' | 'VOTING_OPEN' | 'VOTING_CLOSED' | 'RESULTS_PUBLISHED' | 'ARCHIVED';

interface ElectionData {
  id: string;
  title: string;
  electionType: string;
  status: ElectionStatus;
  eligibleVoters: number;
  participants: number;
  votingStartAt: string;
  votingEndAt: string;
}

interface Candidate {
  id: string;
  name: string;
  movement: string;
  position: string;
}

// Données simulées
const mockElection: ElectionData = {
  id: 'election-1',
  title: 'Élection BDE ENSPD 2027',
  electionType: 'BDE',
  status: 'VOTING_OPEN',
  eligibleVoters: 4821,
  participants: 2917,
  votingStartAt: '2027-03-15T08:00:00',
  votingEndAt: '2027-03-15T18:00:00',
};

const mockCandidates: Candidate[] = [
  { id: 'c1', name: 'Alice Ndongo', movement: 'Mouvement Bleu', position: 'Présidente' },
  { id: 'c2', name: 'Bob Kamga', movement: 'Alliance Innovation', position: 'Président' },
  { id: 'c3', name: 'Charlie Mbarga', movement: 'Mouvement Bleu', position: 'Vice-président' },
];

// ---------- Helper pour le statut ----------
function getStatusInfo(status: ElectionStatus) {
  switch (status) {
    case 'DRAFT':
      return { label: 'Brouillon', color: 'bg-gray-400', icon: Home, pulse: false };
    case 'CAMPAIGN':
      return { label: 'Campagne', color: 'bg-blue-500', icon: Megaphone, pulse: false };
    case 'VOTING_OPEN':
      return { label: 'Vote ouvert', color: 'bg-emerald-500', icon: CheckCircle2, pulse: true };
    case 'VOTING_CLOSED':
      return { label: 'Dépouillement', color: 'bg-orange-500', icon: Clock, pulse: true };
    case 'RESULTS_PUBLISHED':
      return { label: 'Résultats publiés', color: 'bg-violet-500', icon: BarChart3, pulse: false };
    case 'ARCHIVED':
      return { label: 'Archivée', color: 'bg-gray-500', icon: ScrollText, pulse: false };
  }
}

// ---------- Composant principal ----------
export const ElectionRoomScreen: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [election, setElection] = useState<ElectionData>(mockElection);

  // Onglets disponibles
  const tabs = [
    { id: 'overview', label: 'Overview', icon: Home },
    { id: 'candidates', label: 'Candidates', icon: Users },
    { id: 'campaign', label: 'Campaign', icon: Megaphone },
    { id: 'voting', label: 'Voting', icon: CheckCircle2 },
    { id: 'results', label: 'Results', icon: BarChart3, hidden: election.status !== 'RESULTS_PUBLISHED' },
    { id: 'audit', label: 'Audit', icon: ScrollText },
  ];

  const statusInfo = getStatusInfo(election.status);

  return (
    <div className="max-w-5xl mx-auto p-4 md:p-6 pb-24 md:pb-6 space-y-6">
      {/* Bandeau de statut */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white">{election.title}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Type : {election.electionType}</p>
        </div>
        <div
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium',
            statusInfo.color,
            'text-white',
            statusInfo.pulse ? 'animate-pulse' : ''
          )}
        >
          <statusInfo.icon className="h-5 w-5" />
          {statusInfo.label}
        </div>
      </motion.div>

      {/* Onglets */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {tabs
          .filter((tab) => !tab.hidden)
          .map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all',
                activeTab === tab.id
                  ? 'bg-pineapple text-white shadow-neo-pressed dark:shadow-neo-dark-pressed'
                  : 'bg-background-light dark:bg-slate-800 text-gray-600 dark:text-gray-300 shadow-neo-extruded dark:shadow-neo-dark-extruded'
              )}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
      </div>

      {/* Contenu des onglets */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
        >
          {activeTab === 'overview' && (
            <Card variant="neo-extruded" className="p-6">
              <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">Vue d'ensemble</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="p-4 rounded-2xl bg-background-light dark:bg-slate-800">
                  <span className="text-sm text-gray-500">Électeurs éligibles</span>
                  <p className="text-2xl font-bold text-gray-800 dark:text-white">{election.eligibleVoters}</p>
                </div>
                <div className="p-4 rounded-2xl bg-background-light dark:bg-slate-800">
                  <span className="text-sm text-gray-500">Participation actuelle</span>
                  <p className="text-2xl font-bold text-gray-800 dark:text-white">
                    {election.participants} <span className="text-sm">({((election.participants / election.eligibleVoters) * 100).toFixed(1)}%)</span>
                  </p>
                </div>
                <div className="p-4 rounded-2xl bg-background-light dark:bg-slate-800">
                  <span className="text-sm text-gray-500">Statut</span>
                  <p className="font-medium text-gray-800 dark:text-white">{statusInfo.label}</p>
                </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-4 text-sm">
                <span className="flex items-center gap-1"><Clock className="h-4 w-4" /> Début : {new Date(election.votingStartAt).toLocaleString()}</span>
                <span className="flex items-center gap-1"><Clock className="h-4 w-4" /> Fin : {new Date(election.votingEndAt).toLocaleString()}</span>
              </div>
            </Card>
          )}

          {activeTab === 'candidates' && (
            <Card variant="neo-extruded" className="p-6">
              <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">Candidats</h2>
              <div className="space-y-3">
                {mockCandidates.map((candidate) => (
                  <div key={candidate.id} className="flex items-center gap-4 p-3 rounded-xl bg-background-light dark:bg-slate-800">
                    <div className="w-10 h-10 rounded-full bg-pineapple/20 flex items-center justify-center text-pineapple font-bold">
                      {candidate.name.charAt(0)}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-gray-800 dark:text-white">{candidate.name}</p>
                      <p className="text-sm text-gray-500">{candidate.movement} · {candidate.position}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {activeTab === 'campaign' && (
            <Card variant="neo-extruded" className="p-6">
              <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">Campagne</h2>
              <p className="text-gray-600 dark:text-gray-300">Programme et sondages de campagne.</p>
              <div className="mt-4 grid gap-3">
                <div className="p-4 rounded-xl bg-background-light dark:bg-slate-800">
                  <h3 className="font-medium">Mouvement Bleu</h3>
                  <p className="text-sm text-gray-500">Transparence et Progrès</p>
                </div>
                <div className="p-4 rounded-xl bg-background-light dark:bg-slate-800">
                  <h3 className="font-medium">Alliance Innovation</h3>
                  <p className="text-sm text-gray-500">Innover pour l'avenir</p>
                </div>
              </div>
            </Card>
          )}

          {activeTab === 'voting' && (
            <Card variant="neo-extruded" className="p-6">
              <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">Interface de vote</h2>
              {election.status === 'VOTING_OPEN' ? (
                <div className="space-y-4">
                  <p className="text-sm text-gray-600 dark:text-gray-300">
                    Sélectionnez votre choix puis confirmez. Le bulletin est chiffré et anonymisé.
                  </p>
                  <div className="grid gap-3">
                    {mockCandidates.map((candidate) => (
                      <button key={candidate.id} className="p-4 rounded-xl bg-background-light dark:bg-slate-800 hover:shadow-neo-pressed dark:hover:shadow-neo-dark-pressed transition-shadow text-left">
                        <p className="font-medium text-gray-800 dark:text-white">{candidate.name}</p>
                        <p className="text-sm text-gray-500">{candidate.movement} - {candidate.position}</p>
                      </button>
                    ))}
                  </div>
                  <Button variant="primary" className="w-full" icon={CheckCircle2}>
                    Confirmer mon vote
                  </Button>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Lock className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>Le vote n'est pas ouvert actuellement.</p>
                </div>
              )}
            </Card>
          )}

          {activeTab === 'results' && (
            <Card variant="neo-extruded" className="p-6">
              <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">Résultats</h2>
              <p className="text-gray-600 dark:text-gray-300">Résultats officiels publiés.</p>
              {/* Graphique ou tableau */}
            </Card>
          )}

          {activeTab === 'audit' && (
            <Card variant="neo-extruded" className="p-6">
              <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">Registre immuable</h2>
              <div className="space-y-2">
                <div className="flex items-center gap-2 p-3 rounded-xl bg-background-light dark:bg-slate-800">
                  <Eye className="h-4 w-4 text-pineapple" />
                  <span className="text-sm">Election created</span>
                </div>
                <div className="flex items-center gap-2 p-3 rounded-xl bg-background-light dark:bg-slate-800">
                  <Eye className="h-4 w-4 text-pineapple" />
                  <span className="text-sm">Campaign opened</span>
                </div>
                <div className="flex items-center gap-2 p-3 rounded-xl bg-background-light dark:bg-slate-800">
                  <Eye className="h-4 w-4 text-pineapple" />
                  <span className="text-sm">Voting opened</span>
                </div>
              </div>
            </Card>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
};