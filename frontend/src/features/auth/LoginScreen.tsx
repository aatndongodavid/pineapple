// frontend/src/features/auth/LoginScreen.tsx

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Loader2, LogIn, UserPlus, Building2 } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { apiClient, API_ENDPOINTS } from '@/lib/api';
import { useAuthStore } from '@/lib/store/authStore';
import { useTenantStore } from '@/lib/store/tenantStore';
import { cn } from '@/lib/utils';

// Liste des établissements disponibles (pour la démo)
const TENANTS = [
  { id: '11111111-1111-1111-1111-111111111111', code: 'ENSPD', name: 'ENSPD' },
  { id: '22222222-2222-2222-2222-222222222222', code: 'UDo', name: 'UDo' },
  { id: '33333333-3333-3333-3333-333333333333', code: 'ENS', name: 'ENS' },
];

export const LoginScreen: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuthStore();
  const { setTenant } = useTenantStore();

  const [tenantCode, setTenantCode] = useState(TENANTS[0].code);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    // Trouver le tenant correspondant au code sélectionné
    const tenant = TENANTS.find(t => t.code === tenantCode);
    if (!tenant) {
      setError('Établissement inconnu');
      setIsLoading(false);
      return;
    }

    try {
      // 1. Appel API pour authentifier
      const loginResponse = await apiClient.post(API_ENDPOINTS.identity.login, {
        email,
        password,
      }, {
        headers: { 'X-Tenant-ID': tenant.id }, // le header tenant nécessaire
      });

      const { access_token, user_id, tenant_id } = loginResponse.data;

      // Stocker le tenant dans le store
      setTenant(tenant.id, tenant.name);

      // 2. Récupérer le profil complet avec le statut campus
      const meResponse = await apiClient.get(API_ENDPOINTS.identity.me, {
        headers: {
          'Authorization': `Bearer ${access_token}`,
          'X-Tenant-ID': tenant.id,
        },
      });

      const userData = meResponse.data;

      // 3. Mettre à jour le store d'authentification
      login(access_token, {
        id: userData.id,
        email: userData.email,
        firstName: userData.first_name,
        lastName: userData.last_name,
        matricule: userData.matricule,
      }, userData.campus_status_display);

      // Redirection vers la page d'accueil
      navigate('/');
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('Identifiants invalides');
      } else if (err.response?.status === 400 && err.response?.data?.detail?.includes('X-Tenant-ID')) {
        setError('Tenant manquant ou invalide');
      } else {
        setError('Une erreur est survenue. Veuillez réessayer.');
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
        className="w-full max-w-md"
      >
        <Card variant="neo-extruded" className="p-8">
          <div className="flex flex-col items-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-pineapple flex items-center justify-center mb-4 shadow-neo-extruded dark:shadow-neo-dark-extruded">
              <Building2 className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-800 dark:text-white">
              Connexion
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Connecter. Collaborer. Grandir.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Sélecteur d'établissement */}
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

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Email
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="vous@exemple.cm"
                className="w-full px-4 py-3 rounded-xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
              />
            </div>

            {/* Mot de passe */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Mot de passe
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-3 rounded-xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
              />
            </div>

            {error && (
              <div className="p-3 rounded-lg bg-red-100 text-red-700 text-sm">
                {error}
              </div>
            )}

            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-full"
              isLoading={isLoading}
              icon={LogIn}
            >
              Se connecter
            </Button>

            <div className="text-center text-sm text-gray-500 dark:text-gray-400">
              Pas encore de compte ?{' '}
              <Link
                to="/register"
                className="text-pineapple hover:underline font-medium"
              >
                Créer un compte
              </Link>
            </div>
          </form>
        </Card>
      </motion.div>
    </div>
  );
};