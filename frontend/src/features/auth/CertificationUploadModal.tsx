// frontend/src/features/auth/CertificationUploadModal.tsx

import React, { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, X, FileText, Image as ImageIcon, FilePlus } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import { apiClient, API_ENDPOINTS } from '@/lib/api';
import { useAuthStore } from '@/lib/store/authStore';
import { useTenantStore } from '@/lib/store/tenantStore';

// Types de documents acceptés (alignés sur le backend)
enum DocumentType {
  CARTE_ETUDIANT = 'CARTE_ETUDIANT',
  QUITTANCE = 'QUITTANCE',
  DIPLOME = 'DIPLOME',
}

interface CertificationUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const documentOptions = [
  { type: DocumentType.CARTE_ETUDIANT, label: "Carte d'étudiant", icon: FileText },
  { type: DocumentType.QUITTANCE, label: 'Quitus de scolarité', icon: FileText },
  { type: DocumentType.DIPLOME, label: 'Attestation / Diplôme', icon: FileText },
];

export const CertificationUploadModal: React.FC<CertificationUploadModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [selectedType, setSelectedType] = useState<DocumentType>(DocumentType.CARTE_ETUDIANT);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { token } = useAuthStore();
  const { tenantId } = useTenantStore();
  const { updateCampusStatus } = useAuthStore();

  // Gestion du fichier sélectionné ou déposé
  const handleFile = useCallback((selectedFile: File | undefined) => {
    if (!selectedFile) return;
    // Vérifier le type (image ou PDF)
    if (!selectedFile.type.startsWith('image/') && selectedFile.type !== 'application/pdf') {
      setError('Seules les images (PNG, JPG) et les PDF sont acceptés.');
      return;
    }
    setFile(selectedFile);
    // Prévisualisation pour les images
    if (selectedFile.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onloadend = () => setPreviewUrl(reader.result as string);
      reader.readAsDataURL(selectedFile);
    } else {
      setPreviewUrl(null); // pas de prévisualisation pour PDF
    }
    setError(null);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, [handleFile]);

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleSubmit = async () => {
    if (!file) {
      setError('Veuillez sélectionner un fichier.');
      return;
    }
    if (!token || !tenantId) {
      setError('Session invalide. Veuillez vous reconnecter.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    const formData = new FormData();
    formData.append('document_type', selectedType);
    formData.append('file', file);

    try {
      await apiClient.post(API_ENDPOINTS.identity.certificationSubmit, formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
          'Content-Type': 'multipart/form-data',
        },
      });
      // Mettre à jour le statut campus affiché
      updateCampusStatus('Certification en attente');
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de l\'envoi du justificatif.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.95, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.95, y: 20 }}
            transition={{ type: 'spring', damping: 20, stiffness: 300 }}
            className="w-full max-w-lg bg-white dark:bg-slate-900 rounded-3xl shadow-neo-extruded dark:shadow-neo-dark-extruded p-6"
            onClick={(e) => e.stopPropagation()}
          >
            {/* En-tête */}
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800 dark:text-white">
                Soumettre un justificatif
              </h3>
              <button onClick={onClose} className="p-1 rounded-full hover:bg-pineapple/10">
                <X className="h-5 w-5 text-gray-500" />
              </button>
            </div>

            {/* Choix du type de document */}
            <div className="mb-4">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Type de document</span>
              <div className="grid grid-cols-3 gap-2 mt-2">
                {documentOptions.map((opt) => (
                  <button
                    key={opt.type}
                    onClick={() => setSelectedType(opt.type)}
                    className={cn(
                      'flex flex-col items-center p-3 rounded-xl transition-all',
                      selectedType === opt.type
                        ? 'bg-pineapple/15 border-2 border-pineapple text-pineapple'
                        : 'bg-background-light dark:bg-slate-800 border-2 border-transparent text-gray-600 dark:text-gray-300',
                    )}
                  >
                    <opt.icon className="h-6 w-6" />
                    <span className="text-xs mt-1 text-center">{opt.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Zone de drag & drop */}
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
              className={cn(
                'border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-colors',
                isDragOver
                  ? 'border-pineapple bg-pineapple/5'
                  : 'border-gray-300 dark:border-slate-700 hover:border-pineapple',
              )}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,application/pdf"
                className="hidden"
                onChange={(e) => handleFile(e.target.files?.[0])}
              />
              {previewUrl ? (
                <img src={previewUrl} alt="Aperçu" className="max-h-40 mx-auto rounded-lg" />
              ) : file ? (
                <div className="flex items-center gap-2 justify-center text-gray-500">
                  <FileText className="h-6 w-6" />
                  <span className="text-sm">{file.name}</span>
                </div>
              ) : (
                <div className="flex flex-col items-center text-gray-500">
                  <Upload className="h-8 w-8" />
                  <p className="text-sm mt-2">
                    Glissez-déposez votre fichier ici ou cliquez pour parcourir
                  </p>
                  <p className="text-xs mt-1">PNG, JPG ou PDF (max 10 Mo)</p>
                </div>
              )}
            </div>

            {file && (
              <div className="mt-2 text-xs text-gray-500 truncate">
                Fichier : {file.name}
              </div>
            )}

            {error && (
              <div className="mt-3 p-3 rounded-lg bg-red-100 text-red-700 text-sm">
                {error}
              </div>
            )}

            {/* Boutons d'action */}
            <div className="flex gap-3 mt-6">
              <Button variant="secondary" className="flex-1" onClick={onClose}>
                Annuler
              </Button>
              <Button
                variant="primary"
                className="flex-1"
                onClick={handleSubmit}
                isLoading={isSubmitting}
                disabled={!file}
                icon={FilePlus}
              >
                Envoyer
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};