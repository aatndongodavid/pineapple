// frontend/src/features/feed/CreatePostModal.tsx

import React, { useState, useRef, ChangeEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Image as ImageIcon, Globe, Building, User, Loader2, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/Button';
import apiClient from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import { useAuthStore } from '@/lib/store/authStore';
import { useTenantStore } from '@/lib/store/tenantStore';

// Types
type AudienceScope = 'LOCAL' | 'EXTENDED' | 'SPONSORED' | 'PUBLIC';

interface Organization {
  id: string;
  name: string;
}

interface CreatePostModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPostCreated?: () => void;
}

// Liste d'organisations simulée (à remplacer par un appel API)
const mockOrganizations: Organization[] = [
  { id: 'org-1', name: 'Club Robotique' },
  { id: 'org-2', name: 'BDE' },
  { id: 'org-3', name: 'Association IA' },
];

export const CreatePostModal: React.FC<CreatePostModalProps> = ({
  isOpen,
  onClose,
  onPostCreated,
}) => {
  const [content, setContent] = useState('');
  const [mediaUrls, setMediaUrls] = useState<string[]>([]);
  const [scope, setScope] = useState<AudienceScope>('LOCAL');
  const [postAs, setPostAs] = useState<'profile' | 'organization'>('profile');
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { token } = useAuthStore();
  const { tenantId } = useTenantStore();

  // Auto‑extensible textarea
  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setContent(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  // Gestion des fichiers médias
  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newMedia: string[] = [];
    Array.from(files).forEach((file) => {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onloadend = () => {
          const dataUrl = reader.result as string;
          newMedia.push(dataUrl);
          setMediaUrls((prev) => [...prev, dataUrl]);
        };
        reader.readAsDataURL(file);
      } else if (file.type === 'application/pdf') {
        // On accepte le PDF mais sans prévisualisation (on stockera juste le nom)
        // Pour la démonstration, on ignore ou on stocke un placeholder
        // On peut ajouter une icône PDF
        // Ici on va simplement l'ajouter comme une URL de données ? Non, on ne peut pas facilement.
        // On va simuler en ajoutant un lien factice
        newMedia.push(`pdf:${file.name}`);
        setMediaUrls((prev) => [...prev, `pdf:${file.name}`]);
      }
    });

    // Reset l'input pour permettre de sélectionner les mêmes fichiers à nouveau
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeMedia = (index: number) => {
    setMediaUrls((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (!content.trim() && mediaUrls.length === 0) {
      setError('Veuillez écrire un message ou ajouter un média.');
      return;
    }

    if (!token || !tenantId) {
      setError('Session invalide. Veuillez vous reconnecter.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    const payload = {
      content: content.trim(),
      post_type: 'TEXT', // Pour simplifier, on considère le type TEXT ; pourrait être enrichi
      media_urls: mediaUrls,
      organization_id: postAs === 'organization' ? selectedOrgId : undefined,
      scope: scope,
    };

    try {
      await apiClient.post(API_ENDPOINTS.community.posts, payload, {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
        },
      });

      // Réinitialiser les champs
      setContent('');
      setMediaUrls([]);
      setScope('LOCAL');
      setPostAs('profile');
      setSelectedOrgId(null);
      setError(null);

      onPostCreated?.();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la publication.');
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
            className="w-full max-w-lg bg-white dark:bg-slate-900 rounded-3xl shadow-neo-extruded dark:shadow-neo-dark-extruded overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* En-tête */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-slate-700">
              <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
                Créer une publication
              </h2>
              <button onClick={onClose} className="p-1 rounded-full hover:bg-pineapple/10">
                <X className="h-5 w-5 text-gray-500" />
              </button>
            </div>

            {/* Corps */}
            <div className="p-4 space-y-4">
              {/* Zone de texte */}
              <textarea
                ref={textareaRef}
                value={content}
                onChange={handleContentChange}
                placeholder="Quoi de neuf sur le campus ?"
                rows={3}
                className="w-full px-4 py-3 rounded-xl bg-background-light dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple resize-none"
                style={{ minHeight: '80px' }}
              />

              {/* Aperçu des médias */}
              {mediaUrls.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {mediaUrls.map((url, index) => (
                    <div key={index} className="relative group w-24 h-24 rounded-lg overflow-hidden">
                      {url.startsWith('pdf:') ? (
                        <div className="w-full h-full flex items-center justify-center bg-gray-100 dark:bg-slate-700">
                          <FileText className="h-8 w-8 text-gray-400" />
                        </div>
                      ) : (
                        <img src={url} alt={`Média ${index + 1}`} className="w-full h-full object-cover" />
                      )}
                      <button
                        onClick={() => removeMedia(index)}
                        className="absolute top-0 right-0 p-1 bg-red-500 text-white rounded-bl-lg opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Boutons d'ajout de médias */}
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                  icon={ImageIcon}
                >
                  Image
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                  icon={FileText}
                >
                  Document
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*,application/pdf"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>

              {/* Sélecteur de portée */}
              <div>
                <span className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Audience
                </span>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setScope('LOCAL')}
                    className={cn(
                      'flex items-center gap-2 p-3 rounded-xl border-2 transition-colors',
                      scope === 'LOCAL'
                        ? 'border-pineapple bg-pineapple/10 text-pineapple'
                        : 'border-transparent bg-background-light dark:bg-slate-800 text-gray-600 dark:text-gray-300'
                    )}
                  >
                    <Building className="h-5 w-5" />
                    <span className="text-sm">Établissement uniquement</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setScope('EXTENDED')}
                    className={cn(
                      'flex items-center gap-2 p-3 rounded-xl border-2 transition-colors',
                      scope === 'EXTENDED'
                        ? 'border-pineapple bg-pineapple/10 text-pineapple'
                        : 'border-transparent bg-background-light dark:bg-slate-800 text-gray-600 dark:text-gray-300'
                    )}
                  >
                    <Globe className="h-5 w-5" />
                    <span className="text-sm">Réseau Pineapple</span>
                  </button>
                </div>
              </div>

              {/* Sélecteur Profil / Organisation */}
              <div>
                <span className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Publier en tant que
                </span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setPostAs('profile')}
                    className={cn(
                      'flex items-center gap-2 px-4 py-2 rounded-xl border-2 transition-colors',
                      postAs === 'profile'
                        ? 'border-pineapple bg-pineapple/10 text-pineapple'
                        : 'border-transparent bg-background-light dark:bg-slate-800 text-gray-600 dark:text-gray-300'
                    )}
                  >
                    <User className="h-4 w-4" />
                    <span className="text-sm">Profil personnel</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setPostAs('organization')}
                    className={cn(
                      'flex items-center gap-2 px-4 py-2 rounded-xl border-2 transition-colors',
                      postAs === 'organization'
                        ? 'border-pineapple bg-pineapple/10 text-pineapple'
                        : 'border-transparent bg-background-light dark:bg-slate-800 text-gray-600 dark:text-gray-300'
                    )}
                  >
                    <Building className="h-4 w-4" />
                    <span className="text-sm">Organisation</span>
                  </button>
                </div>

                {postAs === 'organization' && (
                  <select
                    value={selectedOrgId || ''}
                    onChange={(e) => setSelectedOrgId(e.target.value)}
                    className="mt-2 w-full px-4 py-2.5 rounded-xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 shadow-neo-inset dark:shadow-neo-dark-inset focus:outline-none focus:ring-2 focus:ring-pineapple"
                  >
                    <option value="" disabled>
                      Choisir une organisation
                    </option>
                    {mockOrganizations.map((org) => (
                      <option key={org.id} value={org.id}>
                        {org.name}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-red-100 text-red-700 text-sm">{error}</div>
              )}
            </div>

            {/* Pied */}
            <div className="flex justify-end gap-3 p-4 border-t border-gray-200 dark:border-slate-700">
              <Button variant="secondary" onClick={onClose}>
                Annuler
              </Button>
              <Button
                variant="primary"
                onClick={handleSubmit}
                isLoading={isSubmitting}
                disabled={isSubmitting}
                icon={Loader2}
              >
                Publier
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};