// frontend/src/features/admin/AdminRosterScreen.tsx

import React, { useState, useEffect } from 'react';
import { Upload, Download, Search, Plus, UserCheck, AlertCircle, FileSpreadsheet, Loader2 } from 'lucide-react';
import apiClient from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';

interface RosterEntry {
  id: string;
  matricule: string;
  first_name: string;
  last_name: string;
  status: 'NOT_CLAIMED' | 'INVITED' | 'CLAIMED' | 'REVOKED';
  class_group_id?: string;
  academic_year: string;
}

export const AdminRosterScreen: React.FC = () => {
  const [entries, setEntries] = useState<RosterEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  
  // Dry run import modal
  const [showImportModal, setShowImportModal] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [dryRunResult, setDryRunResult] = useState<any | null>(null);
  const [importing, setImporting] = useState(false);
  const [importSuccessMsg, setImportSuccessMsg] = useState<string | null>(null);

  const fetchRoster = async () => {
    setLoading(true);
    try {
      const resp = await apiClient.get(API_ENDPOINTS.admin.roster);
      setEntries(resp.data.items || resp.data);
    } catch (err) {
      console.error('Erreur chargement registre:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoster();
  }, []);

  const handleDryRun = async () => {
    if (!importFile) return;
    setImporting(true);
    setDryRunResult(null);

    const formData = new FormData();
    formData.append('file', importFile);

    try {
      const resp = await apiClient.post(`${API_ENDPOINTS.admin.rosterImport}?dry_run=true`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setDryRunResult(resp.data);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Erreur lors de la simulation d\'importation.');
    } finally {
      setImporting(false);
    }
  };

  const handleConfirmImport = async () => {
    if (!importFile) return;
    setImporting(true);

    const formData = new FormData();
    formData.append('file', importFile);

    try {
      const resp = await apiClient.post(`${API_ENDPOINTS.admin.rosterImport}?dry_run=false`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setImportSuccessMsg(`Import réussi : ${resp.data.created_rows} entrées créées.`);
      setShowImportModal(false);
      setImportFile(null);
      setDryRunResult(null);
      fetchRoster();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Erreur lors de l\'importation.');
    } finally {
      setImporting(false);
    }
  };

  const filteredEntries = entries.filter(
    (e) =>
      e.matricule.toLowerCase().includes(search.toLowerCase()) ||
      e.last_name.toLowerCase().includes(search.toLowerCase()) ||
      e.first_name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Registre officiel des étudiants
          </h1>
          <p className="text-sm text-gray-500">
            Gestion du registre d'établissement et import CSV/XLSX.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowImportModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-amber-500 hover:bg-amber-600 text-white font-semibold rounded-xl shadow-sm transition"
          >
            <Upload className="w-4 h-4" /> Importer (CSV / XLSX)
          </button>
        </div>
      </div>

      {importSuccessMsg && (
        <div className="p-4 bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 rounded-xl border border-emerald-200 dark:border-emerald-900/50 flex items-center justify-between text-sm">
          <span>{importSuccessMsg}</span>
          <button onClick={() => setImportSuccessMsg(null)} className="font-bold">×</button>
        </div>
      )}

      {/* Barre de recherche */}
      <div className="relative">
        <Search className="w-5 h-5 absolute left-3 top-3 text-gray-400" />
        <input
          type="text"
          placeholder="Rechercher par matricule, nom ou prénom..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-900 dark:text-white focus:ring-2 focus:ring-amber-500 outline-none"
        />
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-gray-600 dark:text-gray-300">
            <thead className="bg-gray-50 dark:bg-gray-900 text-xs font-semibold text-gray-500 uppercase border-b border-gray-200 dark:border-gray-700">
              <tr>
                <th className="px-6 py-4">Matricule</th>
                <th className="px-6 py-4">Nom & Prénom</th>
                <th className="px-6 py-4">Année académique</th>
                <th className="px-6 py-4">Statut</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {loading ? (
                <tr>
                  <td colSpan={4} className="text-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-amber-500 mx-auto" />
                  </td>
                </tr>
              ) : filteredEntries.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-center py-8 text-gray-500">
                    Aucune entrée dans le registre.
                  </td>
                </tr>
              ) : (
                filteredEntries.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition">
                    <td className="px-6 py-4 font-mono font-bold text-gray-900 dark:text-white">
                      {item.matricule}
                    </td>
                    <td className="px-6 py-4 font-medium text-gray-900 dark:text-white">
                      {item.last_name} {item.first_name}
                    </td>
                    <td className="px-6 py-4 text-xs font-mono">
                      {item.academic_year}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`text-xs px-2.5 py-1 rounded-full font-semibold ${
                        item.status === 'CLAIMED' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300' :
                        item.status === 'INVITED' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300' :
                        'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                      }`}>
                        {item.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Import Dry-Run */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 max-w-lg w-full rounded-2xl p-6 space-y-4 shadow-xl border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-amber-500" /> Importation du registre
            </h3>

            <input
              type="file"
              accept=".csv,.xlsx"
              onChange={(e) => setImportFile(e.target.files?.[0] || null)}
              className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-amber-50 file:text-amber-700 hover:file:bg-amber-100"
            />

            {importFile && !dryRunResult && (
              <button
                onClick={handleDryRun}
                disabled={importing}
                className="w-full py-2.5 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 text-gray-800 dark:text-white font-semibold rounded-xl transition flex items-center justify-center gap-2"
              >
                {importing && <Loader2 className="w-4 h-4 animate-spin" />}
                Lancer la simulation (Dry-Run)
              </button>
            )}

            {dryRunResult && (
              <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-xl space-y-2 text-xs border border-gray-200 dark:border-gray-700">
                <div className="flex justify-between font-bold text-gray-900 dark:text-white">
                  <span>Lignes au total : {dryRunResult.total_rows}</span>
                  <span className="text-emerald-600">Valides : {dryRunResult.created_rows}</span>
                  <span className="text-red-500">Erreurs : {dryRunResult.error_rows}</span>
                </div>
                {dryRunResult.error_rows > 0 && (
                  <div className="p-2 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded text-[11px] max-h-32 overflow-y-auto">
                    {JSON.stringify(dryRunResult.errors_json, null, 2)}
                  </div>
                )}
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => {
                  setShowImportModal(false);
                  setDryRunResult(null);
                  setImportFile(null);
                }}
                className="px-4 py-2 text-gray-500 hover:text-gray-900 dark:hover:text-white font-medium"
              >
                Annuler
              </button>
              {dryRunResult && dryRunResult.created_rows > 0 && (
                <button
                  onClick={handleConfirmImport}
                  disabled={importing}
                  className="px-5 py-2 bg-amber-500 hover:bg-amber-600 text-white font-bold rounded-xl shadow-md transition flex items-center gap-2"
                >
                  {importing && <Loader2 className="w-4 h-4 animate-spin" />}
                  Valider et importer {dryRunResult.created_rows} lignes
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
