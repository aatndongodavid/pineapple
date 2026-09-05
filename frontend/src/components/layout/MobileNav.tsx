// frontend/src/components/layout/MobileNav.tsx

import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, Users, Vote, GraduationCap, Plus, MessageCircle, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

const navItems = [
  { to: '/', label: 'Home', icon: Home },
  { to: '/community', label: 'Community', icon: Users },
  { to: '/democracy', label: 'Democracy', icon: Vote },
  { to: '/academy', label: 'Academy', icon: GraduationCap },
  { to: '/messages', label: 'Messages', icon: MessageCircle },
  { to: '/profile', label: 'Profil', icon: User },
];

const creationOptions = [
  { label: 'Publication', color: 'bg-pineapple' },
  { label: 'Projet', color: 'bg-blue-500' },
  { label: 'Vente', color: 'bg-orange-500' },
  { label: 'Trajet', color: 'bg-purple-500' },
];

export const MobileNav: React.FC = () => {
  const location = useLocation();
  const [showCreateModal, setShowCreateModal] = useState(false);

  const handleCreate = (option: string) => {
    // Ici, on pourrait naviguer vers les formulaires de création respectifs
    console.log('Créer :', option);
    setShowCreateModal(false);
  };

  return (
    <>
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/90 dark:bg-slate-900/90 backdrop-blur-lg border-t border-white/20 dark:border-slate-800 shadow-neo-extruded dark:shadow-neo-dark-extruded">
        <div className="grid grid-cols-6 h-16">
          {navItems.slice(0, 2).map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={cn(
                'flex flex-col items-center justify-center gap-1 text-xs',
                location.pathname === item.to
                  ? 'text-pineapple'
                  : 'text-gray-500 dark:text-gray-400'
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.label}
            </Link>
          ))}

          {/* Bouton central + */}
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center justify-center"
          >
            <span className="relative -mt-6 w-14 h-14 rounded-full bg-pineapple text-white shadow-neo-extruded dark:shadow-neo-dark-extruded flex items-center justify-center">
              <Plus className="h-7 w-7" />
            </span>
          </button>

          {navItems.slice(2).map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={cn(
                'flex flex-col items-center justify-center gap-1 text-xs',
                location.pathname === item.to
                  ? 'text-pineapple'
                  : 'text-gray-500 dark:text-gray-400'
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.label}
            </Link>
          ))}
        </div>
      </nav>

      {/* Modale de création */}
      <AnimatePresence>
        {showCreateModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 backdrop-blur-sm"
            onClick={() => setShowCreateModal(false)}
          >
            <motion.div
              initial={{ y: 100 }}
              animate={{ y: 0 }}
              exit={{ y: 100 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="w-full max-w-md mb-20 mx-4 bg-white dark:bg-slate-900 rounded-3xl p-6 shadow-neo-extruded dark:shadow-neo-dark-extruded"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">
                Créer
              </h3>
              <div className="grid grid-cols-2 gap-3">
                {creationOptions.map((option) => (
                  <button
                    key={option.label}
                    onClick={() => handleCreate(option.label)}
                    className="flex items-center gap-3 p-4 rounded-2xl bg-background-light dark:bg-slate-800 hover:shadow-neo-inset dark:hover:shadow-neo-dark-inset transition-shadow"
                  >
                    <span className={`w-3 h-3 rounded-full ${option.color}`} />
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-200">
                      {option.label}
                    </span>
                  </button>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};