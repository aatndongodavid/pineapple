// frontend/src/components/community/RoomDeclarationModal.tsx

import React, { useState } from 'react';
import { ShieldCheck, Flag, CheckCircle2, ShieldAlert } from 'lucide-react';
import apiClient from '@/lib/api/client';
import { endpoints } from '@/lib/api/endpoints';
import { useAuthStore } from '@/lib/store/authStore';

interface RoomDeclarationModalProps {
  roomId: string;
  roomName: string;
  currentStatus: string;
  onClose: () => void;
  onSuccess: () => void;
}

export const RoomDeclarationModal: React.FC<RoomDeclarationModalProps> = ({
  roomId,
  roomName,
  currentStatus,
  onClose,
  onSuccess,
}) => {
  const { can } = useAuthStore();
  const isDelegate = can('room.declare_status');

  const [status, setStatus] = useState<'OCCUPIED' | 'FREE'>('OCCUPIED');
  const [note, setNote] = useState('');
  const [flagReason, setFlagReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleDeclare = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await apiClient.post(endpoints.community.declareRoomStatus(roomId), {
        status,
        note: note || undefined,
      });
      setMessage({ type: 'success', text: `Statut de la salle ${roomName} mis à jour.` });
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1000);
    } catch (err: any) {
      setMessage({
        type: 'error',
        text: err.response?.data?.message || 'Erreur lors de la déclaration du statut.',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFlagInconsistency = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await apiClient.post(`${endpoints.community.rooms}/${roomId}/flag`, {
        reason: flagReason,
      });
      setMessage({ type: 'success', text: 'Incohérence signalée au délégué et à l\'administration.' });
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1000);
    } catch (err: any) {
      setMessage({
        type: 'error',
        text: err.response?.data?.message || 'Erreur lors du signalement.',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
        <h2 className="text-lg font-bold text-gray-800 dark:text-white">
          {isDelegate ? `Déclarer l'état de la salle : ${roomName}` : `Signaler une incohérence : ${roomName}`}
        </h2>

        {message && (
          <div
            className={`p-3 rounded-xl text-xs font-medium flex items-center gap-2 ${
              message.type === 'success'
                ? 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20'
                : 'bg-rose-500/10 text-rose-600 border border-rose-500/20'
            }`}
          >
            {message.type === 'success' ? <CheckCircle2 className="h-4 w-4" /> : <ShieldAlert className="h-4 w-4" />}
            {message.text}
          </div>
        )}

        {isDelegate ? (
          <form onSubmit={handleDeclare} className="space-y-4 text-sm">
            <div>
              <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300 mb-2">
                Nouveau statut de la salle (Action Délégué)
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setStatus('OCCUPIED')}
                  className={`p-3 rounded-xl font-bold border transition ${
                    status === 'OCCUPIED'
                      ? 'bg-amber-500/15 border-amber-500 text-amber-600'
                      : 'border-gray-200 dark:border-slate-700 text-gray-500'
                  }`}
                >
                  Occupée par mon cours
                </button>
                <button
                  type="button"
                  onClick={() => setStatus('FREE')}
                  className={`p-3 rounded-xl font-bold border transition ${
                    status === 'FREE'
                      ? 'bg-emerald-500/15 border-emerald-500 text-emerald-600'
                      : 'border-gray-200 dark:border-slate-700 text-gray-500'
                  }`}
                >
                  Libérée
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300 mb-1">
                Note facultative (ex. Cours de Mathématiques jusqu'à 12h)
              </label>
              <input
                type="text"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Précisions..."
                className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-pineapple/50"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-slate-700"
              >
                Annuler
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-pineapple text-white text-xs font-semibold rounded-xl hover:bg-pineapple-hover flex items-center gap-1.5"
              >
                <ShieldCheck className="h-4 w-4" />
                Déclarer l'état
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleFlagInconsistency} className="space-y-4 text-sm">
            <p className="text-xs text-gray-500">
              Seuls les délégués de classe peuvent déclarer si une salle est occupée. Si vous constatez que l'état indiqué ({currentStatus}) ne correspond pas à la réalité, signalez-le.
            </p>

            <div>
              <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300 mb-1">
                Motif du signalement
              </label>
              <textarea
                value={flagReason}
                onChange={(e) => setFlagReason(e.target.value)}
                placeholder="Ex. La salle est en réalité vide..."
                rows={3}
                className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-pineapple/50"
                required
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-slate-700"
              >
                Annuler
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-amber-500 text-white text-xs font-semibold rounded-xl hover:bg-amber-600 flex items-center gap-1.5"
              >
                <Flag className="h-4 w-4" />
                Signaler au délégué
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
