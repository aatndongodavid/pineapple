// frontend/src/features/community/OrganizationsScreen.tsx

import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  Plus,
  Users,
  CheckCircle,
  MapPin,
  ChevronRight,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';

type OrganizationType = 'CLUB' | 'ASSOCIATION' | 'MOVEMENT';

interface Organization {
  id: string;
  name: string;
  slug: string;
  description: string;
  type: OrganizationType;
  logo_url?: string;
  is_verified: boolean;
  member_count: number;
  location?: string;
}

const mockOrganizations: Organization[] = [
  {
    id: '1',
    name: 'Club Robotique ENSPD',
    slug: 'club-robotique-enspd',
    description: 'Promotion de la robotique et de l\'intelligence artificielle à travers des ateliers et compétitions.',
    type: 'CLUB',
    is_verified: true,
    member_count: 45,
    location: 'Douala',
  },
  {
    id: '2',
    name: 'BDE ENSPD',
    slug: 'bde-enspd',
    description: 'Bureau des Étudiants de l\'ENSPD, défense des intérêts étudiants.',
    type: 'ASSOCIATION',
    is_verified: true,
    member_count: 120,
    location: 'Douala',
  },
  {
    id: '3',
    name: 'Mouvement Bleu',
    slug: 'mouvement-bleu',
    description: 'Mouvement étudiant pour la transparence et le progrès.',
    type: 'MOVEMENT',
    is_verified: false,
    member_count: 85,
    location: 'Douala',
  },
  {
    id: '4',
    name: 'Alliance Innovation',
    slug: 'alliance-innovation',
    description: 'Mouvement pour l\'innovation numérique sur le campus.',
    type: 'MOVEMENT',
    is_verified: false,
    member_count: 70,
    location: 'Douala',
  },
  {
    id: '5',
    name: 'Ciné-Club',
    slug: 'cine-club',
    description: 'Projections de films et débats culturels.',
    type: 'CLUB',
    is_verified: false,
    member_count: 30,
    location: 'Douala',
  },
];

const typeLabels: Record<OrganizationType, string> = {
  CLUB: 'Club',
  ASSOCIATION: 'Association',
  MOVEMENT: 'Mouvement',
};

export const OrganizationsScreen: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<OrganizationType | 'ALL'>('ALL');
  const [followedIds, setFollowedIds] = useState<Set<string>>(new Set());
  const [showCreateModal, setShowCreateModal] = useState(false);

  const filteredOrganizations = useMemo(() => {
    return mockOrganizations.filter((org) => {
      const matchesSearch =
        org.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        org.description.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesFilter = activeFilter === 'ALL' || org.type === activeFilter;
      return matchesSearch && matchesFilter;
    });
  }, [searchQuery, activeFilter]);

  const toggleFollow = (orgId: string) => {
    setFollowedIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(orgId)) {
        newSet.delete(orgId);
      } else {
        newSet.add(orgId);
      }
      return newSet;
    });
  };

  return (
    <div className="max-w-5xl mx-auto p-4 md:p-6 pb-24 md:pb-6 space-y-6">
      {/* En-tête */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
          <Users className="h-7 w-7 text-pineapple" />
          Organisations
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Clubs, associations et mouvements de votre campus
        </p>
      </motion.div>

      {/* Barre de recherche */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="relative"
      >
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Rechercher une organisation..."
          className="w-full pl-10 pr-4 py-3 rounded-2xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
        />
      </motion.div>

      {/* Filtres */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="flex gap-2 overflow-x-auto pb-2"
      >
        {(['ALL', 'CLUB', 'ASSOCIATION', 'MOVEMENT'] as const).map((filter) => (
          <button
            key={filter}
            onClick={() => setActiveFilter(filter)}
            className={cn(
              'px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all',
              activeFilter === filter
                ? 'bg-pineapple text-white shadow-neo-pressed dark:shadow-neo-dark-pressed'
                : 'bg-background-light dark:bg-slate-800 text-gray-600 dark:text-gray-300 shadow-neo-extruded dark:shadow-neo-dark-extruded'
            )}
          >
            {filter === 'ALL' ? 'Tous' : typeLabels[filter]}
          </button>
        ))}
      </motion.div>

      {/* Grille d'organisations */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
      >
        {filteredOrganizations.map((org) => (
          <motion.div
            key={org.id}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.2 }}
          >
            <Card variant="neo-extruded" className="h-full p-5 flex flex-col">
              <div className="flex items-start gap-3">
                <div className="w-12 h-12 rounded-xl bg-pineapple/20 flex items-center justify-center shrink-0">
                  {org.logo_url ? (
                    <img src={org.logo_url} alt={org.name} className="w-full h-full object-cover rounded-xl" />
                  ) : (
                    <Users className="h-6 w-6 text-pineapple" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1 flex-wrap">
                    <h3 className="font-semibold text-gray-800 dark:text-white truncate">
                      {org.name}
                    </h3>
                    {org.is_verified && (
                      <Badge variant="success" className="ml-1">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Vérifié
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {typeLabels[org.type]}
                  </p>
                </div>
              </div>

              <p className="mt-3 text-sm text-gray-600 dark:text-gray-300 line-clamp-3 flex-1">
                {org.description}
              </p>

              <div className="mt-4 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                <span className="flex items-center gap-1">
                  <Users className="h-4 w-4" />
                  {org.member_count} membres
                </span>
                {org.location && (
                  <span className="flex items-center gap-1">
                    <MapPin className="h-4 w-4" />
                    {org.location}
                  </span>
                )}
              </div>

              <div className="mt-4">
                <Button
                  variant={followedIds.has(org.id) ? 'secondary' : 'primary'}
                  size="sm"
                  className="w-full"
                  onClick={() => toggleFollow(org.id)}
                >
                  {followedIds.has(org.id) ? 'Ne plus suivre' : 'Suivre'}
                </Button>
              </div>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      {/* Bouton flottant "Créer une organisation" */}
      <motion.button
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.3 }}
        onClick={() => setShowCreateModal(true)}
        className="fixed bottom-24 md:bottom-8 right-6 md:right-10 z-40 w-14 h-14 rounded-full bg-pineapple text-white shadow-neo-extruded dark:shadow-neo-dark-extruded flex items-center justify-center hover:shadow-neo-pressed dark:hover:shadow-neo-dark-pressed transition-shadow"
        aria-label="Créer une organisation"
      >
        <Plus className="h-7 w-7" />
      </motion.button>

      {/* Modale placeholder pour la création */}
      <AnimatePresence>
        {showCreateModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
            onClick={() => setShowCreateModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-white dark:bg-slate-900 rounded-3xl p-6 w-full max-w-md shadow-neo-extruded dark:shadow-neo-dark-extruded"
              onClick={(e) => e.stopPropagation()}
            >
              <h2 className="text-lg font-semibold mb-4">Créer une organisation</h2>
              <p className="text-sm text-gray-500">
                Formulaire de demande à venir. Les organisations sont soumises à validation administrative.
              </p>
              <Button
                variant="primary"
                className="mt-4 w-full"
                onClick={() => setShowCreateModal(false)}
              >
                Fermer
              </Button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};