// frontend/src/features/enrollment/JoinSchoolWizard.tsx

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, Search, CheckCircle2, AlertCircle, ArrowLeft, Loader2 } from 'lucide-react';
import apiClient from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import { useAuthStore } from '@/lib/store/authStore';

interface PublicSchool {
  id: string;
  name: string;
  code: string;
  logo_url?: string;
}

export const JoinSchoolWizard: React.FC = () => {
  const navigate = useNavigate();
  const { setAuthData, token } = useAuthStore();

  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [schools, setSchools] = useState<PublicSchool[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSchool, setSelectedSchool] = useState<PublicSchool | null>(null);

  // Formulaire d'état civil (Étape 2)
  const [formData, setFormData] = useState({
    last_name: '',
    first_name: '',
    matricule: '',
    birth_date: '',
    birth_place: '',
  });

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successStatus, setSuccessStatus] = useState<'ACTIVE' | 'PENDING' | null>(null);

  useEffect(() => {
    // Charger les établissements publics
    const fetchSchools = async () => {
      try {
        const resp = await apiClient.get(API_ENDPOINTS.schools.publicList, {
          params: { q: searchQuery },
        });
        setSchools(resp.data);
      } catch (err) {
        console.error('Erreur chargement établissements:', err);
      }
    };
    fetchSchools();
  }, [searchQuery]);

  const handleSelectSchool = (school: PublicSchool) => {
    setSelectedSchool(school);
    setStep(2);
    setErrorMsg(null);
  };

  const handleSubmitClaim = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSchool) return;

    setLoading(true);
    setErrorMsg(null);

    try {
      const resp = await apiClient.post(API_ENDPOINTS.enrollment.claim, {
        tenant_code: selectedSchool.code,
        last_name: formData.last_name,
        first_name: formData.first_name,
        matricule: formData.matricule,
        birth_date: formData.birth_date,
        birth_place: formData.birth_place,
      });

      const data = resp.data;
      setSuccessStatus(data.status);
      setStep(3);

      // Si le jeton rafraîchi est renvoyé, rafraîchir /me
      if (data.token) {
        const meResp = await apiClient.get(API_ENDPOINTS.identity.me, {
          headers: { Authorization: `Bearer ${data.token}` },
        });
        setAuthData(data.token, meResp.data);
      }
    } catch (err: any) {
      if (err.response?.status === 429) {
        setErrorMsg('Nombre maximal d\'essais atteint. Réessayez dans 30 minutes.');
      } else {
        // Message générique obligatoire (Règle 6.2)
        setErrorMsg('Informations non reconnues. Vérifie auprès de ton établissement.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        {step > 1 && step < 3 && (
          <button
            onClick={() => setStep(1)}
            className="p-2 text-gray-500 hover:text-gray-900 dark:hover:text-white rounded-lg"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
        )}
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Rejoindre mon établissement
          </h1>
          <p className="text-sm text-gray-500">
            Étape {step} sur 3 — Rattachement sécurisé
          </p>
        </div>
      </div>

      {/* Étape 1 : Choisir son école */}
      {step === 1 && (
        <div className="space-y-4">
          <div className="relative">
            <Search className="w-5 h-5 absolute left-3 top-3 text-gray-400" />
            <input
              type="text"
              placeholder="Rechercher par nom ou code (ex. ENSPD)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-amber-500 outline-none"
            />
          </div>

          <div className="space-y-3">
            {schools.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                Aucun établissement trouvé.
              </div>
            ) : (
              schools.map((school) => (
                <div
                  key={school.id}
                  onClick={() => handleSelectSchool(school)}
                  className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-amber-500 cursor-pointer transition shadow-sm"
                >
                  <div className="flex items-center gap-3">
                    <Building2 className="w-8 h-8 text-amber-500 p-1.5 bg-amber-50 dark:bg-amber-900/30 rounded-lg" />
                    <div>
                      <h3 className="font-bold text-gray-900 dark:text-white">
                        {school.name}
                      </h3>
                      <span className="text-xs font-mono bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded text-gray-600 dark:text-gray-300">
                        Code: {school.code}
                      </span>
                    </div>
                  </div>
                  <span className="text-sm text-amber-600 font-medium">Sélectionner →</span>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Étape 2 : Saisie des informations officielles */}
      {step === 2 && selectedSchool && (
        <form onSubmit={handleSubmitClaim} className="space-y-4 bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-900/40 text-xs text-amber-800 dark:text-amber-300">
            Saisis exactement tes informations telles qu'enregistrées à la scolarité de <strong>{selectedSchool.name}</strong>.
          </div>

          {errorMsg && (
            <div className="p-4 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-xl border border-red-200 dark:border-red-900/50 flex items-center gap-3 text-sm">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
              Nom officiel (famille) *
            </label>
            <input
              type="text"
              required
              value={formData.last_name}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white"
              placeholder="ex. DUPONT"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
              Prénom(s) *
            </label>
            <input
              type="text"
              required
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white"
              placeholder="ex. Jean Marc"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
              Matricule officiel *
            </label>
            <input
              type="text"
              required
              value={formData.matricule}
              onChange={(e) => setFormData({ ...formData, matricule: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white font-mono"
              placeholder="ex. 23G00123"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                Date de naissance *
              </label>
              <input
                type="date"
                required
                value={formData.birth_date}
                onChange={(e) => setFormData({ ...formData, birth_date: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                Lieu de naissance *
              </label>
              <input
                type="text"
                required
                value={formData.birth_place}
                onChange={(e) => setFormData({ ...formData, birth_place: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white"
                placeholder="ex. Douala"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-white font-bold rounded-xl transition shadow-md flex items-center justify-center gap-2"
          >
            {loading && <Loader2 className="w-5 h-5 animate-spin" />}
            Vérifier et me rattacher
          </button>
        </form>
      )}

      {/* Étape 3 : Succès */}
      {step === 3 && (
        <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl border border-gray-200 dark:border-gray-700 text-center space-y-4 shadow-lg">
          <CheckCircle2 className="w-16 h-16 text-emerald-500 mx-auto animate-bounce" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            {successStatus === 'ACTIVE' ? 'Bienvenue dans votre établissement !' : 'Demande transmise à l\'administration'}
          </h2>
          <p className="text-gray-600 dark:text-gray-300 text-sm">
            {successStatus === 'ACTIVE'
              ? 'Vos informations ont été vérifiées avec succès. Vos accès aux outils de campus (salles, annonces, délégués) sont débloqués.'
              : 'Votre demande de rattachement est en attente d\'approbation par la scolarité de votre établissement.'}
          </p>

          <button
            onClick={() => navigate('/feed')}
            className="w-full py-3 bg-amber-500 hover:bg-amber-600 text-white font-bold rounded-xl shadow-md transition"
          >
            Accéder à mon fil d'actualité
          </button>
        </div>
      )}
    </div>
  );
};
