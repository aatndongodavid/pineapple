// frontend/src/features/feed/PostCard.tsx

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Heart,
  MessageCircle,
  Share2,
  Eye,
  MapPin,
  BadgeCheck,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// --- Types basés sur le DTO Backend (étendus pour l'affichage) ---
type AudienceScope = 'LOCAL' | 'EXTENDED' | 'SPONSORED' | 'PUBLIC';
type PostType = 'TEXT' | 'IMAGE' | 'VIDEO' | 'EVENT' | 'PROJECT';

interface PostAuthor {
  id: string;
  name: string;
  campusStatus?: string;      // ex: "Étudiant certifié"
  avatarUrl?: string;
}

interface PostCardData {
  id: string;
  author: PostAuthor;
  content: string;
  post_type: PostType;
  media_urls?: string[];
  scope: AudienceScope;
  is_sponsored?: boolean;
  views_count: number;
  created_at: string;
  organization?: string;      // nom de l'organisation si applicable
}

interface PostCardProps {
  post: PostCardData;
  className?: string;
}

// --- Helpers ---
function formatRelativeDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "à l'instant";
  if (diffMin < 60) return `il y a ${diffMin} min`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `il y a ${diffHours} h`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays === 1) return 'hier';
  if (diffDays < 7) return `il y a ${diffDays} jours`;
  return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
}

function getScopeLabel(scope: AudienceScope, isSponsored?: boolean): string {
  if (isSponsored) return 'Sponsorisé';
  switch (scope) {
    case 'LOCAL':
      return 'Local';
    case 'EXTENDED':
      return 'Étendu';
    case 'PUBLIC':
      return 'Public';
    default:
      return scope;
  }
}

// --- Grille d'images dynamique ---
const ImageGrid: React.FC<{ images: string[] }> = ({ images }) => {
  const count = images.length;
  if (count === 0) return null;

  if (count === 1) {
    return (
      <div className="mt-3 rounded-xl overflow-hidden">
        <img
          src={images[0]}
          alt="Contenu"
          className="w-full h-64 object-cover"
          loading="lazy"
        />
      </div>
    );
  }

  if (count === 2) {
    return (
      <div className="mt-3 grid grid-cols-2 gap-1 rounded-xl overflow-hidden">
        {images.map((src, idx) => (
          <img
            key={idx}
            src={src}
            alt={`Image ${idx + 1}`}
            className="h-48 w-full object-cover"
            loading="lazy"
          />
        ))}
      </div>
    );
  }

  // 3+ images : première grande à gauche, deux petites à droite
  return (
    <div className="mt-3 grid grid-cols-3 gap-1 rounded-xl overflow-hidden">
      <img
        src={images[0]}
        alt="Image principale"
        className="col-span-2 row-span-2 h-full w-full object-cover"
        loading="lazy"
      />
      {images.slice(1, 3).map((src, idx) => (
        <img
          key={idx}
          src={src}
          alt={`Image ${idx + 2}`}
          className="h-24 w-full object-cover"
          loading="lazy"
        />
      ))}
      {images.length > 3 && (
        <div className="relative h-24 w-full bg-gray-800 flex items-center justify-center text-white text-sm">
          +{images.length - 3}
        </div>
      )}
    </div>
  );
};

// --- Composant principal ---
export const PostCard: React.FC<PostCardProps> = ({ post, className }) => {
  const [isLiked, setIsLiked] = useState(false);
  const [likesCount, setLikesCount] = useState(0); // initialisé à 0, on pourrait le passer en prop
  const [isExpanded, setIsExpanded] = useState(false);
  const [showAllText, setShowAllText] = useState(false);

  const handleLike = () => {
    setIsLiked((prev) => !prev);
    setLikesCount((prev) => (isLiked ? prev - 1 : prev + 1));
  };

  const handleToggleText = () => setShowAllText((prev) => !prev);

  const scopeLabel = getScopeLabel(post.scope, post.is_sponsored);
  const shouldTruncate = post.content.length > 200;
  const displayedContent =
    shouldTruncate && !showAllText ? `${post.content.substring(0, 200)}...` : post.content;

  return (
    <div
      className={cn(
        'p-5 rounded-2xl bg-white dark:bg-slate-800 shadow-neo-extruded dark:shadow-neo-dark-extruded transition-shadow',
        'hover:shadow-neo-pressed dark:hover:shadow-neo-dark-pressed',
        className
      )}
    >
      {/* En-tête */}
      <div className="flex items-start gap-3">
        {/* Avatar */}
        <div className="w-11 h-11 rounded-full bg-pineapple/20 flex items-center justify-center text-pineapple font-bold shrink-0">
          {post.author.avatarUrl ? (
            <img src={post.author.avatarUrl} alt={post.author.name} className="w-full h-full rounded-full object-cover" />
          ) : (
            post.author.name.charAt(0).toUpperCase()
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center flex-wrap gap-1">
            <span className="font-semibold text-gray-800 dark:text-white truncate">
              {post.author.name}
            </span>
            {post.author.campusStatus && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-emerald-100 text-emerald-700">
                <BadgeCheck className="w-3 h-3 mr-1" />
                {post.author.campusStatus}
              </span>
            )}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {formatRelativeDate(post.created_at)}
            {post.organization && <span> · {post.organization}</span>}
          </div>
        </div>

        {/* Indicateur de portée */}
        <span
          className={cn(
            'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
            post.is_sponsored
              ? 'bg-yellow-100 text-yellow-700'
              : post.scope === 'LOCAL'
                ? 'bg-gray-100 text-gray-600'
                : 'bg-blue-100 text-blue-700'
          )}
        >
          <MapPin className="w-3 h-3 mr-1" />
          {scopeLabel}
        </span>
      </div>

      {/* Corps : texte */}
      <div className="mt-3">
        <p className="text-gray-700 dark:text-gray-300 whitespace-pre-line break-words">
          {displayedContent}
        </p>
        {shouldTruncate && (
          <button
            onClick={handleToggleText}
            className="mt-1 text-sm text-pineapple font-medium flex items-center gap-1"
          >
            {showAllText ? (
              <>
                Voir moins <ChevronUp className="w-4 h-4" />
              </>
            ) : (
              <>
                Voir plus <ChevronDown className="w-4 h-4" />
              </>
            )}
          </button>
        )}
      </div>

      {/* Grille d'images */}
      {post.media_urls && post.media_urls.length > 0 && (
        <ImageGrid images={post.media_urls} />
      )}

      {/* Pied de carte */}
      <div className="mt-4 pt-3 border-t border-gray-200 dark:border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-1 text-gray-500 dark:text-gray-400">
          <Eye className="w-4 h-4" />
          <span className="text-xs">{post.views_count} vues</span>
        </div>

        <div className="flex items-center gap-4">
          {/* Like */}
          <motion.button
            whileTap={{ scale: 0.85 }}
            onClick={handleLike}
            className={cn(
              'flex items-center gap-1 text-sm transition-colors',
              isLiked ? 'text-red-500' : 'text-gray-500 hover:text-red-400'
            )}
            aria-label="J'aime"
          >
            <Heart className={cn('w-5 h-5', isLiked && 'fill-current')} />
            <span>{likesCount > 0 ? likesCount : ''}</span>
          </motion.button>

          {/* Commentaire */}
          <button className="flex items-center gap-1 text-sm text-gray-500 hover:text-pineapple transition-colors">
            <MessageCircle className="w-5 h-5" />
            <span>{/* nombre de commentaires si dispo */}</span>
          </button>

          {/* Partager */}
          <button className="flex items-center gap-1 text-sm text-gray-500 hover:text-pineapple transition-colors">
            <Share2 className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};