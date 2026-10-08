// frontend/src/features/admin/AdminClassesScreen.tsx

import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Users, CheckCircle2, ShieldAlert } from 'lucide-react';
import apiClient from '@/lib/api/client';
import { endpoints } from '@/lib/api/endpoints';

interface ClassGroup {
  id: string;
  name: string;
  code: string;
  faculty?: string;
  filiere?: string;
  level?: string;
  academic_year: string;
  capacity?: number;
  is_active: boolean;
}

export const AdminClassesScreen: React.FC = () => {
  const [classes, setClasses] = useState<ClassGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    faculty: '',
    filiere: '',
    level: '',
    academic_year: '2026-2027',
    capacity: 50,
  });
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchClasses = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get(endpoints.admin.classes);
      setClasses(res.data.items || res.data || []);
    } catch (err: any) {
      console.error(err);
      setMessage({ type: 'error', text: 'Impossible de charger les classes.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClasses();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingId) {
        await apiClient.put(`${endpoints.admin.classes}/${editingId}`, formData);
        setMessage({ type: 'success', text: 'Classe mise à jour.' });
      } else {
        await apiClient.post(endpoints.admin.classes, formData);
        setMessage({ type: 'success', text: 'Classe créée avec succès.' });
      }
      setShowModal(false);
      setEditingId(null);
      setFormData({ name: '', code: '', faculty: '', filiere: '', level: '', academic_year: '2026-2027', capacity: 50 });
      fetchClasses();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.message || 'Erreur lors de l’enregistrement.' });
    }
  };

  const handleEdit = (cls: ClassGroup) => {
    setEditingId(cls.id);
    setFormData({
      name: cls.name,
      code: cls.code,
      faculty: cls.faculty || '',
      filiere: cls.filiere || '',
      level: cls.level || '',
      academic_year: cls.academic_year,
      capacity: cls.capacity || 50,
    });
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Voulez-vous vraiment désactiver cette classe ?')) return;
    try {
      await apiClient.delete(`${endpoints.admin.classes}/${id}`);
      setMessage({ type: 'success', text: 'Classe désactivée.' });
      fetchClasses();
    } catch (err: any) {
      setMessage({ type: 'error', text: 'Erreur lors de la suppression.' });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Gestion des Classes</h1>
          <p className="text-sm text-gray-500">
            Définissez les promotions / filières de l'établissement (ex. GIT 3, MSP 1).
          </p>
        </div>
        <button
          onClick={() => {
            setEditingId(null);
            setFormData({ name: '', code: '', faculty: '', filiere: '', level: '', academic_year: '2026-2027', capacity: 50 });
            setShowModal(true);
          }}
          className="px-4 py-2.5 bg-pineapple hover:bg-pineapple-hover text-white text-sm font-semibold rounded-xl shadow-md transition flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Ajouter une classe
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

      {/* Grid des classes */}
      {loading ? (
        <div className="p-12 text-center text-gray-400 text-sm">Chargement des classes...</div>
      ) : classes.length === 0 ? (
        <div className="p-12 text-center text-gray-400 text-sm">Aucune classe définie.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {classes.map((cls) => (
            <div
              key={cls.id}
              className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 shadow-sm flex flex-col justify-between hover:shadow-md transition"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="px-2.5 py-1 bg-pineapple/10 text-pineapple font-mono text-xs font-bold rounded-lg uppercase">
                    {cls.code}
                  </span>
                  <span className="text-xs text-gray-400">{cls.academic_year}</span>
                </div>
                <h3 className="text-lg font-bold text-gray-800 dark:text-white mb-1">{cls.name}</h3>
                <p className="text-xs text-gray-500 mb-4">
                  {cls.faculty || 'Faculté non spécifiée'} • {cls.filiere || 'Filière'} ({cls.level || 'Niveau'})
                </p>
              </div>

              <div className="pt-4 border-t border-gray-100 dark:border-slate-700 flex items-center justify-between text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <Users className="h-4 w-4 text-gray-400" />
                  Capacité: {cls.capacity || 'N/A'}
                </span>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleEdit(cls)}
                    className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700 text-gray-600 dark:text-gray-300 transition"
                  >
                    <Edit2 className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(cls.id)}
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

      {/* Modal Modal Création / Édition */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h2 className="text-lg font-bold text-gray-800 dark:text-white">
              {editingId ? 'Modifier la classe' : 'Ajouter une classe'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300 mb-1">
                  Nom complet (ex. Genie Informatique 3)
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
                    Code unique (ex. GIT3)
                  </label>
                  <input
                    type="text"
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                    className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 font-mono focus:outline-none focus:ring-2 focus:ring-pineapple/50"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300 mb-1">
                    Année académique
                  </label>
                  <input
                    type="text"
                    value={formData.academic_year}
                    onChange={(e) => setFormData({ ...formData, academic_year: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-pineapple/50"
                    required
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300 mb-1">
                    Faculté / Département
                  </label>
                  <input
                    type="text"
                    value={formData.faculty}
                    onChange={(e) => setFormData({ ...formData, faculty: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-pineapple/50"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 dark:text-gray-300 mb-1">
                    Filière
                  </label>
                  <input
                    type="text"
                    value={formData.filiere}
                    onChange={(e) => setFormData({ ...formData, filiere: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-pineapple/50"
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
