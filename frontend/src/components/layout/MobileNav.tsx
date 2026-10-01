// frontend/src/components/layout/MobileNav.tsx

import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, Users, Vote, GraduationCap, Plus, MessageCircle, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { useMessagingStore } from '@/lib/store/messagingStore';
import { useTranslation } from 'react-i18next';

const navItems = [
  { to: '/', label: 'Home', icon: Home },
  { to: '/community', label: 'Community', icon: Users },
  { to: '/democracy', label: 'Democracy', icon: Vote },
  { to: '/academy', label: 'Academy', icon: GraduationCap },
  { to: '/profile', label: 'Profil', icon: User },
];

const creationOptions = [
  { label: 'Publication', color: 'bg-primary' },
  { label: 'Projet', color: 'bg-info' },
  { label: 'Vente', color: 'bg-secondary' },
  { label: 'Trajet', color: 'bg-accent' },
];

export const MobileNav: React.FC = () => {
  const { t } = useTranslation();
  const location = useLocation();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const openChatDrawer = useMessagingStore((state) => state.openChatDrawer);
  const conversationsCount = useMessagingStore((state) => state.conversations.length);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && showCreateModal) {
        setShowCreateModal(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showCreateModal]);

  const handleCreate = (option: string) => {
    console.log('Créer :', option);
    setShowCreateModal(false);
  };

  const isMessagesDisabled = conversationsCount === 0;

  return (
    <>
      <nav
        aria-label="Navigation principale mobile"
        className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/95 dark:bg-stone-900/95 backdrop-blur-lg border-t border-stone-200 dark:border-stone-800 shadow-lg"
      >
        <div className="grid grid-cols-7 h-16">
          {navItems.slice(0, 2).map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={cn(
                'flex flex-col items-center justify-center gap-1 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-primary rounded-lg',
                location.pathname === item.to
                  ? 'text-primary font-semibold'
                  : 'text-stone-600 dark:text-stone-400 hover:text-primary'
              )}
            >
              <item.icon className="h-5 w-5" aria-hidden="true" />
              {item.label}
            </Link>
          ))}

          {/* Bouton central + */}
          <button
            type="button"
            onClick={() => setShowCreateModal(true)}
            aria-label="Créer du contenu"
            className="flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-primary rounded-full"
          >
            <span className="relative -mt-6 w-14 h-14 rounded-full bg-primary text-white shadow-md hover:bg-primary-dark transition-colors flex items-center justify-center">
              <Plus className="h-7 w-7" aria-hidden="true" />
            </span>
          </button>

          {navItems.slice(2).map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={cn(
                'flex flex-col items-center justify-center gap-1 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-primary rounded-lg',
                location.pathname === item.to
                  ? 'text-primary font-semibold'
                  : 'text-stone-600 dark:text-stone-400 hover:text-primary'
              )}
            >
              <item.icon className="h-5 w-5" aria-hidden="true" />
              {item.label}
            </Link>
          ))}

          {/* Messages */}
          <button
            type="button"
            onClick={openChatDrawer}
            disabled={isMessagesDisabled}
            aria-disabled={isMessagesDisabled}
            tabIndex={isMessagesDisabled ? -1 : 0}
            title={isMessagesDisabled ? t('common.messagesDisabledReason') : 'Ouvrir la messagerie'}
            aria-label={
              isMessagesDisabled
                ? `Messages (${t('common.messagesDisabledReason')})`
                : 'Ouvrir les messages'
            }
            className={cn(
              'flex flex-col items-center justify-center gap-1 text-xs focus:outline-none focus:ring-2 focus:ring-primary rounded-lg transition-colors',
              isMessagesDisabled
                ? 'text-stone-400 dark:text-stone-600 cursor-not-allowed opacity-60'
                : 'text-stone-600 dark:text-stone-400 hover:text-primary'
            )}
          >
            <MessageCircle className="h-5 w-5" aria-hidden="true" />
            Messages
          </button>
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
              role="dialog"
              aria-modal="true"
              aria-labelledby="create-modal-title"
              initial={{ y: 100 }}
              animate={{ y: 0 }}
              exit={{ y: 100 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="w-full max-w-md mb-20 mx-4 bg-white dark:bg-stone-900 rounded-3xl p-6 shadow-xl border border-stone-200 dark:border-stone-800"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 id="create-modal-title" className="text-lg font-semibold mb-4 text-stone-900 dark:text-white">
                Créer
              </h3>
              <div className="grid grid-cols-2 gap-3">
                {creationOptions.map((option) => (
                  <button
                    key={option.label}
                    onClick={() => handleCreate(option.label)}
                    className="flex items-center gap-3 p-4 rounded-2xl bg-background-light dark:bg-stone-800 border border-stone-200 dark:border-stone-700 hover:border-primary transition-all focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <span className={`w-3 h-3 rounded-full ${option.color}`} aria-hidden="true" />
                    <span className="text-sm font-medium text-stone-700 dark:text-stone-200">
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

