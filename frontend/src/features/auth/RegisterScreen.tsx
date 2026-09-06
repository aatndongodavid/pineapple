// frontend/src/features/auth/RegisterScreen.tsx

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Loader2, ChevronLeft, ChevronRight, Check } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { apiClient, API_ENDPOINTS } from '@/lib/api';
import { useTenantStore } from '@/lib/store/tenantStore';
import { cn } from '@/lib/utils';

// Liste des établissements disponibles (cohérente avec LoginScreen)
const TENANTS = [
  { id: '11111111-1111-1111-1111-111111111111', code: 'ENSPD', name: 'ENSPD' },
  { id: '22222222-2222-2222-2222-222222222222', code: 'UDo', name: 'UDo' },
  { id: '33333333-3333-3333-3333-333333333333', code: 'ENS', name: 'ENS' },
];

const FACULTIES = [
  'Génie Logiciel',
  'Génie Électrique',
  'Génie Mécanique',
  'Sciences Économiques',
  'Médecine',
];

const FILIERES: Record<string, string[]> = {
  'Génie Logiciel': ['Informatique', 'Réseaux', 'Data Science'],
  'Génie Électrique': ['Électrotechnique', 'Automatique'],
  'Génie Mécanique': ['Construction', 'Énergétique'],
  'Sciences Économiques': ['Finance', 'Management'],
  'Médecine': ['Médecine Générale'],
};

const ACADEMIC_YEARS = ['2026-2027', '2025-2026', '2024-2025'];

type FormData = {
  email: string;
  password: string;
  confirmPassword: string;
  firstName: string;
  lastName: string;
  matricule: string;
  faculty: string;
  filiere: string;
  academicYear: string;
};

const initialFormData: FormData = {
  email: '',
  password: '',
  confirmPassword: '',
  firstName: '',
  lastName: '',
  matricule: '',
  faculty: FACULTIES[0],
  filiere: FILIERES[FACULTIES[0]][0],
  academicYear: ACADEMIC_YEARS[0],
};

const StepIndicator: React.FC<{ currentStep: number }> = ({ currentStep }) => {
  const steps = ['Compte', 'Identité', 'Académique'];
  return (
    <div className="flex items-center justify-center mb-8">
      {steps.map((step, index) => (
        <React.Fragment key={step}>
          {index > 0 && (
            <div className={cn('h-1 w-10 mx-2 rounded', index <= currentStep ? 'bg-pineapple' : 'bg-gray-300')} />
          )}
          <div className="flex flex-col items-center">
            <div
              className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
                index < currentStep
                  ? 'bg-pineapple text-white'
                  : index === currentStep
                    ? 'bg-pineapple/20 text-pineapple border-2 border-pineapple'
                    : 'bg-gray-200 text-gray-500'
              )}
            >
              {index < currentStep ? <Check className="w-4 h-4" /> : index + 1}
            </div>
            <span className="text-xs mt-1 text-gray-500">{step}</span>
          </div>
        </React.Fragment>
      ))}
    </div>
  );
};

export const RegisterScreen: React.FC = () => {
  const navigate = useNavigate();
  const { tenantId } = useTenantStore();

  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tenantCode, setTenantCode] = useState(TENANTS[0].code);

  const updateField = (field: keyof FormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleNext = () => {
    // Validation spécifique à chaque étape
    if (currentStep === 0) {
      if (!formData.email || !formData.password || !formData.confirmPassword) {
        setError('Veuillez remplir tous les champs.');
        return;
      }
      if (formData.password !== formData.confirmPassword) {
        setError('Les mots de passe ne correspondent pas.');
        return;
      }
      if (formData.password.length < 8) {
        setError('Le mot de passe doit contenir au moins 8 caractères.');
        return;
      }
    } else if (currentStep === 1) {
      if (!formData.firstName || !formData.lastName || !formData.matricule) {
        setError('Veuillez remplir tous les champs.');
        return;
      }
    }
    setError(null);
    setCurrentStep(prev => Math.min(prev + 1, 2));
  };

  const handlePrevious = () => {
    setError(null);
    setCurrentStep(prev => Math.max(prev - 1, 0));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    // Vérifier qu'un tenant est sélectionné (sinon utiliser le tenant par défaut)
    const tenant = TENANTS.find(t => t.code === tenantCode) || TENANTS[0];

    try {
      await apiClient.post(
        API_ENDPOINTS.identity.register,
        {
          email: formData.email,
          password: formData.password,
          first_name: formData.firstName,
          last_name: formData.lastName,
          matricule: formData.matricule,
          faculty: formData.faculty,
          filiere: formData.filiere,
          academic_year: formData.academicYear,
        },
        {
          headers: { 'X-Tenant-ID': tenant.id },
        }
      );
      // Inscription réussie : redirection vers la connexion
      navigate('/login');
    } catch (err: any) {
      if (err.response?.status === 409) {
        setError('Email ou matricule déjà utilisé.');
      } else {
        setError('Erreur lors de l\'inscription. Veuillez réessayer.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background-light dark:bg-background-dark">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="w-full max-w-lg"
      >
        <Card variant="neo-extruded" className="p-8">
          <div className="flex flex-col items-center mb-6">
            <div className="w-16 h-16 rounded-2xl bg-pineapple flex items-center justify-center mb-4 shadow-neo-extruded dark:shadow-neo-dark-extruded">
              <span className="text-white text-2xl font-bold">P</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-800 dark:text-white">
              Créer un compte
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Rejoignez votre campus numérique
            </p>
          </div>

          <StepIndicator currentStep={currentStep} />

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Établissement (affiché en permanence) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Établissement
              </label>
              <select
                value={tenantCode}
                onChange={(e) => setTenantCode(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
              >
                {TENANTS.map((t) => (
                  <option key={t.id} value={t.code}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>

            {currentStep === 0 && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => updateField('email', e.target.value)}
                    placeholder="vous@exemple.cm"
                    className="w-full px-4 py-3 rounded-xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Mot de passe
                  </label>
                  <input
                    type="password"
                    required
                    value={formData.password}
                    onChange={(e) => updateField('password', e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-4 py-3 rounded-xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Confirmer le mot de passe
                  </label>
                  <input
                    type="password"
                    required
                    value={formData.confirmPassword}
                    onChange={(e) => updateField('confirmPassword', e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-4 py-3 rounded-xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
                  />
                </div>
              </>
            )}

            {currentStep === 1 && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Prénom
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.firstName}
                    onChange={(e) => updateField('firstName', e.target.value)}
                    placeholder="Votre prénom"
                    className="w-full px-4 py-3 rounded-xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Nom
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.lastName}
                    onChange={(e) => updateField('lastName', e.target.value)}
                    placeholder="Votre nom"
                    className="w-full px-4 py-3 rounded-xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Matricule
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.matricule}
                    onChange={(e) => updateField('matricule', e.target.value)}
                    placeholder="ENSPD2026001"
                    className="w-full px-4 py-3 rounded-xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
                  />
                </div>
              </>
            )}

            {currentStep === 2 && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Faculté
                  </label>
                  <select
                    value={formData.faculty}
                    onChange={(e) => {
                      const faculty = e.target.value;
                      const filieres = FILIERES[faculty] || [];
                      updateField('faculty', faculty);
                      updateField('filiere', filieres[0] || '');
                    }}
                    className="w-full px-4 py-3 rounded-xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
                  >
                    {FACULTIES.map((f) => (
                      <option key={f} value={f}>
                        {f}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Filière
                  </label>
                  <select
                    value={formData.filiere}
                    onChange={(e) => updateField('filiere', e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
                  >
                    {(FILIERES[formData.faculty] || []).map((f) => (
                      <option key={f} value={f}>
                        {f}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Année académique
                  </label>
                  <select
                    value={formData.academicYear}
                    onChange={(e) => updateField('academicYear', e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
                  >
                    {ACADEMIC_YEARS.map((y) => (
                      <option key={y} value={y}>
                        {y}
                      </option>
                    ))}
                  </select>
                </div>
              </>
            )}

            {error && (
              <div className="p-3 rounded-lg bg-red-100 text-red-700 text-sm">
                {error}
              </div>
            )}

            <div className="flex gap-3">
              {currentStep > 0 && (
                <Button
                  type="button"
                  variant="secondary"
                  onClick={handlePrevious}
                  className="flex-1"
                  icon={ChevronLeft}
                >
                  Retour
                </Button>
              )}
              {currentStep < 2 ? (
                <Button
                  type="button"
                  variant="primary"
                  onClick={handleNext}
                  className="flex-1"
                  icon={ChevronRight}
                >
                  Suivant
                </Button>
              ) : (
                <Button
                  type="submit"
                  variant="primary"
                  className="flex-1"
                  isLoading={isLoading}
                  icon={Check}
                >
                  S'inscrire
                </Button>
              )}
            </div>

            <div className="text-center text-sm text-gray-500 dark:text-gray-400">
              Déjà un compte ?{' '}
              <Link to="/login" className="text-pineapple hover:underline font-medium">
                Se connecter
              </Link>
            </div>
          </form>
        </Card>
      </motion.div>
    </div>
  );
};