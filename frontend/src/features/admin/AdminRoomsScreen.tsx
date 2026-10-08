// frontend/src/features/admin/AdminRoomsScreen.tsx

import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Building, CheckCircle2, ShieldAlert } from 'lucide-react';
import apiClient from '@/lib/api/client';
import { endpoints } from '@/lib/api/endpoints';

interface Room {
  id: string;
  name: string;
  building?: string;
  capacity?: number;
  is_active: boolean;
  current_status?: string;
}

export const AdminRoomsScreen: React.FC = () => {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    building: '',
    capacity: 100,
  });
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchRooms = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get(endpoints.admin.rooms);
      setRooms(res.data.items || res.data || []);
    } catch (err: any) {
      console.error(err);
      setMessage({ type: 'error', text: 'Impossible de charger les salles.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRooms();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingId) {
        await apiClient.put(`${endpoints.admin.rooms}/${editingId}`, formData);
        setMessage({ type: 'success', text: 'Salle mise à jour.' });
      } else {
        await apiClient.post(endpoints.admin.rooms, formData);
        setMessage({ type: 'success', text: 'Salle créée avec succès.' });
      }
      setShowModal(false);
      setEditingId(null);
      setFormData({ name: '', building: '', capacity: 100 });
      fetchRooms();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.message || 'Erreur lors de l’enregistrement.' });
    }
  };

  const handleEdit = (room: Room) => {
    setEditingId(room.id);
    setFormData({
      name: room.name,
      building: room.building || '',
      capacity: room.capacity || 100,
    });
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Voulez-vous vraiment désactiver cette salle ?')) return;
    try {
      await apiClient.delete(`${endpoints.admin.rooms}/${id}`);
      setMessage({ type: 'success', text: 'Salle désactivée.' });
      fetchRooms();
    } catch (err: any) {
      setMessage({ type: 'error', text: 'Erreur lors de la suppression.' });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Gestion des Salles Physiques</h1>
          <p className="text-sm text-gray-500">
            Configurez les amphithéâtres, salles de TD et laboratoires de l'établissement.
          </p>
        </div>
        <button
          onClick={() => {
            setEditingId(null);
            setFormData({ name: '', building: '', capacity: 100 });
            setShowModal(true);
          }}
          className="px-4 py-2.5 bg-pineapple hover:bg-pineapple-hover text-white text-sm font-semibold rounded-xl shadow-md transition flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Ajouter une salle
        </button>
      </div>

      {message && (
        <div
          className={`p-4 rounded-xl text-sm font-medium flex items-center gap-2 ${
            message.type === 'success'
              ? 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20'
              : 'bg-rose-500/10 text-rose-600 border border-rose-500/20'
          }`}
        >
          {message.type === 'success' ? <CheckCircle2 className="h-5 w-5" /> : <ShieldAlert className="h-5 w-5" />}
          {message.text}
        </div>
      )}

      {loading ? (
        <div className="p-12 text-center text-gray-400 text-sm">Chargement des salles...</div>
      ) : rooms.length === 0 ? (
        <div className="p-12 text-center text-gray-400 text-sm">Aucune salle configurée.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {rooms.map((room) => (
            <div
              key={room.id}
              className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 shadow-sm flex flex-col justify-between hover:shadow-md transition"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="flex items-center gap-1.5 text-xs text-gray-400">
                    <Building className="h-3.5 w-3.5" />
                    {room.building || 'Bâtiment Principal'}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-500/10 text-emerald-600">
                    Actif
                  </span>
                </div>
                <h3 className="text-lg font-bold text-gray-800 dark:text-white mb-1">{room.name}</h3>
                <p className="text-xs text-gray-500">Capacité: {room.capacity || 'N/A'} places</p>
              </div>

              <div className="pt-4 mt-4 border-t border-gray-100 dark:border-slate-700 flex items-center justify-between">
                <span className="text-xs font-semibold text-gray-400">
                  État: {room.current_status || 'FREE'}
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleEdit(room)}
                    className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700 text-gray-600 dark:text-gray-300 transition"
                  >
                    <Edit2 className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(room.id)}
                    className="p-1.5 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-900/20 text-rose-600 transition"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal Création / Édition */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h2 className="text-lg font-bold text-gray-800 dark:text-white">
              {editingId ? 'Modifier la salle' : 'Ajouter une salle'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300 mb-1">
                  Nom de la salle (ex. Amphi 500, Salle TD B12)
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-pineapple/50"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300 mb-1">
                    Bâtiment
                  </label>
                  <input
                    type="text"
                    value={formData.building}
                    onChange={(e) => setFormData({ ...formData, building: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-pineapple/50"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300 mb-1">
                    Capacité (places)
                  </label>
                  <input
                    type="number"
                    value={formData.capacity}
                    onChange={(e) => setFormData({ ...formData, capacity: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-pineapple/50"
                    required
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-slate-700"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-pineapple text-white text-xs font-semibold rounded-xl hover:bg-pineapple-hover"
                >
                  Enregistrer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
