// frontend/src/features/academy/PineappleReaderScreen.tsx

import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { X, FileText, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import apiClient from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import { useAuthStore } from '@/lib/store/authStore';
import { useTenantStore } from '@/lib/store/tenantStore';

interface PineappleReaderScreenProps {
  documentId: string;
  onClose: () => void;
  documentTitle?: string;
}

export const PineappleReaderScreen: React.FC<PineappleReaderScreenProps> = ({
  documentId,
  onClose,
  documentTitle,
}) => {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const { token } = useAuthStore();
  const { tenantId } = useTenantStore();
  const { user } = useAuthStore();

  // Récupérer les informations de l'utilisateur pour le filigrane
  const studentName = user ? `${user.firstName} ${user.lastName}` : 'Utilisateur';
  const matricule = user?.matricule || 'N/A';
  const currentDate = new Date().toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });

  useEffect(() => {
    const controller = new AbortController();
    const loadPdf = async () => {
      if (!token || !tenantId) {
        setError('Session invalide');
        setIsLoading(false);
        return;
      }

      try {
        const response = await apiClient.get(
          API_ENDPOINTS.academy.readerStream(documentId),
          {
            headers: {
              Authorization: `Bearer ${token}`,
              'X-Tenant-ID': tenantId,
            },
            responseType: 'blob',
            signal: controller.signal,
          }
        );

        const blobUrl = URL.createObjectURL(response.data);
        setPdfUrl(blobUrl);
        setIsLoading(false);
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          setError('Impossible de charger le document protégé.');
          setIsLoading(false);
        }
      }
    };

    loadPdf();

    return () => {
      controller.abort();
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl);
      }
    };
  }, [documentId, token, tenantId]);

  // Désactivation du clic droit et de la sélection
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const preventContextMenu = (e: MouseEvent) => e.preventDefault();
    const preventSelection = (e: Event) => e.preventDefault();

    container.addEventListener('contextmenu', preventContextMenu);
    container.addEventListener('selectstart', preventSelection);
    container.addEventListener('dragstart', preventSelection);

    return () => {
      container.removeEventListener('contextmenu', preventContextMenu);
      container.removeEventListener('selectstart', preventSelection);
      container.removeEventListener('dragstart', preventSelection);
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 z-50 bg-black/90 backdrop-blur-sm flex flex-col"
      style={{ userSelect: 'none', WebkitUserSelect: 'none', msUserSelect: 'none' }}
    >
      {/* Barre supérieure */}
      <div className="flex items-center justify-between p-4 bg-gray-900/80 border-b border-gray-800">
        <div className="flex items-center gap-3 min-w-0">
          <ShieldCheck className="h-6 w-6 text-pineapple shrink-0" />
          <div className="min-w-0">
            <h2 className="text-white font-semibold truncate">
              {documentTitle || 'Document sécurisé'}
            </h2>
            <p className="text-xs text-gray-400">
              Pineapple Reader · Lecture protégée
            </p>
          </div>
        </div>
        <Button
          variant="glass"
          size="sm"
          onClick={onClose}
          icon={X}
          className="shrink-0"
        >
          Fermer
        </Button>
      </div>

      {/* Zone de contenu */}
      <div className="flex-1 relative overflow-hidden">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <FileText className="h-16 w-16 text-gray-500 animate-pulse mx-auto mb-4" />
              <p className="text-gray-400">Chargement du document sécurisé...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center p-6">
            <div className="text-center">
              <p className="text-red-400 mb-4">{error}</p>
              <Button variant="secondary" onClick={onClose}>
                Retour à la bibliothèque
              </Button>
            </div>
          </div>
        )}

        {pdfUrl && !isLoading && !error && (
          <iframe
            src={pdfUrl}
            title="Pineapple Reader"
            className="w-full h-full border-0"
            sandbox="allow-scripts allow-same-origin"
            style={{ pointerEvents: 'auto' }}
          />
        )}

        {/* Filigrane dynamique superposé */}
        {!isLoading && !error && (
          <div
            className="absolute inset-0 pointer-events-none flex items-center justify-center"
            aria-hidden="true"
          >
            <div
              className="absolute transform -rotate-45 text-center select-none"
              style={{
                opacity: 0.2,
                color: '#ffffff',
                fontSize: '2rem',
                fontWeight: 'bold',
                textShadow: '2px 2px 4px rgba(0,0,0,0.5)',
                maxWidth: '90%',
                userSelect: 'none',
              }}
            >
              <p>{studentName}</p>
              <p>{matricule}</p>
              <p>{currentDate}</p>
              <p className="mt-2 text-sm">PROPRIÉTÉ EXCLUSIVE - NE PAS DIFFUSER</p>
            </div>
          </div>
        )}
      </div>

      {/* Bouton flottant fermer (mobile) */}
      <motion.button
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.3 }}
        onClick={onClose}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-pineapple text-white shadow-neo-extruded dark:shadow-neo-dark-extruded flex items-center justify-center hover:shadow-neo-pressed dark:hover:shadow-neo-dark-pressed transition-shadow md:hidden"
        aria-label="Fermer le lecteur"
      >
        <X className="h-7 w-7" />
      </motion.button>
    </div>
  );
};