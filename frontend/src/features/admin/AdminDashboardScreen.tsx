// frontend/src/features/admin/AdminDashboardScreen.tsx

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Users,
  UserCheck,
  Clock,
  Flag,
  ShieldCheck,
  Activity,
  TrendingUp,
  Award,
  Upload,
  FileSpreadsheet,
  Download,
  AlertTriangle,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { useTranslation } from 'react-i18next';
import apiClient from '@/lib/api/client';
import { useAuthStore } from '@/lib/store/authStore';
import { useTenantStore } from '@/lib/store/tenantStore';

interface Stats {
  certifiedStudents: number;
  pendingCertifications: number;
  unresolvedReports: number;
  licenseTier: 'BASIC' | 'STANDARD' | 'ENTERPRISE';
}

const mockStats: Stats = {
  certifiedStudents: 1890,
  pendingCertifications: 212,
  unresolvedReports: 7,
  licenseTier: 'STANDARD',
};

const licenseLabels: Record<Stats['licenseTier'], string> = {
  BASIC: 'Basic',
  STANDARD: 'Standard',
  ENTERPRISE: 'Enterprise',
};

interface ImportDetail {
  line: number;
  email: string;
  status: 'SUCCESS' | 'ERROR';
  reason?: string;
  temp_password?: string;
}

interface ImportReport {
  filename: string;
  total_lines: number;
  succeeded_count: number;
  failed_count: number;
  details: ImportDetail[];
}

export const AdminDashboardScreen: React.FC = () => {
  const { t } = useTranslation();
  const { token } = useAuthStore();
  const { tenantId } = useTenantStore();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [importReport, setImportReport] = useState<ImportReport | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [isExporting, setIsExporting] = useState(false);
  const [exportMessage, setExportMessage] = useState<string | null>(null);

  const participationRate = 64;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setUploadError(null);
    }
  };

  const handleBulkImport = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setUploadError(null);
    setImportReport(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await apiClient.post('/identity/admin/users/bulk-import', formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
          'Content-Type': 'multipart/form-data',
        },
      });
      setImportReport(response.data);
    } catch (err: any) {
      setUploadError(
        err.response?.data?.detail || 'Erreur lors de l\'importation en masse du fichier CSV.'
      );
    } finally {
      setIsUploading(false);
    }
  };

  const handleTenantExport = async () => {
    setIsExporting(true);
    setExportMessage(null);
    try {
      const response = await apiClient.post('/identity/admin/tenant/export', {}, {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
        },
      });
      setExportMessage(response.data.message || 'Export initié avec succès !');
    } catch (err: any) {
      setExportMessage(err.response?.data?.detail || 'Erreur lors de la génération de l\'export.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* En-tête */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Dashboard Administration</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Vue d'ensemble de l'établissement & outils de gestion des données
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="info" className="text-sm">
            <ShieldCheck className="h-4 w-4 mr-1" />
            {licenseLabels[mockStats.licenseTier]} License
          </Badge>
          <Button
            variant="neo"
            size="sm"
            onClick={handleTenantExport}
            disabled={isExporting}
            className="flex items-center gap-2"
          >
            <Download className="h-4 w-4 text-primary" />
            {isExporting ? 'Export en cours...' : 'Exporter Données Tenant'}
          </Button>
        </div>
      </motion.div>

      {exportMessage && (
        <Card variant="outline" className="p-4 bg-emerald-50 dark:bg-emerald-950/20 border-emerald-500">
          <p className="text-sm text-emerald-700 dark:text-emerald-300 font-medium">
            {exportMessage}
          </p>
        </Card>
      )}

      {/* Cartes de statistiques */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card variant="default" className="p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-blue-900/10 flex items-center justify-center">
              <UserCheck className="h-6 w-6 text-blue-900 dark:text-blue-300" />
            </div>
            <div>
              <span className="text-sm text-gray-500">Certification</span>
              <p className="text-xl font-bold text-gray-800 dark:text-white">
                {mockStats.certifiedStudents}{' '}
                <span className="text-sm font-normal text-gray-500">certifiés</span>
              </p>
            </div>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500 flex items-center gap-1">
              <Clock className="h-4 w-4 text-amber-500" />
              {mockStats.pendingCertifications} en attente
            </span>
            <span className="text-emerald-600 font-medium">
              {((mockStats.certifiedStudents / (mockStats.certifiedStudents + mockStats.pendingCertifications)) * 100).toFixed(1)}%
            </span>
          </div>
        </Card>

        <Card variant="default" className="p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
              <Flag className="h-6 w-6 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <span className="text-sm text-gray-500">Modération</span>
              <p className="text-xl font-bold text-gray-800 dark:text-white">
                {mockStats.unresolvedReports}{' '}
                <span className="text-sm font-normal text-gray-500">signalements ouverts</span>
              </p>
            </div>
          </div>
          <div className="mt-2">
            <div className="h-2 bg-gray-200 dark:bg-slate-700 rounded-full">
              <div
                className="h-full bg-red-500 rounded-full"
                style={{ width: `${Math.min(mockStats.unresolvedReports * 10, 100)}%` }}
              />
            </div>
          </div>
        </Card>

        <Card variant="default" className="p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-900/20 flex items-center justify-center">
              <Award className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <span className="text-sm text-gray-500">Licence Campus</span>
              <p className="text-xl font-bold text-gray-800 dark:text-white">
                {licenseLabels[mockStats.licenseTier]}
              </p>
            </div>
          </div>
          <div className="text-sm text-gray-500">
            Jusqu'à 5 000 étudiants certifiés
          </div>
        </Card>
      </div>

      {/* SECTION PARTIE O : Importation en Masse (CSV Onboarding) */}
      <Card variant="default" className="p-6 space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
            <FileSpreadsheet className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
              {t('bulkImport.title')}
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {t('bulkImport.subtitle')}
            </p>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-background-light dark:bg-slate-900 border border-dashed border-gray-300 dark:border-slate-700 flex flex-col items-center justify-center gap-3 text-center">
          <Upload className="h-8 w-8 text-primary animate-bounce" />
          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-200">
              {selectedFile ? selectedFile.name : t('bulkImport.dragDropText')}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              Colonnes requises : email, first_name, last_name, matricule (facultatif : faculty, filiere, academic_year)
            </p>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="file"
              accept=".csv"
              id="csv-file-input"
              className="hidden"
              onChange={handleFileChange}
            />
            <label
              htmlFor="csv-file-input"
              className="px-4 py-2 text-sm font-medium rounded-xl bg-gray-200 dark:bg-slate-800 text-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-slate-700 cursor-pointer transition-colors"
            >
              Parcourir...
            </label>
            <Button
              variant="primary"
              size="sm"
              onClick={handleBulkImport}
              disabled={!selectedFile || isUploading}
            >
              {isUploading ? t('bulkImport.processing') : t('bulkImport.uploadButton')}
            </Button>
          </div>
        </div>

        {uploadError && (
          <div className="p-3 rounded-xl bg-red-50 dark:bg-red-950/20 text-red-600 dark:text-red-400 text-sm flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 flex-shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}

        {importReport && (
          <div className="mt-4 p-4 rounded-2xl bg-slate-950 text-white space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-emerald-400 flex items-center gap-2">
                <CheckCircle className="h-5 w-5" />
                {t('bulkImport.reportTitle')} - {importReport.filename}
              </h3>
              <span className="text-xs text-slate-400">
                {importReport.succeeded_count} / {importReport.total_lines} réussis
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div className="p-2 rounded-lg bg-slate-900">
                <p className="text-slate-400">{t('bulkImport.processedCount')}</p>
                <p className="text-base font-bold text-white">{importReport.total_lines}</p>
              </div>
              <div className="p-2 rounded-lg bg-emerald-950/40">
                <p className="text-emerald-400">{t('bulkImport.successCount')}</p>
                <p className="text-base font-bold text-emerald-300">{importReport.succeeded_count}</p>
              </div>
              <div className="p-2 rounded-lg bg-red-950/40">
                <p className="text-red-400">{t('bulkImport.errorCount')}</p>
                <p className="text-base font-bold text-red-300">{importReport.failed_count}</p>
              </div>
            </div>

            <p className="text-xs text-slate-400 italic">
              {t('bulkImport.tempPasswordNotice')}
            </p>

            <div className="max-h-60 overflow-y-auto space-y-1 text-xs font-mono">
              {importReport.details.map((detail, idx) => (
                <div
                  key={idx}
                  className={`p-2 rounded flex items-center justify-between ${
                    detail.status === 'SUCCESS' ? 'bg-slate-900 text-slate-200' : 'bg-red-950/40 text-red-300'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    {detail.status === 'SUCCESS' ? (
                      <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
                    ) : (
                      <XCircle className="h-3.5 w-3.5 text-red-400" />
                    )}
                    Ligne {detail.line} : {detail.email}
                  </span>
                  {detail.status === 'SUCCESS' ? (
                    <span className="text-emerald-400">Pass: {detail.temp_password}</span>
                  ) : (
                    <span className="text-red-400">{detail.reason}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>

      {/* Graphique d'activité */}
      <Card variant="outline" className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-white flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            Activité du réseau
          </h2>
          <span className="text-sm text-gray-500 flex items-center gap-1">
            <TrendingUp className="h-4 w-4" />
            +12% cette semaine
          </span>
        </div>
        <div className="h-40 bg-background-light dark:bg-slate-800 rounded-xl flex items-end justify-around p-4">
          {[35, 52, 41, 68, 55, 74, 63].map((height, index) => (
            <div key={index} className="flex flex-col items-center gap-1">
              <div
                className="w-8 bg-gradient-to-t from-blue-900 to-blue-500 dark:from-blue-700 dark:to-blue-300 rounded-t"
                style={{ height: `${height}px` }}
              />
              <span className="text-xs text-gray-500">{['L', 'M', 'M', 'J', 'V', 'S', 'D'][index]}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};