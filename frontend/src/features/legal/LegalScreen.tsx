// frontend/src/features/legal/LegalScreen.tsx

import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Shield, FileText, Lock, ArrowLeft, AlertCircle } from 'lucide-react';
import { Card } from '@/components/ui/Card';

import cguContent from '@/content/legal/cgu.md?raw';
import confidentialiteContent from '@/content/legal/confidentialite.md?raw';
import mentionsLegalesContent from '@/content/legal/mentions-legales.md?raw';

const legalDocs: Record<string, { title: string; icon: React.ElementType; content: string }> = {
  cgu: {
    title: "Conditions Générales d'Utilisation",
    icon: FileText,
    content: cguContent,
  },
  confidentialite: {
    title: 'Politique de Confidentialité',
    icon: Lock,
    content: confidentialiteContent,
  },
  'mentions-legales': {
    title: 'Mentions Légales',
    icon: Shield,
    content: mentionsLegalesContent,
  },
};

export const LegalScreen: React.FC = () => {
  const { docType = 'cgu' } = useParams<{ docType: string }>();
  const doc = legalDocs[docType] || legalDocs.cgu;
  const Icon = doc.icon;

  return (
    <div className="max-w-4xl mx-auto p-4 md:p-8 pb-24 space-y-6">
      <div className="flex items-center justify-between">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-sm text-primary hover:underline font-medium"
        >
          <ArrowLeft className="h-4 w-4" />
          Retour à l'accueil
        </Link>
        <div className="flex items-center gap-3 text-xs">
          <Link
            to="/legal/cgu"
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              docType === 'cgu' ? 'bg-primary text-white' : 'bg-gray-200 dark:bg-slate-800 text-gray-700 dark:text-gray-300'
            }`}
          >
            CGU
          </Link>
          <Link
            to="/legal/confidentialite"
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              docType === 'confidentialite' ? 'bg-primary text-white' : 'bg-gray-200 dark:bg-slate-800 text-gray-700 dark:text-gray-300'
            }`}
          >
            Confidentialité
          </Link>
          <Link
            to="/legal/mentions-legales"
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              docType === 'mentions-legales' ? 'bg-primary text-white' : 'bg-gray-200 dark:bg-slate-800 text-gray-700 dark:text-gray-300'
            }`}
          >
            Mentions Légales
          </Link>
        </div>
      </div>

      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <Card variant="default" className="p-6 md:p-8 space-y-6">
          <div className="flex items-center gap-3 border-b border-gray-200 dark:border-slate-800 pb-4">
            <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center">
              <Icon className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-800 dark:text-white">{doc.title}</h1>
              <p className="text-xs text-gray-500">Document légal officiel — Version 1.0.0</p>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-300 text-xs flex items-center gap-2">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span>Contenu juridique à valider par un juriste certifié avant déploiement définitif.</span>
          </div>

          <div className="prose dark:prose-invert max-w-none text-sm text-gray-700 dark:text-gray-300 space-y-4 whitespace-pre-wrap">
            {doc.content}
          </div>
        </Card>
      </motion.div>
    </div>
  );
};
