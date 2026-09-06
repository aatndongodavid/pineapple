// frontend/src/features/campus_life/ListingCard.tsx

import React from 'react';
import { motion } from 'framer-motion';
import { MapPin, Clock, MessageCircle, User } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

export interface Listing {
  id: string;
  title: string;
  description: string;
  price: number; // en FCFA
  category: 'BOOKS' | 'ELECTRONICS' | 'CLOTHING' | 'SERVICES' | 'HOUSING' | 'OTHER';
  images: string[];
  seller: {
    id: string;
    name: string;
    isCertified: boolean;
  };
  createdAt: string;
}

interface ListingCardProps {
  listing: Listing;
  onContact: (listingId: string) => void;
}

function formatPrice(price: number): string {
  return `${price.toLocaleString('fr-FR')} FCFA`;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
}

export const ListingCard: React.FC<ListingCardProps> = ({ listing, onContact }) => {
  const fallbackImage = 'https://via.placeholder.com/300x200?text=Pineapple+Market';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.2 }}
    >
      <Card variant="neo-extruded" className="overflow-hidden h-full flex flex-col">
        {/* Image */}
        <div className="relative h-40 w-full bg-gray-200 dark:bg-slate-700">
          <img
            src={listing.images[0] || fallbackImage}
            alt={listing.title}
            className="w-full h-full object-cover"
            loading="lazy"
          />
          <div className="absolute top-2 right-2">
            <Badge variant="success" className="text-xs">
              {listing.category}
            </Badge>
          </div>
        </div>

        {/* Contenu */}
        <div className="p-4 flex flex-col flex-1">
          <h3 className="font-semibold text-gray-800 dark:text-white truncate">
            {listing.title}
          </h3>
          <p className="text-lg font-bold text-pineapple mt-1">
            {formatPrice(listing.price)}
          </p>
          <div className="flex items-center gap-1 mt-2 text-xs text-gray-500">
            <User className="h-3.5 w-3.5" />
            <span>{listing.seller.name}</span>
            {listing.seller.isCertified && (
              <Badge variant="success" className="ml-1 text-xs">Certifié</Badge>
            )}
          </div>
          <div className="flex items-center gap-1 mt-1 text-xs text-gray-400">
            <Clock className="h-3.5 w-3.5" />
            <span>{formatDate(listing.createdAt)}</span>
          </div>

          <div className="mt-auto pt-3">
            <Button
              variant="secondary"
              size="sm"
              className="w-full"
              onClick={() => onContact(listing.id)}
              icon={MessageCircle}
            >
              Contacter le vendeur
            </Button>
          </div>
        </div>
      </Card>
    </motion.div>
  );
};