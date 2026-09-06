// frontend/src/features/notifications/NotificationCenter.tsx

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, CheckCheck, X, ShieldAlert, Vote, MessageCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

// Types
type NotificationType = 'admin' | 'democracy' | 'community';

interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  description: string;
  timestamp: string;
  isRead: boolean;
}

const mockNotifications: Notification[] = [
  {
    id: 'n1',
    type: 'admin',
    title: 'Votre statut a été validé !',
    description: 'Votre certification pour l\'année 2026-2027 a été approuvée.',
    timestamp: '2026-09-05T08:30:00Z',
    isRead: false,
  },
  {
    id: 'n2',
    type: 'democracy',
    title: 'Élection BDE 2027 ouverte',
    description: 'Le vote pour le BDE est ouvert. Participez avant 18h.',
    timestamp: '2026-09-06T09:00:00Z',
    isRead: false,
  },
  {
    id: 'n3',
    type: 'community',
    title: 'Nouveau message',
    description: 'Bob K. vous a envoyé un message concernant votre annonce.',
    timestamp: '2026-09-06T10:15:00Z',
    isRead: true,
  },
  {
    id: 'n4',
    type: 'community',
    title: 'Nouvelle réaction',
    description: 'Alice N. a aimé votre publication.',
    timestamp: '2026-09-06T11:05:00Z',
    isRead: false,
  },
];

const typeConfig: Record<NotificationType, { icon: React.ElementType; color: string }> = {
  admin: { icon: ShieldAlert, color: 'text-blue-500' },
  democracy: { icon: Vote, color: 'text-pineapple' },
  community: { icon: MessageCircle, color: 'text-purple-500' },
};

export const NotificationCenter: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>(mockNotifications);
  const [isOpen, setIsOpen] = useState(false);
  const [isMobile, setIsMobile] = useState<boolean>(window.innerWidth < 768);
  const panelRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const unreadCount = notifications.filter((n) => !n.isRead).length;

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Fermer si clic extérieur (pour desktop)
  useEffect(() => {
    if (!isOpen) return;
    const handleClickOutside = (event: MouseEvent) => {
      if (
        panelRef.current &&
        !panelRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, isRead: true })));
  };

  const markAsRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, isRead: true } : n))
    );
  };

  const formatTime = (iso: string) => {
    const date = new Date(iso);
    return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="relative">
      {/* Bouton cloche */}
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-full hover:bg-pineapple/10 transition-colors"
        aria-label="Notifications"
      >
        <Bell className="h-5 w-5 text-gray-600 dark:text-gray-300" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-xs w-5 h-5 flex items-center justify-center rounded-full">
            {unreadCount}
          </span>
        )}
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            ref={panelRef}
            initial={isMobile ? { y: '100%', opacity: 0.5 } : { opacity: 0, y: -10 }}
            animate={isMobile ? { y: 0, opacity: 1 } : { opacity: 1, y: 0 }}
            exit={isMobile ? { y: '100%', opacity: 0 } : { opacity: 0, y: -10 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className={cn(
              'bg-white dark:bg-slate-900 rounded-t-3xl md:rounded-2xl shadow-neo-extruded dark:shadow-neo-dark-extruded overflow-hidden',
              isMobile
                ? 'fixed bottom-0 left-0 right-0 z-50 max-h-[80vh]'
                : 'absolute right-0 top-full mt-2 w-80 z-50'
            )}
          >
            {/* En-tête */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-slate-800">
              <h3 className="font-semibold text-gray-800 dark:text-white">Notifications</h3>
              <div className="flex items-center gap-2">
                <button
                  onClick={markAllAsRead}
                  className="text-xs text-pineapple hover:underline flex items-center gap-1"
                >
                  <CheckCheck className="h-4 w-4" />
                  Tout marquer comme lu
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 rounded-full hover:bg-pineapple/10 md:hidden"
                >
                  <X className="h-5 w-5 text-gray-500" />
                </button>
              </div>
            </div>

            {/* Liste des notifications */}
            <div className="overflow-y-auto max-h-[60vh]">
              {notifications.length === 0 ? (
                <p className="text-center text-gray-500 py-8">Aucune notification</p>
              ) : (
                notifications.map((notification) => {
                  const { icon: Icon, color } = typeConfig[notification.type];
                  return (
                    <button
                      key={notification.id}
                      onClick={() => markAsRead(notification.id)}
                      className={cn(
                        'w-full text-left px-4 py-3 border-b border-gray-200 dark:border-slate-800 transition-colors',
                        notification.isRead
                          ? 'bg-white dark:bg-slate-900'
                          : 'bg-pineapple/5 dark:bg-pineapple/10'
                      )}
                    >
                      <div className="flex gap-3">
                        <Icon className={cn('h-5 w-5 mt-0.5 shrink-0', color)} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-medium text-gray-800 dark:text-white text-sm truncate">
                              {notification.title}
                            </span>
                            <span className="text-xs text-gray-400 shrink-0">
                              {formatTime(notification.timestamp)}
                            </span>
                          </div>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2">
                            {notification.description}
                          </p>
                        </div>
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};