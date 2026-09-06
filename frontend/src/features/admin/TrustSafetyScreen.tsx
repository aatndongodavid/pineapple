// frontend/src/features/admin/TrustSafetyScreen.tsx

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Flag,
  Eye,
  ShieldAlert,
  CheckCircle,
  XCircle,
  Ban,
  AlertTriangle,
  MessageSquare,
  User,
  FileText,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';

// Types
type ReportStatus = 'PENDING' | 'INVESTIGATING' | 'RESOLVED' | 'DISMISSED';
type ReportReason = 'SPAM' | 'HARASSMENT' | 'HATE_SPEECH' | 'FRAUD' | 'ELECTION_VIOLATION';
type TargetType = 'POST' | 'COMMENT' | 'USER';

interface Report {
  id: string;
  targetType: TargetType;
  reason: ReportReason;
  reporterName: string;
  status: ReportStatus;
  content: string; // contenu signalé (simulé)
  targetName: string; // nom de l'utilisateur ou titre du post
}

const mockReports: Report[] = [
  {
    id: 'r1',
    targetType: 'POST',
    reason: 'HARASSMENT',
    reporterName: 'Alice N.',
    status: 'PENDING',
    content: 'Ce post contient des insultes envers un autre étudiant.',
    targetName: 'Post de Bob K.',
  },
  {
    id: 'r2',
    targetType: 'COMMENT',
    reason: 'SPAM',
    reporterName: 'Charlie M.',
    status: 'PENDING',
    content: 'Commentaire publicitaire non sollicité.',
    targetName: 'Commentaire sur la publication "Atelier Robotique"',
  },
  {
    id: 'r3',
    targetType: 'USER',
    reason: 'FRAUD',
    reporterName: 'Diane E.',
    status: 'INVESTIGATING',
    content: 'Utilisateur suspecté de vendre de faux documents.',
    targetName: 'Profil de Franck N.',
  },
];

const reasonLabels: Record<ReportReason, string> = {
  SPAM: 'Spam',
  HARASSMENT: 'Harcèlement',
  HATE_SPEECH: 'Discours haineux',
  FRAUD: 'Fraude',
  ELECTION_VIOLATION: 'Violation électorale',
};

const targetTypeIcons: Record<TargetType, React.ElementType> = {
  POST: FileText,
  COMMENT: MessageSquare,
  USER: User,
};

const statusLabels: Record<ReportStatus, string> = {
  PENDING: 'En attente',
  INVESTIGATING: 'En cours',
  RESOLVED: 'Résolu',
  DISMISSED: 'Classé sans suite',
};

export const TrustSafetyScreen: React.FC = () => {
  const [reports, setReports] = useState<Report[]>(mockReports);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);

  const handleOpenReport = (report: Report) => {
    setSelectedReport(report);
  };

  const handleCloseModal = () => {
    setSelectedReport(null);
  };

  const handleAction = (action: 'HIDE_CONTENT' | 'WARN_USER' | 'BAN_USER' | 'DISMISS') => {
    if (!selectedReport) return;
    const updatedStatus: ReportStatus = action === 'DISMISS' ? 'DISMISSED' : 'RESOLVED';
    setReports((prev) =>
      prev.map((r) => (r.id === selectedReport.id ? { ...r, status: updatedStatus } : r))
    );
    setSelectedReport(null);
    // En production, on enverrait une requête API avec l'action
  };

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
          <ShieldAlert className="h-7 w-7 text-pineapple" />
          Trust & Safety
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Traitez les signalements de la communauté.
        </p>
      </motion.div>

      {/* Liste des signalements */}
      <div className="space-y-3">
        {reports
          .filter((r) => r.status === 'PENDING' || r.status === 'INVESTIGATING')
          .map((report) => {
            const TargetIcon = targetTypeIcons[report.targetType];
            return (
              <Card key={report.id} variant="neo-extruded" className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-xl bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
                      <TargetIcon className="h-5 w-5 text-red-600 dark:text-red-400" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium text-gray-800 dark:text-white">
                          {report.targetName}
                        </span>
                        <Badge variant="danger">{reasonLabels[report.reason]}</Badge>
                      </div>
                      <p className="text-sm text-gray-500 mt-0.5">
                        Signalé par {report.reporterName} · Statut :{' '}
                        <span className="font-medium">{statusLabels[report.status]}</span>
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleOpenReport(report)}
                    icon={Eye}
                  >
                    Examiner
                  </Button>
                </div>
              </Card>
            );
          })}

        {reports.filter((r) => r.status === 'PENDING' || r.status === 'INVESTIGATING').length === 0 && (
          <Card variant="neo-inset" className="p-8 text-center">
            <CheckCircle className="h-16 w-16 text-emerald-500 mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-300">Aucun signalement en attente.</p>
          </Card>
        )}
      </div>

      {/* Modale d'examen */}
      <AnimatePresence>
        {selectedReport && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
            onClick={handleCloseModal}
          >
            <motion.div
              initial={{ scale: 0.95, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 20 }}
              className="bg-white dark:bg-slate-900 rounded-2xl p-6 w-full max-w-2xl shadow-neo-extruded dark:shadow-neo-dark-extruded"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
                <Flag className="h-5 w-5 text-red-500" />
                Examen du signalement
              </h3>

              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <Badge variant="danger">{reasonLabels[selectedReport.reason]}</Badge>
                  <Badge variant="info">{selectedReport.targetType}</Badge>
                </div>
                <div className="p-4 rounded-xl bg-background-light dark:bg-slate-800">
                  <p className="text-sm text-gray-700 dark:text-gray-300">
                    <span className="font-medium">Contenu signalé :</span> {selectedReport.content}
                  </p>
                </div>
                <p className="text-sm text-gray-500">
                  Signalé par {selectedReport.reporterName}
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-6">
                <Button variant="secondary" onClick={() => handleAction('HIDE_CONTENT')} icon={Eye}>
                  Masquer le contenu
                </Button>
                <Button variant="secondary" onClick={() => handleAction('WARN_USER')} icon={AlertTriangle}>
                  Avertir l'utilisateur
                </Button>
                <Button variant="danger" onClick={() => handleAction('BAN_USER')} icon={Ban}>
                  Bannir l'utilisateur
                </Button>
                <Button variant="ghost" onClick={() => handleAction('DISMISS')} icon={XCircle}>
                  Classer sans suite
                </Button>
              </div>
              <div className="mt-4 flex justify-end">
                <Button variant="ghost" onClick={handleCloseModal}>
                  Fermer
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};