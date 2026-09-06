// frontend/src/features/campus_life/PineappleRideScreen.tsx

import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Search, Plus, MapPin, CalendarDays } from 'lucide-react';
import { RideCard, Ride } from './RideCard';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';

// Données simulées
const mockRides: Ride[] = [
  {
    id: 'r1',
    driver: { id: 'd1', name: 'Alice Ndongo', isCertified: true },
    departure: 'Bonamoussadi',
    destination: 'Campus ENSPD',
    departureTime: new Date(Date.now() + 3600 * 1000).toISOString(),
    totalSeats: 4,
    availableSeats: 2,
    pricePerSeat: 500,
  },
  {
    id: 'r2',
    driver: { id: 'd2', name: 'Bob Kamga', isCertified: true },
    departure: 'Campus ENSPD',
    destination: 'Akwa',
    departureTime: new Date(Date.now() + 7200 * 1000).toISOString(),
    totalSeats: 3,
    availableSeats: 1,
    pricePerSeat: 300,
  },
  {
    id: 'r3',
    driver: { id: 'd3', name: 'Charlie Mbarga', isCertified: false },
    departure: 'Ndokoti',
    destination: 'Campus ENSPD',
    departureTime: new Date(Date.now() + 1800 * 1000).toISOString(),
    totalSeats: 4,
    availableSeats: 0,
    pricePerSeat: 400,
  },
];

export const PineappleRideScreen: React.FC = () => {
  const [departureQuery, setDepartureQuery] = useState('');
  const [destinationQuery, setDestinationQuery] = useState('');
  const [timeQuery, setTimeQuery] = useState('');

  const filteredRides = useMemo(() => {
    return mockRides.filter((ride) => {
      const matchesDeparture = ride.departure.toLowerCase().includes(departureQuery.toLowerCase());
      const matchesDestination = ride.destination.toLowerCase().includes(destinationQuery.toLowerCase());
      // Filtre par heure simple : on vérifie si l'heure saisie correspond approximativement
      let matchesTime = true;
      if (timeQuery) {
        const rideHour = new Date(ride.departureTime).getHours();
        const queryHour = parseInt(timeQuery, 10);
        matchesTime = !isNaN(queryHour) && rideHour >= queryHour;
      }
      return matchesDeparture && matchesDestination && matchesTime;
    });
  }, [departureQuery, destinationQuery, timeQuery]);

  return (
    <div className="max-w-5xl mx-auto p-4 md:p-6 pb-24 md:pb-6 space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Pineapple Ride</h1>
        <Button variant="primary" icon={Plus}>Proposer un trajet</Button>
      </motion.div>

      {/* Formulaire de recherche */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="relative">
          <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Départ"
            value={departureQuery}
            onChange={(e) => setDepartureQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-3 rounded-2xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
          />
        </div>
        <div className="relative">
          <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Destination"
            value={destinationQuery}
            onChange={(e) => setDestinationQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-3 rounded-2xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
          />
        </div>
        <div className="relative">
          <CalendarDays className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="number"
            placeholder="Heure (ex: 14)"
            value={timeQuery}
            onChange={(e) => setTimeQuery(e.target.value)}
            min={0}
            max={23}
            className="w-full pl-10 pr-4 py-3 rounded-2xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
          />
        </div>
      </div>

      {/* Liste des trajets */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {filteredRides.map((ride) => (
          <RideCard
            key={ride.id}
            ride={ride}
            onBook={(rideId) => console.log('Réserver trajet', rideId)}
          />
        ))}
      </div>

      {filteredRides.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          Aucun trajet trouvé pour ces critères.
        </div>
      )}
    </div>
  );
};