// frontend/src/features/opportunities/OpportunitiesScreen.tsx

import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Search, Plus } from 'lucide-react';
import { OpportunityCard, Opportunity } from './OpportunityCard';
import { cn } from '@/lib/utils';

// Types d'onglets
type OpportunityTab = 'PROJECT' | 'RESEARCH' | 'CHALLENGE' | 'INTERNSHIP' | 'STARTUP';

// Données mockées
const mockOpportunities: Opportunity[] = [
  {
    id: '1',
    title: 'Application mobile pour gestion de clubs',
    type: 'PROJECT',
    description: 'Développer une application mobile Flutter pour la gestion des clubs étudiants.',
    required_skills: ['Flutter', 'Firebase', 'UI/UX'],
    status: 'OPEN',
  },
  {
    id: '2',
    title: 'Étude sur les réseaux électriques intelligents',
    type: 'RESEARCH',
    description: 'Participer à une recherche sur l\'optimisation des réseaux électriques.',
    required_skills: ['Python', 'MATLAB', 'Énergie'],
    status: 'OPEN',
  },
  {
    id: '3',
    title: 'Défi innovation : Solutions EdTech',
    type: 'CHALLENGE',
    description: 'Défi lancé par une entreprise partenaire pour créer une solution éducative.',
    required_skills: ['React', 'Node.js', 'IA'],
    status: 'OPEN',
  },
  {
    id: '4',
    title: 'Stage en développement web',
    type: 'INTERNSHIP',
    description: 'Stage de 3 mois dans une startup locale.',
    required_skills: ['JavaScript', 'React', 'Git'],
    status: 'CLOSED',
  },
  {
    id: '5',
    title: 'Startup : Plateforme de covoiturage',
    type: 'STARTUP',
    description: 'Rejoindre une équipe fondatrice pour une plateforme de mobilité.',
    required_skills: ['Business', 'Développement', 'Marketing'],
    status: 'OPEN',
  },
];

const tabs: { id: OpportunityTab; label: string }[] = [
  { id: 'PROJECT', label: 'Projets' },
  { id: 'RESEARCH', label: 'Recherche' },
  { id: 'CHALLENGE', label: 'Défis Entreprises' },
  { id: 'INTERNSHIP', label: 'Stages' },
  { id: 'STARTUP', label: 'Startups' },
];

export const OpportunitiesScreen: React.FC = () => {
  const [activeTab, setActiveTab] = useState<OpportunityTab>('PROJECT');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredOpportunities = useMemo(() => {
    return mockOpportunities.filter((opp) => {
      const matchesTab = opp.type === activeTab;
      const matchesSearch =
        opp.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        opp.description.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesTab && matchesSearch;
    });
  }, [activeTab, searchQuery]);

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-6 pb-24 md:pb-6 space-y-6">
      {/* En-tête */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Opportunités</h1>
        <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-pineapple text-white shadow-neo-extruded dark:shadow-neo-dark-extruded hover:shadow-neo-pressed dark:hover:shadow-neo-dark-pressed transition-shadow">
          <Plus className="h-5 w-5" />
          <span className="text-sm font-medium">Proposer une opportunité</span>
        </button>
      </motion.div>

      {/* Recherche */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Rechercher une opportunité..."
          className="w-full pl-10 pr-4 py-3 rounded-2xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
        />
      </div>

      {/* Onglets */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all',
              activeTab === tab.id
                ? 'bg-pineapple text-white shadow-neo-pressed dark:shadow-neo-dark-pressed'
                : 'bg-background-light dark:bg-slate-800 text-gray-600 dark:text-gray-300 shadow-neo-extruded dark:shadow-neo-dark-extruded'
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Grille de cartes */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredOpportunities.map((opp) => (
          <OpportunityCard
            key={opp.id}
            opportunity={opp}
            onApply={(id) => console.log('Postuler à', id)}
          />
        ))}
      </div>

      {filteredOpportunities.length === 0 && (
        <div className="text-center py-12 text-gray-500">Aucune opportunité trouvée.</div>
      )}
    </div>
  );
};