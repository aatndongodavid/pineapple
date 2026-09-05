// frontend/src/features/auth/ProfileScreen.tsx

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  ShieldCheck,
  BookOpen,
  LogOut,
  RefreshCw,
  ChevronRight,
  User,
  Mail,
  Building,
  GraduationCap,
  IdCard,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusPill } from '@/components/ui/StatusPill';
import { CertificationUploadModal } from './CertificationUploadModal';
import { useAuthStore } from '@/lib/store/authStore';
import { useTenantStore } from '@/lib/store/tenantStore';
import { cn } from '@/lib/utils';

export const ProfileScreen: React.FC = () => {
  const { user, campusStatusDisplay, logout } = useAuthStore();
  const { campusName, tenantId } = useTenantStore();
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  const handleLogout = () => {
    logout();
    // Redirection vers login (à adapter selon le routeur)
    window.location.href = '/login';
  };

  const handleRenewCertification = () => {
    setIsUploadModalOpen(true);
  };

  const needsRenewal = campusStatusDisplay === 'Certification en attente' ||
                       campusStatusDisplay === 'Non certifié' ||
                       campusStatusDisplay === 'Archivé';

  return (
    <div className="max-w-2xl mx-auto p-4 md:p-6 space-y-6 pb-24 md:pb-6">
      {/* En-tête */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Profil</h1>
        <Button variant="ghost" size="sm" onClick={handleLogout} icon={LogOut}>
          Déconnexion
        </Button>
      </motion.div>

      {/* Carte Pineapple ID */}
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.05 }}
      >
        <Card variant="glass" className="p-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-pineapple/20 flex items-center justify-center shadow-neo-extruded dark:shadow-neo-dark-extruded">
              <User className="h-8 w-8 text-pineapple" />
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-white">
                {user?.firstName} {user?.lastName}
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-2">
                <Mail className="h-4 w-4" /> {user?.email}
              </p>
              <div className="mt-2">
                <StatusPill status={campusStatusDisplay || 'Non certifié'} />
              </div>
            </div>
          </div>

          {/* Informations académiques */}
          <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex items-center gap-3 p-3 rounded-xl bg-background-light dark:bg-slate-800">
              <Building className="h-5 w-5 text-pineapple" />
              <div>
                <span className="text-xs text-gray-500 dark:text-gray-400">Établissement</span>
                <p className="font-medium text-gray-800 dark:text-white">{campusName || 'ENSPD'}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-xl bg-background-light dark:bg-slate-800">
              <GraduationCap className="h-5 w-5 text-pineapple" />
              <div>
                <span className="text-xs text-gray-500 dark:text-gray-400">Filière</span>
                <p className="font-medium text-gray-800 dark:text-white">
                  {user?.filiere || 'Non renseignée'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-xl bg-background-light dark:bg-slate-800">
              <IdCard className="h-5 w-5 text-pineapple" />
              <div>
                <span className="text-xs text-gray-500 dark:text-gray-400">Matricule</span>
                <p className="font-medium text-gray-800 dark:text-white">{user?.matricule || 'N/A'}</p>
              </div>
            </div>
          </div>

          {/* Bouton de renouvellement de certification */}
          {needsRenewal && (
            <div className="mt-6">
              <Button
                variant="primary"
                className="w-full"
                onClick={handleRenewCertification}
                icon={RefreshCw}
              >
                Renouveler ma certification
              </Button>
            </div>
          )}
        </Card>
      </motion.div>

      {/* Raccourcis */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="space-y-3"
      >
        <Card variant="flat" className="p-4">
          <button className="w-full flex items-center gap-3 py-2 hover:bg-pineapple/5 rounded-lg transition-colors">
            <ShieldCheck className="h-5 w-5 text-pineapple" />
            <span className="flex-1 text-left text-gray-700 dark:text-gray-200">Security Center</span>
            <ChevronRight className="h-5 w-5 text-gray-400" />
          </button>
          <div className="border-t border-gray-200 dark:border-slate-700 my-2" />
          <button className="w-full flex items-center gap-3 py-2 hover:bg-pineapple/5 rounded-lg transition-colors">
            <BookOpen className="h-5 w-5 text-pineapple" />
            <span className="flex-1 text-left text-gray-700 dark:text-gray-200">Ma bibliothèque</span>
            <ChevronRight className="h-5 w-5 text-gray-400" />
          </button>
        </Card>
      </motion.div>

      {/* Modale de téléversement de certification */}
      <CertificationUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
      />
    </div>
  );
};