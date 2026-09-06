// frontend/src/features/academy/LibraryScreen.tsx

import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Search, Filter, BookOpen, GraduationCap, Star } from 'lucide-react';
import { CourseCard, CourseCardData } from './CourseCard';
import { cn } from '@/lib/utils';

// Types d'onglets
type LibraryTab = 'formations' | 'bibliotheque' | 'premium';

// Données mockées (à remplacer par des appels API)
const mockCourses: CourseCardData[] = [
  {
    id: '1',
    title: 'Introduction aux Algorithmes',
    type: 'COURSE',
    faculty: 'Génie Logiciel',
    filiere: 'Informatique',
    level: 'L2',
    isPremium: false,
    author: 'Pr. Kamga',
    views_count: 245,
  },
  {
    id: '2',
    title: 'TD de Thermodynamique',
    type: 'TD',
    faculty: 'Génie Mécanique',
    filiere: 'Énergétique',
    level: 'L3',
    isPremium: false,
    author: 'Dr. Ngono',
    views_count: 187,
  },
  {
    id: '3',
    title: 'Corrigé Examen Réseaux 2026',
    type: 'CORRIGE_PREMIUM',
    faculty: 'Génie Logiciel',
    filiere: 'Réseaux',
    level: 'L3',
    isPremium: true,
    price: 2500,
    author: 'Pr. Mbarga',
    views_count: 512,
  },
  {
    id: '4',
    title: 'TP de Programmation Python',
    type: 'TP',
    faculty: 'Génie Logiciel',
    filiere: 'Informatique',
    level: 'L1',
    isPremium: false,
    author: 'M. Etoa',
    views_count: 320,
  },
  {
    id: '5',
    title: 'Article de Recherche - IA',
    type: 'RESEARCH_PAPER',
    faculty: 'Génie Logiciel',
    filiere: 'Data Science',
    level: 'M1',
    isPremium: false,
    author: 'Dr. Fouda',
    views_count: 98,
  },
  {
    id: '6',
    title: 'Corrigé Maths Discrètes 2025',
    type: 'CORRIGE_PREMIUM',
    faculty: 'Génie Logiciel',
    filiere: 'Informatique',
    level: 'L2',
    isPremium: true,
    price: 3000,
    author: 'Pr. Nkoa',
    views_count: 420,
  },
];

const faculties = ['Tous', 'Génie Logiciel', 'Génie Électrique', 'Génie Mécanique', 'Sciences Économiques'];
const levels = ['Tous', 'L1', 'L2', 'L3', 'M1', 'M2'];

export const LibraryScreen: React.FC = () => {
  const [activeTab, setActiveTab] = useState<LibraryTab>('formations');
  const [searchQuery, setSearchQuery] = useState('');
  const [facultyFilter, setFacultyFilter] = useState('Tous');
  const [levelFilter, setLevelFilter] = useState('Tous');

  const filteredCourses = useMemo(() => {
    return mockCourses.filter((course) => {
      const matchesTab =
        activeTab === 'formations'
          ? true // Toutes formations confondues
          : activeTab === 'bibliotheque'
            ? !course.isPremium // Documents gratuits
            : course.isPremium; // Premium uniquement

      const matchesSearch =
        course.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        course.author?.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesFaculty = facultyFilter === 'Tous' || course.faculty === facultyFilter;
      const matchesLevel = levelFilter === 'Tous' || course.level === levelFilter;

      return matchesTab && matchesSearch && matchesFaculty && matchesLevel;
    });
  }, [activeTab, searchQuery, facultyFilter, levelFilter]);

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-6 pb-24 md:pb-6 space-y-6">
      {/* En-tête */}
      <motion.h1
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-2"
      >
        <GraduationCap className="h-7 w-7 text-pineapple" />
        Académie
      </motion.h1>

      {/* Onglets */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        <button
          onClick={() => setActiveTab('formations')}
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all',
            activeTab === 'formations'
              ? 'bg-pineapple text-white shadow-neo-pressed dark:shadow-neo-dark-pressed'
              : 'bg-background-light dark:bg-slate-800 text-gray-600 dark:text-gray-300 shadow-neo-extruded dark:shadow-neo-dark-extruded'
          )}
        >
          <BookOpen className="h-4 w-4" />
          Formations
        </button>
        <button
          onClick={() => setActiveTab('bibliotheque')}
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all',
            activeTab === 'bibliotheque'
              ? 'bg-pineapple text-white shadow-neo-pressed dark:shadow-neo-dark-pressed'
              : 'bg-background-light dark:bg-slate-800 text-gray-600 dark:text-gray-300 shadow-neo-extruded dark:shadow-neo-dark-extruded'
          )}
        >
          <BookOpen className="h-4 w-4" />
          Bibliothèque
        </button>
        <button
          onClick={() => setActiveTab('premium')}
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all',
            activeTab === 'premium'
              ? 'bg-pineapple text-white shadow-neo-pressed dark:shadow-neo-dark-pressed'
              : 'bg-background-light dark:bg-slate-800 text-gray-600 dark:text-gray-300 shadow-neo-extruded dark:shadow-neo-dark-extruded'
          )}
        >
          <Star className="h-4 w-4" />
          Premium
        </button>
      </div>

      {/* Barre de recherche */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Rechercher un document..."
          className="w-full pl-10 pr-4 py-3 rounded-2xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
        />
      </div>

      {/* Filtres */}
      <div className="flex flex-wrap gap-2">
        <select
          value={facultyFilter}
          onChange={(e) => setFacultyFilter(e.target.value)}
          className="px-3 py-2 rounded-xl bg-background-light dark:bg-slate-800 text-sm text-gray-600 dark:text-gray-300 shadow-neo-extruded dark:shadow-neo-dark-extruded focus:outline-none focus:ring-2 focus:ring-pineapple"
        >
          {faculties.map((f) => (
            <option key={f} value={f}>{f}</option>
          ))}
        </select>
        <select
          value={levelFilter}
          onChange={(e) => setLevelFilter(e.target.value)}
          className="px-3 py-2 rounded-xl bg-background-light dark:bg-slate-800 text-sm text-gray-600 dark:text-gray-300 shadow-neo-extruded dark:shadow-neo-dark-extruded focus:outline-none focus:ring-2 focus:ring-pineapple"
        >
          {levels.map((l) => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
      </div>

      {/* Grille de documents */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredCourses.map((course) => (
          <CourseCard
            key={course.id}
            data={course}
            onConsult={(id) => console.log('Consulter', id)}
            onPurchase={(id) => console.log('Acheter', id)}
          />
        ))}
      </div>

      {filteredCourses.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          Aucun document trouvé.
        </div>
      )}
    </div>
  );
};