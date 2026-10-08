// frontend/src/features/community/RoomsScreen.tsx

import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Clock, MapPin, CheckCircle2, XCircle, HelpCircle, DoorOpen, ShieldCheck, Flag } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { cn } from '@/lib/utils';
import apiClient from '@/lib/api/client';
import { endpoints } from '@/lib/api/endpoints';
import { useAuthStore } from '@/lib/store/authStore';
import { RoomDeclarationModal } from '@/components/community/RoomDeclarationModal';

type RoomStatus = 'FREE' | 'OCCUPIED' | 'TO_CONFIRM';

interface Room {
  id: string;
  name: string;
  building: string;
  status: RoomStatus;
  declared_by_user_id?: string;
  expires_at?: string | null;
}

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
      return { color: 'bg-rose-500', label: 'Occupée', icon: XCircle };
    case 'TO_CONFIRM':
    default:
      return { color: 'bg-amber-500', label: 'À confirmer', icon: HelpCircle };
  }
}

export const RoomsScreen: React.FC = () => {
  const { can } = useAuthStore();
  const isDelegate = can('room.declare_status');

  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);
  const [now, setNow] = useState(new Date());
  const [selectedRoom, setSelectedRoom] = useState<Room | null>(null);

  const fetchRooms = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiClient.get(endpoints.community.rooms);
      setRooms(res.data.items || res.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRooms();
  }, [fetchRooms]);

  useEffect(() => {
    const interval = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-6 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <motion.h1
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-2"
          >
            <DoorOpen className="h-7 w-7 text-pineapple" />
            État des Salles Physiques
          </motion.h1>
          <p className="text-sm text-gray-500">
            {isDelegate
              ? 'En tant que délégué, vous pouvez déclarer l\'occupation ou la libération d\'une salle par votre classe.'
              : 'Consultez en temps réel la disponibilité des salles. Signalez toute incohérence aux délégués.'}
          </p>
        </div>
      </div>

      {loading ? (
        <div className="p-12 text-center text-gray-400 text-sm">Chargement des salles...</div>
      ) : rooms.length === 0 ? (
        <div className="p-12 text-center text-gray-400 text-sm">Aucune salle disponible pour le moment.</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {rooms.map((room) => {
            const statusInfo = getStatusInfo(room.status);
            const remaining = room.expires_at ? formatRemainingTime(room.expires_at, now) : null;

            return (
              <Card key={room.id} variant="neo-extruded" className="p-5 flex flex-col justify-between space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <h3 className="font-bold text-lg text-gray-800 dark:text-white flex items-center gap-2">
                      <DoorOpen className="h-5 w-5 text-pineapple" />
                      {room.name}
                    </h3>
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-white dark:bg-slate-800 shadow-neo-inset">
                      <span className={cn('w-2 h-2 rounded-full', statusInfo.color)} />
                      {statusInfo.label}
                    </span>
                  </div>

                  <p className="text-xs text-gray-500 flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5 text-gray-400" />
                    {room.building || 'Bâtiment Principal'}
                  </p>

                  {remaining && room.status === 'FREE' && (
                    <p className="text-xs text-emerald-600 flex items-center gap-1 font-medium">
                      <Clock className="h-3.5 w-3.5" />
                      Libre pour encore : {remaining}
                    </p>
                  )}
                </div>

                <div className="pt-3 border-t border-gray-100 dark:border-slate-700 flex justify-end">
                  <button
                    onClick={() => setSelectedRoom(room)}
                    className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 ${
                      isDelegate
                        ? 'bg-pineapple text-white hover:bg-pineapple-hover shadow-sm'
                        : 'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200'
                    }`}
                  >
                    {isDelegate ? (
                      <>
                        <ShieldCheck className="h-4 w-4" />
                        Déclarer l'état
                      </>
                    ) : (
                      <>
                        <Flag className="h-4 w-4" />
                        Signaler une erreur
                      </>
                    )}
                  </button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {selectedRoom && (
        <RoomDeclarationModal
          roomId={selectedRoom.id}
          roomName={selectedRoom.name}
          currentStatus={selectedRoom.status}
          onClose={() => setSelectedRoom(null)}
          onSuccess={fetchRooms}
        />
      )}
    </div>
  );
};