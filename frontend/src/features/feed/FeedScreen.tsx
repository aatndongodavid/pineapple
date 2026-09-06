// frontend/src/features/feed/FeedScreen.tsx

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RefreshCw, ChevronDown, Sparkles, Building, Users, Briefcase } from 'lucide-react';
import { cn } from '@/lib/utils';

// Types pour les posts (à adapter selon le backend)
interface Post {
  id: string;
  author: {
    id: string;
    name: string;
    avatar?: string;
    campusStatus?: string;
  };
  content: string;
  type: 'TEXT' | 'IMAGE' | 'VIDEO' | 'EVENT' | 'PROJECT';
  mediaUrls?: string[];
  organization?: string;
  isSponsored?: boolean;
  viewsCount: number;
  createdAt: string;
}

// Sous‑composants (peuvent être déplacés dans des fichiers séparés)
const CreatePostTrigger: React.FC<{ onClick: () => void }> = ({ onClick }) => (
  <button
    onClick={onClick}
    className="w-full flex items-center gap-3 px-5 py-4 rounded-2xl bg-background-light dark:bg-slate-800 shadow-neo-inset dark:shadow-neo-dark-inset text-gray-500 dark:text-gray-400 text-sm hover:shadow-neo-pressed dark:hover:shadow-neo-dark-pressed transition-all"
  >
    <span className="flex-1 text-left">Quoi de neuf sur le campus ?</span>
    <RefreshCw className="h-5 w-5 opacity-50" />
  </button>
);

const SkeletonPostCard: React.FC = () => (
  <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 shadow-neo-extruded dark:shadow-neo-dark-extruded animate-pulse">
    <div className="flex items-center gap-3 mb-4">
      <div className="w-10 h-10 rounded-full bg-gray-300 dark:bg-slate-700" />
      <div className="flex-1">
        <div className="h-4 bg-gray-300 dark:bg-slate-700 rounded w-1/3" />
        <div className="h-3 bg-gray-200 dark:bg-slate-600 rounded w-1/4 mt-1" />
      </div>
    </div>
    <div className="h-4 bg-gray-300 dark:bg-slate-700 rounded mb-2" />
    <div className="h-4 bg-gray-300 dark:bg-slate-700 rounded w-5/6" />
    <div className="h-32 bg-gray-200 dark:bg-slate-700 rounded mt-4" />
  </div>
);

const PostCard: React.FC<{ post: Post }> = ({ post }) => (
  <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 shadow-neo-extruded dark:shadow-neo-dark-extruded transition-shadow hover:shadow-neo-pressed dark:hover:shadow-neo-dark-pressed">
    <div className="flex items-center gap-3 mb-3">
      <div className="w-10 h-10 rounded-full bg-pineapple/20 flex items-center justify-center text-pineapple font-bold">
        {post.author.name.charAt(0)}
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-gray-800 dark:text-white">{post.author.name}</span>
          {post.author.campusStatus && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">
              {post.author.campusStatus}
            </span>
          )}
        </div>
        <div className="text-xs text-gray-500">{new Date(post.createdAt).toLocaleDateString()}</div>
      </div>
      {post.isSponsored && (
        <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700">Sponsorisé</span>
      )}
    </div>
    <p className="text-gray-700 dark:text-gray-300">{post.content}</p>
    {post.mediaUrls && post.mediaUrls.length > 0 && (
      <div className="mt-3 rounded-xl overflow-hidden">
        <img src={post.mediaUrls[0]} alt="Contenu" className="w-full h-48 object-cover" />
      </div>
    )}
    <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
      <span>{post.viewsCount} vues</span>
      <span className="font-medium text-pineapple">Voir plus</span>
    </div>
  </div>
);

// Hook de pull‑to‑refresh (mobile)
function usePullToRefresh(ref: React.RefObject<HTMLDivElement>, onRefresh: () => Promise<void>) {
  const [pullDistance, setPullDistance] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const startY = useRef<number | null>(null);

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (window.scrollY === 0) {
      startY.current = e.touches[0].clientY;
    }
  }, []);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (startY.current === null) return;
    const currentY = e.touches[0].clientY;
    const diff = currentY - startY.current;
    if (diff > 0 && window.scrollY === 0) {
      setPullDistance(Math.min(diff, 80));
    }
  }, []);

  const handleTouchEnd = useCallback(async () => {
    if (pullDistance > 50) {
      setIsRefreshing(true);
      await onRefresh();
      setIsRefreshing(false);
    }
    setPullDistance(0);
    startY.current = null;
  }, [pullDistance, onRefresh]);

  return { pullDistance, isRefreshing, handleTouchStart, handleTouchMove, handleTouchEnd };
}

export const FeedScreen: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'pour_toi' | 'mon_etablissement' | 'mes_communautes' | 'opportunites'>('pour_toi');
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Simulation de chargement
  const fetchPosts = useCallback(async () => {
    setLoading(true);
    // Appel API factice – à remplacer par le vrai endpoint
    await new Promise((resolve) => setTimeout(resolve, 800));
    const mockPosts: Post[] = [
      {
        id: '1',
        author: { id: 'u1', name: 'Alice Ndongo', campusStatus: 'Étudiant certifié' },
        content: 'Le club de robotique organise un atelier ce vendredi à 14h en salle A101. Venez nombreux !',
        type: 'EVENT',
        viewsCount: 42,
        createdAt: new Date().toISOString(),
      },
      {
        id: '2',
        author: { id: 'u2', name: 'Mouvement Bleu', campusStatus: 'Enseignant vérifié' },
        content: 'Notre programme pour les élections BDE 2027 est en ligne. Découvrez nos propositions pour améliorer la vie étudiante.',
        type: 'TEXT',
        isSponsored: true,
        viewsCount: 128,
        createdAt: new Date(Date.now() - 3600 * 1000).toISOString(),
      },
    ];
    setPosts(mockPosts);
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchPosts();
  }, [activeTab, fetchPosts]);

  const { pullDistance, isRefreshing, handleTouchStart, handleTouchMove, handleTouchEnd } =
    usePullToRefresh(scrollRef, fetchPosts);

  const tabs = [
    { id: 'pour_toi', label: 'Pour toi', icon: Sparkles },
    { id: 'mon_etablissement', label: 'Mon établissement', icon: Building },
    { id: 'mes_communautes', label: 'Mes communautés', icon: Users },
    { id: 'opportunites', label: 'Opportunités', icon: Briefcase },
  ] as const;

  return (
    <div
      ref={scrollRef}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      className="max-w-2xl mx-auto p-4 md:p-6 pb-24 md:pb-6"
      style={{ transform: `translateY(${pullDistance}px)`, transition: pullDistance === 0 ? 'transform 0.2s' : 'none' }}
    >
      {/* Indicateur pull‑to‑refresh */}
      <div className="flex justify-center mb-2">
        <ChevronDown
          className={cn(
            'h-6 w-6 text-gray-400 transition-transform',
            isRefreshing ? 'animate-spin' : '',
            pullDistance > 50 ? 'rotate-180' : ''
          )}
        />
      </div>

      {/* Bouton de création */}
      <CreatePostTrigger onClick={() => setShowCreateModal(true)} />

      {/* Onglets */}
      <div className="flex gap-2 overflow-x-auto mt-4 pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap',
              'bg-background-light dark:bg-slate-800 shadow-neo-extruded dark:shadow-neo-dark-extruded',
              activeTab === tab.id
                ? 'bg-pineapple text-white shadow-neo-pressed dark:shadow-neo-dark-pressed'
                : 'text-gray-600 dark:text-gray-300'
            )}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Liste des posts */}
      <div className="space-y-4 mt-4">
        {loading ? (
          <>
            <SkeletonPostCard />
            <SkeletonPostCard />
            <SkeletonPostCard />
          </>
        ) : (
          posts.map((post) => <PostCard key={post.id} post={post} />)
        )}
      </div>

      {/* Modale de création (placeholder) */}
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
              className="bg-white dark:bg-slate-900 rounded-3xl p-6 w-full max-w-lg shadow-neo-extruded dark:shadow-neo-dark-extruded"
              onClick={(e) => e.stopPropagation()}
            >
              <h2 className="text-lg font-semibold mb-4">Créer une publication</h2>
              <p className="text-sm text-gray-500">Formulaire à venir</p>
              <button
                className="mt-4 px-4 py-2 bg-pineapple text-white rounded-xl"
                onClick={() => setShowCreateModal(false)}
              >
                Fermer
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};