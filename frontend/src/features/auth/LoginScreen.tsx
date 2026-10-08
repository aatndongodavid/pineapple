// frontend/src/features/auth/LoginScreen.tsx

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Loader2, LogIn, UserPlus, Building2, CheckCircle2 } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { apiClient, API_ENDPOINTS } from '@/lib/api';
import { useAuthStore } from '@/lib/store/authStore';
import { useTenantStore } from '@/lib/store/tenantStore';

interface SchoolItem {
  id: string;
  name: string;
  code: string;
}

const DEFAULT_DEMO_ACCOUNTS = [
  { label: 'Admin Établissement', email: 'admin@enspd.cm', pass: 'AdminENSPD2026!', role: 'ENSPD' },
  { label: 'Étudiant', email: 'student@enspd.cm', pass: 'Student2026!', role: 'ENSPD' },
  { label: 'Délégué Titulaire', email: 'delegate@enspd.cm', pass: 'Delegate2026!', role: 'ENSPD' },
  { label: 'Visiteur Public', email: 'visitor@pineapple.cm', pass: 'Visitor2026!', role: 'Visiteur' },
  { label: 'Super Admin', email: 'superadmin@pineapple.cm', pass: 'SuperAdmin2026!', role: 'Plateforme' },
];

export const LoginScreen: React.FC = () => {
  const navigate = useNavigate();
  const { setAuthData } = useAuthStore();
  const { setTenant } = useTenantStore();

  const [schools, setSchools] = useState<SchoolItem[]>([]);
  const [selectedSchoolId, setSelectedSchoolId] = useState<string>('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Charger la liste des écoles réelles depuis le backend
  useEffect(() => {
    let isMounted = true;
    apiClient
      .get(API_ENDPOINTS.schools.publicList)
      .then((res) => {
        if (isMounted && res.data && res.data.length > 0) {
          setSchools(res.data);
          setSelectedSchoolId(res.data[0].id);
        }
      })
      .catch(() => {
        // Fallback si serveur non démarré
        if (isMounted) {
          const fallback = [
            { id: '00000000-0000-0000-0000-000000000000', code: 'ENSPD', name: 'Établissement Démo Pineapple' },
          ];
          setSchools(fallback);
          setSelectedSchoolId(fallback[0].id);
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const fillDemoAccount = (acc: typeof DEFAULT_DEMO_ACCOUNTS[0]) => {
    setEmail(acc.email);
    setPassword(acc.pass);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    const activeSchool = schools.find((s) => s.id === selectedSchoolId);

    try {
      // 1. Authentification
      const loginHeaders: Record<string, string> = {};
      if (selectedSchoolId) {
        loginHeaders['X-Tenant-ID'] = selectedSchoolId;
      }

      const loginResponse = await apiClient.post(
        API_ENDPOINTS.identity.login,
        { email, password },
        { headers: loginHeaders }
      );

      const { access_token, tenant_id } = loginResponse.data;

      // 2. Récupérer le profil me
      const meHeaders: Record<string, string> = {
        Authorization: `Bearer ${access_token}`,
      };
      const finalTenantId = tenant_id || selectedSchoolId;
      if (finalTenantId) {
        meHeaders['X-Tenant-ID'] = finalTenantId;
      }

      const meResponse = await apiClient.get(API_ENDPOINTS.identity.me, {
        headers: meHeaders,
      });

      // Stocker le tenant dans le store
      if (activeSchool) {
        setTenant(activeSchool.id, activeSchool.name);
      } else if (meResponse.data.tenant) {
        setTenant(meResponse.data.tenant.id, meResponse.data.tenant.name);
      }

      // 3. Mettre à jour le store d'authentification
      setAuthData(access_token, meResponse.data);

      // Redirection vers la page d'accueil
      navigate('/');
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('Identifiants invalides. Vérifiez votre e-mail et mot de passe.');
      } else if (err.response?.status === 403) {
        setError('Établissement non correspondant (TENANT_MISMATCH). Choisissez le bon établissement.');
      } else {
        setError('Une erreur est survenue lors de la connexion. Vérifiez que le backend est actif.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-slate-950 text-slate-100 font-sans">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="w-full max-w-lg space-y-6"
      >
        {/* Card de connexion */}
        <Card variant="neo-extruded" className="p-8 bg-slate-900 border border-slate-800 shadow-2xl rounded-2xl">
          <div className="flex flex-col items-center mb-6">
            <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center mb-4 shadow-lg">
              <span className="text-3xl">🍍</span>
            </div>
            <h1 className="text-2xl font-black text-white">Connexion Pineapple OS</h1>
            <p className="text-xs text-slate-400 mt-1">Le système d'exploitation numérique des campus</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Sélecteur d'établissement */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-1.5">
                Établissement Rattaché
              </label>
              <select
                value={selectedSchoolId}
                onChange={(e) => setSelectedSchoolId(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs font-semibold focus:outline-none focus:border-amber-500 transition-colors"
              >
                {schools.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.code})
                  </option>
                ))}
              </select>
            </div>

            {/* Email */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-1.5">
                Adresse E-mail
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="ex: admin@enspd.cm"
                className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs font-semibold focus:outline-none focus:border-amber-500 transition-colors"
              />
            </div>

            {/* Mot de passe */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-1.5">
                Mot de passe
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs font-semibold focus:outline-none focus:border-amber-500 transition-colors"
              />
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-semibold">
                {error}
              </div>
            )}

            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-full bg-amber-500 hover:bg-amber-600 text-slate-950 font-black text-sm py-3 rounded-xl transition-colors shadow-md"
              isLoading={isLoading}
              icon={LogIn}
            >
              Se Connecter
            </Button>
          </form>

          {/* Helper : Comptes Démo du Seed */}
          <div className="mt-8 pt-6 border-t border-slate-800 space-y-3">
            <span className="block text-[11px] font-extrabold uppercase tracking-wider text-amber-400">
              ⚡ Comptes de Démo Pré-Chargés (Seed)
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {DEFAULT_DEMO_ACCOUNTS.map((acc, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => fillDemoAccount(acc)}
                  className="p-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-left transition-colors text-xs group"
                >
                  <div className="flex items-center justify-between text-white font-bold mb-0.5">
                    <span>{acc.label}</span>
                    <span className="text-[10px] text-amber-400 font-semibold">{acc.role}</span>
                  </div>
                  <span className="block text-[11px] text-slate-400 truncate">{acc.email}</span>
                </button>
              ))}
            </div>
          </div>
        </Card>
      </motion.div>
    </div>
  );
};