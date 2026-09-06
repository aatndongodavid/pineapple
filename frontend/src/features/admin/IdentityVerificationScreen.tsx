// frontend/src/features/admin/IdentityVerificationScreen.tsx

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircle,
  XCircle,
  Eye,
  FileText,
  UserCheck,
  AlertCircle,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';

// Types
interface CertificationRequest {
  id: string;
  firstName: string;
  lastName: string;
  matricule: string;
  filiere: string;
  submittedAt: string; // ISO string
  documentUrl: string; // simulé
}

// Données mockées
const mockRequests: CertificationRequest[] = [
  {
    id: '1',
    firstName: 'Alice',
    lastName: 'Ndongo',
    matricule: 'ENSPD2026001',
    filiere: 'Génie Logiciel',
    submittedAt: '2026-09-01T09:30:00Z',
    documentUrl: '/documents/alice.pdf',
  },
  {
    id: '2',
    firstName: 'Bob',
    lastName: 'Kamga',
    matricule: 'ENSPD2026002',
    filiere: 'Génie Électrique',
    submittedAt: '2026-09-02T14:15:00Z',
    documentUrl: '/documents/bob.pdf',
  },
  {
    id: '3',
    firstName: 'Charlie',
    lastName: 'Mbarga',
    matricule: 'ENSPD2026003',
    filiere: 'Génie Mécanique',
    submittedAt: '2026-09-03T11:45:00Z',
    documentUrl: '/documents/charlie.pdf',
  },
];

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' });
}

export const IdentityVerificationScreen: React.FC = () => {
  const [requests, setRequests] = useState<CertificationRequest[]>(mockRequests);
  const [rejectionReason, setRejectionReason] = useState<string>('');
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(null);

  const handleApprove = (id: string) => {
    setRequests((prev) => prev.filter((req) => req.id !== id));
    // Ici on ferait un appel API pour approuver
  };

  const handleRejectClick = (id: string) => {
    setSelectedRequestId(id);
    setShowRejectModal(true);
  };

  const confirmReject = () => {
    if (selectedRequestId && rejectionReason.trim()) {
      setRequests((prev) => prev.filter((req) => req.id !== selectedRequestId));
      // Appel API avec motif
      setShowRejectModal(false);
      setRejectionReason('');
      setSelectedRequestId(null);
    }
  };

  const viewDocument = (url: string) => {
    // Simuler l'ouverture du document
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
          <UserCheck className="h-7 w-7 text-pineapple" />
          Certification des étudiants
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Validez ou rejetez les demandes de certification annuelle.
        </p>
      </motion.div>

      <Card variant="neo-extruded" className="p-4 md:p-6 overflow-x-auto">
        {requests.length === 0 ? (
          <div className="text-center py-12">
            <CheckCircle className="h-16 w-16 text-emerald-500 mx-auto mb-4" />
            <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
              Toutes les demandes sont traitées
            </h2>
            <p className="text-sm text-gray-500 mt-2">
              Aucune certification en attente de validation.
            </p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-300 dark:border-slate-700">
                <th className="px-4 py-3 text-left font-medium text-gray-500 dark:text-gray-400">Nom</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500 dark:text-gray-400">Prénom</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500 dark:text-gray-400">Matricule</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500 dark:text-gray-400">Filière</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500 dark:text-gray-400">Date de soumission</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500 dark:text-gray-400">Justificatif</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500 dark:text-gray-400">Actions</th>
              </tr>
            </thead>
            <tbody>
              {requests.map((req) => (
                <tr key={req.id} className="border-b border-gray-200 dark:border-slate-800 hover:bg-pineapple/5 transition-colors">
                  <td className="px-4 py-3 text-gray-800 dark:text-white font-medium">{req.lastName}</td>
                  <td className="px-4 py-3 text-gray-800 dark:text-white">{req.firstName}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300 font-mono text-xs">{req.matricule}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{req.filiere}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{formatDate(req.submittedAt)}</td>
                  <td className="px-4 py-3">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => viewDocument(req.documentUrl)}
                      icon={Eye}
                    >
                      Voir le document
                    </Button>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleApprove(req.id)}
                        icon={CheckCircle}
                      >
                        Approuver
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleRejectClick(req.id)}
                        icon={XCircle}
                      >
                        Rejeter
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {/* Modale de rejet */}
      <AnimatePresence>
        {showRejectModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
            onClick={() => setShowRejectModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 20 }}
              className="bg-white dark:bg-slate-900 rounded-2xl p-6 w-full max-w-md shadow-neo-extruded dark:shadow-neo-dark-extruded"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-red-500" />
                Motif de rejet
              </h3>
              <textarea
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="Précisez le motif du rejet..."
                rows={4}
                className="w-full px-4 py-3 rounded-xl bg-background-light dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple resize-none"
              />
              <div className="flex justify-end gap-3 mt-4">
                <Button variant="secondary" onClick={() => setShowRejectModal(false)}>
                  Annuler
                </Button>
                <Button
                  variant="primary"
                  onClick={confirmReject}
                  disabled={!rejectionReason.trim()}
                >
                  Confirmer le rejet
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};