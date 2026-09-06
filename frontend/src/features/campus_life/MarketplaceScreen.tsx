// frontend/src/features/campus_life/MarketplaceScreen.tsx

import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Search, Plus, BookOpen, Cpu, Shirt, Wrench } from 'lucide-react';
import { ListingCard, Listing } from './ListingCard';
import { Button } from '@/components/ui/Button';
import { useAuthStore } from '@/lib/store/authStore';
import { cn } from '@/lib/utils';

// Catégories disponibles
const categories = [
  { id: 'ALL', label: 'Tous', icon: null },
  { id: 'BOOKS', label: 'Livres', icon: BookOpen },
  { id: 'ELECTRONICS', label: 'Électronique', icon: Cpu },
  { id: 'CLOTHING', label: 'Vêtements', icon: Shirt },
  { id: 'SERVICES', label: 'Services', icon: Wrench },
  { id: 'HOUSING', label: 'Logement', icon: null },
  { id: 'OTHER', label: 'Autres', icon: null },
];

// Données simulées
const mockListings: Listing[] = [
  {
    id: '1',
    title: 'Manuel d\'Algorithmique',
    description: 'Manuel en très bon état, édition 2024.',
    price: 5000,
    category: 'BOOKS',
    images: [],
    seller: { id: 's1', name: 'Alice N.', isCertified: true },
    createdAt: '2026-08-20T10:00:00Z',
  },
  {
    id: '2',
    title: 'Casque Bluetooth Sony',
    description: 'Casque sans fil, utilisé 2 mois.',
    price: 15000,
    category: 'ELECTRONICS',
    images: [],
    seller: { id: 's2', name: 'Bob K.', isCertified: true },
    createdAt: '2026-08-18T14:30:00Z',
  },
  {
    id: '3',
    title: 'T-shirt ENSPD',
    description: 'T-shirt officiel de l\'école, taille M.',
    price: 3000,
    category: 'CLOTHING',
    images: [],
    seller: { id: 's3', name: 'Charlie M.', isCertified: false },
    createdAt: '2026-08-15T09:00:00Z',
  },
  {
    id: '4',
    title: 'Cours de soutien en Maths',
    description: 'Séances de soutien pour L1/L2.',
    price: 2000,
    category: 'SERVICES',
    images: [],
    seller: { id: 's4', name: 'Diane E.', isCertified: true },
    createdAt: '2026-08-12T11:15:00Z',
  },
];

export const MarketplaceScreen: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const { campusStatusDisplay } = useAuthStore();

  const isCertifiedActive = campusStatusDisplay === 'Étudiant certifié';

  const filteredListings = useMemo(() => {
    return mockListings.filter((listing) => {
      const matchesCategory = activeCategory === 'ALL' || listing.category === activeCategory;
      const matchesSearch =
        listing.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        listing.description.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesCategory && matchesSearch;
    });
  }, [activeCategory, searchQuery]);

  const handleSellClick = () => {
    if (!isCertifiedActive) {
      alert('Seuls les étudiants certifiés actifs peuvent vendre un article.');
      return;
    }
    // Ouvrir la modale de vente (à implémenter)
    console.log('Ouvrir le formulaire de vente');
  };

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-6 pb-24 md:pb-6 space-y-6">
      {/* En-tête */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Marketplace</h1>
        <Button
          variant="primary"
          onClick={handleSellClick}
          icon={Plus}
        >
          Vendre un article
        </Button>
      </motion.div>

      {/* Barre de recherche */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Rechercher un article..."
          className="w-full pl-10 pr-4 py-3 rounded-2xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
        />
      </div>

      {/* Filtres par catégories */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setActiveCategory(cat.id)}
            className={cn(
              'flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all',
              activeCategory === cat.id
                ? 'bg-pineapple text-white shadow-neo-pressed dark:shadow-neo-dark-pressed'
                : 'bg-background-light dark:bg-slate-800 text-gray-600 dark:text-gray-300 shadow-neo-extruded dark:shadow-neo-dark-extruded'
            )}
          >
            {cat.icon && <cat.icon className="h-4 w-4" />}
            {cat.label}
          </button>
        ))}
      </div>

      {/* Grille d'annonces */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredListings.map((listing) => (
          <ListingCard
            key={listing.id}
            listing={listing}
            onContact={(id) => console.log('Contacter vendeur pour listing', id)}
          />
        ))}
      </div>

      {filteredListings.length === 0 && (
        <div className="text-center py-12 text-gray-500">Aucun article trouvé.</div>
      )}
    </div>
  );
};