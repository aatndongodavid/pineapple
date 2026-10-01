import React, { useState, useEffect } from 'react';
import { Building2, Users, Vote, ShoppingBag, Plus, RefreshCw, ShieldAlert, CheckCircle2 } from 'lucide-react';
import client from '@/lib/api/client';

interface Tenant {
  id: string;
  name: string;
  code: string;
  domain?: string;
  is_active: boolean;
  created_at: string;
  user_count: number;
  election_count: number;
}

interface PlatformMetrics {
  total_tenants: number;
  total_users: number;
  total_elections: number;
  total_listings: number;
}

export const SuperAdminDashboardScreen: React.FC = () => {
  const [platformToken, setPlatformToken] = useState<string | null>(
    localStorage.getItem('pineapple_platform_token')
  );
  const [email, setEmail] = useState('admin@gemula.cm');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [metrics, setMetrics] = useState<PlatformMetrics | null>(null);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Formulaire création
  const [newName, setNewName] = useState('');
  const [newCode, setNewCode] = useState('');
  const [newDomain, setNewDomain] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await client.post('/api/v1/platform/login', { email, password });
      const token = res.data.access_token;
      setPlatformToken(token);
      localStorage.setItem('pineapple_platform_token', token);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Échec de la connexion Super Admin');
    } finally {
      setLoading(false);
    }
  };

  const fetchDashboardData = async () => {
    if (!platformToken) return;
    setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${platformToken}` };
      const [metricsRes, tenantsRes] = await Promise.all([
        client.get('/api/v1/platform/metrics', { headers }),
        client.get('/api/v1/platform/tenants', { headers }),
      ]);
      setMetrics(metricsRes.data);
      setTenants(tenantsRes.data);
    } catch (err: any) {
      if (err.response?.status === 401 || err.response?.status === 403) {
        setPlatformToken(null);
        localStorage.removeItem('pineapple_platform_token');
      }
      setError('Erreur lors du chargement des données de la plateforme');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (platformToken) {
      fetchDashboardData();
    }
  }, [platformToken]);

  const handleCreateTenant = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName || !newCode) return;
    setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${platformToken}` };
      await client.post(
        '/api/v1/platform/tenants',
        { name: newName, code: newCode, domain: newDomain || null },
        { headers }
      );
      setShowCreateModal(false);
      setNewName('');
      setNewCode('');
      setNewDomain('');
      fetchDashboardData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Échec de création de l'établissement");
    } finally {
      setLoading(false);
    }
  };

  if (!platformToken) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white p-4">
        <div className="bg-gray-800 p-8 rounded-2xl shadow-2xl max-w-md w-full border border-gray-700">
          <div className="flex items-center space-x-3 mb-6">
            <ShieldAlert className="h-8 w-8 text-amber-400" />
            <div>
              <h1 className="text-xl font-bold">Espace Super Admin (Gemula)</h1>
              <p className="text-xs text-gray-400">Gestion transverse multi-établissements</p>
            </div>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-900/50 border border-red-500 rounded-lg text-sm text-red-200">
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1">Email Super Admin</label>
              <input
                type="email"
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-amber-500"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1">Mot de passe</label>
              <input
                type="password"
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-amber-500"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Mot de passe Super Admin"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-amber-500 hover:bg-amber-600 text-black font-semibold py-2 rounded-lg transition"
            >
              {loading ? 'Authentification...' : 'Se connecter'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-8 border-b border-gray-800 pb-4">
        <div className="flex items-center space-x-3">
          <Building2 className="h-8 w-8 text-amber-400" />
          <div>
            <h1 className="text-2xl font-bold text-white">Super Admin Global Dashboard</h1>
            <p className="text-sm text-gray-400">Vue d'ensemble et contrôle de la plateforme Pineapple</p>
          </div>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={fetchDashboardData}
            className="flex items-center space-x-1 px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm text-gray-300 transition"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Actualiser</span>
          </button>
          <button
            onClick={() => {
              setPlatformToken(null);
              localStorage.removeItem('pineapple_platform_token');
            }}
            className="px-3 py-2 bg-red-900/50 hover:bg-red-800 text-red-200 rounded-lg text-sm transition"
          >
            Déconnexion
          </button>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-gray-900 p-5 rounded-xl border border-gray-800 flex items-center space-x-4">
          <div className="p-3 bg-amber-500/10 text-amber-400 rounded-lg">
            <Building2 className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs text-gray-400 font-medium">Établissements</p>
            <p className="text-2xl font-bold text-white">{metrics?.total_tenants ?? 0}</p>
          </div>
        </div>

        <div className="bg-gray-900 p-5 rounded-xl border border-gray-800 flex items-center space-x-4">
          <div className="p-3 bg-blue-500/10 text-blue-400 rounded-lg">
            <Users className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs text-gray-400 font-medium">Utilisateurs Globaux</p>
            <p className="text-2xl font-bold text-white">{metrics?.total_users ?? 0}</p>
          </div>
        </div>

        <div className="bg-gray-900 p-5 rounded-xl border border-gray-800 flex items-center space-x-4">
          <div className="p-3 bg-purple-500/10 text-purple-400 rounded-lg">
            <Vote className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs text-gray-400 font-medium">Élections Campus</p>
            <p className="text-2xl font-bold text-white">{metrics?.total_elections ?? 0}</p>
          </div>
        </div>

        <div className="bg-gray-900 p-5 rounded-xl border border-gray-800 flex items-center space-x-4">
          <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-lg">
            <ShoppingBag className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs text-gray-400 font-medium">Annonces Marketplace</p>
            <p className="text-2xl font-bold text-white">{metrics?.total_listings ?? 0}</p>
          </div>
        </div>
      </div>

      {/* Tenants Table & Header */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-semibold text-white">Établissements / Tenants Réseau</h2>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center space-x-2 bg-amber-500 hover:bg-amber-600 text-black px-4 py-2 rounded-lg text-sm font-semibold transition"
          >
            <Plus className="h-4 w-4" />
            <span>Nouveau Tenant</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-gray-300">
            <thead className="bg-gray-800/50 text-gray-400 text-xs uppercase font-semibold">
              <tr>
                <th className="py-3 px-4">Nom de l'établissement</th>
                <th className="py-3 px-4">Code Tenant</th>
                <th className="py-3 px-4">Domaine</th>
                <th className="py-3 px-4">Utilisateurs</th>
                <th className="py-3 px-4">Élections</th>
                <th className="py-3 px-4">Statut</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {tenants.map((t) => (
                <tr key={t.id} className="hover:bg-gray-800/30 transition">
                  <td className="py-3 px-4 font-medium text-white">{t.name}</td>
                  <td className="py-3 px-4 font-mono text-amber-400">{t.code}</td>
                  <td className="py-3 px-4 text-gray-400">{t.domain || '-'}</td>
                  <td className="py-3 px-4">{t.user_count}</td>
                  <td className="py-3 px-4">{t.election_count}</td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center space-x-1 text-emerald-400 text-xs">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      <span>Actif</span>
                    </span>
                  </td>
                </tr>
              ))}
              {tenants.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-center py-6 text-gray-500">
                    Aucun établissement trouvé. Créez-en un pour commencer.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Création Tenant */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-900 border border-gray-800 p-6 rounded-xl max-w-md w-full shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-4">Provisionner un nouvel établissement</h3>
            <form onSubmit={handleCreateTenant} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1">Nom (ex: ENSPD Douala)</label>
                <input
                  type="text"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-amber-500"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="École Nationale Supérieure..."
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1">Code unique (ex: ENSPD)</label>
                <input
                  type="text"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-amber-500"
                  value={newCode}
                  onChange={(e) => setNewCode(e.target.value.toUpperCase())}
                  placeholder="ENSPD"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1">Domaine web (optionnel)</label>
                <input
                  type="text"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-amber-500"
                  value={newDomain}
                  onChange={(e) => setNewDomain(e.target.value)}
                  placeholder="enspd.cm"
                />
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-gray-800 text-gray-300 hover:bg-gray-700 rounded-lg text-sm font-medium transition"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-amber-500 text-black hover:bg-amber-600 rounded-lg text-sm font-semibold transition"
                >
                  {loading ? 'Création...' : 'Créer Établissement'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
