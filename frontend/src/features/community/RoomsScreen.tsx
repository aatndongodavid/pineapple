// frontend/src/features/community/RoomsScreen.tsx

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Clock,
  MapPin,
  CheckCircle2,
  XCircle,
  HelpCircle,
  MoreVertical,
  DoorOpen,
  X,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';

// ---------- Types ----------
type RoomStatus = 'FREE' | 'OCCUPIED' | 'TO_CONFIRM';

interface Room {
  id: string;
  tenant_id: string;
  name: string;
  building: string;
  status: RoomStatus;
  declared_by_user_id: string;
  expires_at: string | null; // ISO date
}

// Données simulées
const mockRooms: Room[] = [
  {
    id: 'room-1',
    tenant_id: 'tenant-1',
    name: 'Salle A101',
    building: 'Bâtiment A',
    status: 'FREE',
    declared_by_user_id: 'user-1',
    expires_at: new Date(Date.now() + 55 * 60 * 1000).toISOString(),
  },
  {
    id: 'room-2',
    tenant_id: 'tenant-1',
    name: 'Salle B202',
    building: 'Bâtiment B',
    status: 'OCCUPIED',
    declared_by_user_id: 'user-2',
    expires_at: null,
  },
  {
    id: 'room-3',
    tenant_id: 'tenant-1',
    name: 'Amphi 500',
    building: 'Amphithéâtre',
    status: 'TO_CONFIRM',
    declared_by_user_id: 'user-3',
    expires_at: null,
  },
];

// ---------- Helpers ----------
function formatRemainingTime(expiresAt: string, now: Date): string | null {
  const exp = new Date(expiresAt);
  const diff = exp.getTime() - now.getTime();
  if (diff <= 0) return 'Expiré';
  const minutes = Math.floor(diff / 60000);
  const seconds = Math.floor((diff % 60000) / 1000);
  if (minutes > 0) {
    return `${minutes} min ${seconds.toString().padStart(2, '0')} s`;
  }
  return `${seconds} s`;
}

function getStatusInfo(status: RoomStatus) {
  switch (status) {
    case 'FREE':
      return { color: 'bg-emerald-500', label: 'Libre', icon: CheckCircle2 };
    case 'OCCUPIED':
      return { color: 'bg-red-500', label: 'Occupée', icon: XCircle };
    case 'TO_CONFIRM':
      return { color: 'bg-gray-400', label: 'À confirmer', icon: HelpCircle };
  }
}

// ---------- Composant RoomCard ----------
interface RoomCardProps {
  room: Room;
  now: Date;
  onDeclare: (roomId: string) => void;
}

const RoomCard: React.FC<RoomCardProps> = ({ room, now, onDeclare }) => {
  const statusInfo = getStatusInfo(room.status);
  const remaining = room.expires_at ? formatRemainingTime(room.expires_at, now) : null;

  return (
    <Card variant="neo-extruded" className="p-4 flex flex-col">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <DoorOpen className="h-5 w-5 text-pineapple" />
          <h3 className="font-semibold text-gray-800 dark:text-white">{room.name}</h3>
        </div>
        <button
          onClick={() => onDeclare(room.id)}
          className="p-1 rounded-full hover:bg-pineapple/10"
          aria-label="Déclarer le statut"
        >
          <MoreVertical className="h-5 w-5 text-gray-500" />
        </button>
      </div>
      <div className="mt-1 text-sm text-gray-500 dark:text-gray-400 flex items-center gap-1">
        <MapPin className="h-4 w-4" />
        {room.building}
      </div>

      <div className="mt-4 flex items-center justify-between">
        <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-white dark:bg-slate-800 shadow-neo-inset dark:shadow-neo-dark-inset">
          <span className={cn('w-2.5 h-2.5 rounded-full', statusInfo.color)} />
          {statusInfo.label}
        </span>

        {remaining && room.status === 'FREE' && (
          <span className="text-xs text-gray-500 flex items-center gap-1">
            <Clock className="h-4 w-4" />
            {remaining}
          </span>
        )}
      </div>
    </Card>
  );
};

// ---------- Composant principal ----------
export const RoomsScreen: React.FC = () => {
  const [rooms, setRooms] = useState<Room[]>(mockRooms);
  const [now, setNow] = useState(new Date());
  const [declareRoomId, setDeclareRoomId] = useState<string | null>(null);
  const [isDeclareOpen, setIsDeclareOpen] = useState(false);

  // Mise à jour du temps toutes les secondes
  useEffect(() => {
    const interval = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  const openDeclare = useCallback((roomId: string) => {
    setDeclareRoomId(roomId);
    setIsDeclareOpen(true);
  }, []);

  const closeDeclare = useCallback(() => {
    setIsDeclareOpen(false);
    setDeclareRoomId(null);
  }, []);

  const updateRoomStatus = useCallback(
    (roomId: string, status: RoomStatus, durationMinutes?: number) => {
      setRooms((prev) =>
        prev.map((room) => {
          if (room.id !== roomId) return room;
          let expiresAt: string | null = null;
          if (status === 'FREE' && durationMinutes) {
            expiresAt = new Date(Date.now() + durationMinutes * 60 * 1000).toISOString();
          }
          return { ...room, status, expires_at: expiresAt };
        })
      );
      closeDeclare();
    },
    [closeDeclare]
  );

  return (
    <div className="max-w-5xl mx-auto p-4 md:p-6 pb-24 md:pb-6 space-y-6">
      <motion.h1
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-2"
      >
        <MapPin className="h-7 w-7 text-pineapple" />
        Salles de classe
      </motion.h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {rooms.map((room) => (
          <RoomCard key={room.id} room={room} now={now} onDeclare={openDeclare} />
        ))}
      </div>

      {/* BottomSheet / Popover de déclaration */}
      <AnimatePresence>
        {isDeclareOpen && declareRoomId && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
            onClick={closeDeclare}
          >
            <motion.div
              initial={{ y: 100, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 100, opacity: 0 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="absolute bottom-0 left-0 right-0 md:bottom-auto md:top-1/2 md:left-1/2 md:-translate-x-1/2 md:-translate-y-1/2 w-full max-w-md mx-auto bg-white dark:bg-slate-900 rounded-t-3xl md:rounded-2xl shadow-neo-extruded dark:shadow-neo-dark-extruded p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-800 dark:text-white">
                  Déclarer le statut
                </h3>
                <button onClick={closeDeclare} className="p-1 rounded-full hover:bg-pineapple/10">
                  <X className="h-5 w-5 text-gray-500" />
                </button>
              </div>

              <div className="space-y-2">
                <Button
                  variant="secondary"
                  className="w-full justify-start"
                  onClick={() => updateRoomStatus(declareRoomId, 'FREE', 60)}
                  icon={CheckCircle2}
                >
                  Libre (1h)
                </Button>
                <Button
                  variant="secondary"
                  className="w-full justify-start"
                  onClick={() => updateRoomStatus(declareRoomId, 'FREE', 120)}
                  icon={CheckCircle2}
                >
                  Libre (2h)
                </Button>
                <Button
                  variant="secondary"
                  className="w-full justify-start"
                  onClick={() => updateRoomStatus(declareRoomId, 'OCCUPIED')}
                  icon={XCircle}
                >
                  Occupée
                </Button>
                <Button
                  variant="secondary"
                  className="w-full justify-start"
                  onClick={() => updateRoomStatus(declareRoomId, 'TO_CONFIRM')}
                  icon={HelpCircle}
                >
                  À confirmer
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};