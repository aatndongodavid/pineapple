// frontend/src/features/campus_life/RideCard.tsx

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { MapPin, Clock, User, Users, ShieldAlert } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';

export interface Ride {
  id: string;
  driver: {
    id: string;
    name: string;
    isCertified: boolean;
  };
  departure: string;
  destination: string;
  departureTime: string; // ISO string
  totalSeats: number;
  availableSeats: number;
  pricePerSeat: number; // en FCFA
}

interface RideCardProps {
  ride: Ride;
  onBook: (rideId: string) => void;
}

function formatTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
}

export const RideCard: React.FC<RideCardProps> = ({ ride, onBook }) => {
  const [isBooking, setIsBooking] = useState(false);
  const isFull = ride.availableSeats === 0;

  const handleBook = async () => {
    if (isFull || isBooking) return;
    setIsBooking(true);
    // Simuler un délai de réservation
    await new Promise(resolve => setTimeout(resolve, 800));
    setIsBooking(false);
    onBook(ride.id);
  };

  const remainingPercentage = (ride.availableSeats / ride.totalSeats) * 100;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.2 }}
    >
      <Card variant="neo-extruded" className="p-5 h-full flex flex-col">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1 text-sm font-medium text-gray-800 dark:text-white">
              <MapPin className="h-4 w-4 text-pineapple" />
              <span className="truncate">{ride.departure}</span>
            </div>
            <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-300 mt-1">
              <MapPin className="h-4 w-4 text-gray-400" />
              <span className="truncate">{ride.destination}</span>
            </div>
          </div>
          <Badge variant={isFull ? 'danger' : 'success'} className="ml-2 shrink-0">
            {isFull ? 'Complet' : `${ride.availableSeats} place(s)`}
          </Badge>
        </div>

        <div className="flex items-center gap-2 text-xs text-gray-500 mt-1">
          <Clock className="h-3.5 w-3.5" />
          <span>{formatDate(ride.departureTime)} à {formatTime(ride.departureTime)}</span>
        </div>

        <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
          <User className="h-3.5 w-3.5" />
          <span>{ride.driver.name}</span>
          {ride.driver.isCertified && (
            <Badge variant="success" className="text-xs">Certifié</Badge>
          )}
        </div>

        {/* Jauge des places */}
        <div className="mt-4">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Places disponibles</span>
            <span>{ride.availableSeats}/{ride.totalSeats}</span>
          </div>
          <div className="h-2 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${remainingPercentage}%` }}
              transition={{ duration: 0.5 }}
              className={cn(
                'h-full rounded-full',
                remainingPercentage > 50 ? 'bg-emerald-500' : remainingPercentage > 20 ? 'bg-yellow-500' : 'bg-red-500'
              )}
            />
          </div>
        </div>

        <div className="mt-4 flex items-center justify-between">
          <span className="text-lg font-bold text-pineapple">
            {ride.pricePerSeat.toLocaleString('fr-FR')} FCFA
          </span>
          <span className="text-xs text-gray-400">/ place</span>
        </div>

        <div className="mt-4">
          <Button
            variant="primary"
            size="sm"
            className="w-full"
            onClick={handleBook}
            isLoading={isBooking}
            disabled={isFull}
            icon={Users}
          >
            {isFull ? 'Complet' : 'Réserver ma place'}
          </Button>
        </div>

        {/* Disclaimer */}
        <div className="mt-3 flex items-start gap-2 text-xs text-gray-500 dark:text-gray-400 bg-background-light dark:bg-slate-800 p-2 rounded-lg">
          <ShieldAlert className="h-4 w-4 text-amber-500 shrink-0" />
          <span>
            Pineapple est uniquement un coordinateur numérique, le paiement se fait entre étudiants.
          </span>
        </div>
      </Card>
    </motion.div>
  );
};