// frontend/src/features/democracy/VotingBoothScreen.tsx

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Lock,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  ShieldCheck,
  FileCheck2,
  Eye,
  EyeOff,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';

// ---------- Types ----------
interface Movement {
  id: string;
  name: string;
  candidates: { id: string; name: string; position: string }[];
}

const mockMovements: Movement[] = [
  {
    id: 'mv1',
    name: 'Mouvement Bleu',
    candidates: [
      { id: 'c1', name: 'Alice Ndongo', position: 'Présidente' },
      { id: 'c2', name: 'Charlie Mbarga', position: 'Vice-président' },
    ],
  },
  {
    id: 'mv2',
    name: 'Alliance Innovation',
    candidates: [
      { id: 'c3', name: 'Bob Kamga', position: 'Président' },
      { id: 'c4', name: 'Esther Fouda', position: 'Vice-présidente' },
    ],
  },
];

// Simule une vérification d'éligibilité (vrai dans la plupart des cas)
const IS_ELIGIBLE = true;

// Fonction utilitaire pour générer un faux hash de reçu
function generateVoterHash(): string {
  const chars = 'abcdef0123456789';
  let hash = '';
  for (let i = 0; i < 12; i++) {
    hash += chars[Math.floor(Math.random() * chars.length)];
  }
  return `${hash.slice(0, 4)}...${hash.slice(8)}`;
}

// ---------- Composant ----------
export const VotingBoothScreen: React.FC = () => {
  const [step, setStep] = useState(0); // 0: sélection, 1: confirmation, 2: chiffrement, 3: reçu
  const [selectedMovement, setSelectedMovement] = useState<Movement | null>(null);
  const [isEncrypting, setIsEncrypting] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [voterHash, setVoterHash] = useState<string | null>(null);

  // Simule l'étape de chiffrement : après 2.5s, on active le bouton de dépôt
  useEffect(() => {
    if (step === 2) {
      setIsEncrypting(true);
      const timer = setTimeout(() => {
        setIsEncrypting(false);
      }, 2500);
      return () => clearTimeout(timer);
    }
  }, [step]);

  const handleSelectMovement = (movement: Movement) => {
    setSelectedMovement(movement);
    setStep(1);
  };

  const handleConfirmSelection = () => {
    setStep(2);
  };

  const handleDepositBallot = () => {
    setIsSubmitting(true);
    // Simule un délai avant de générer le reçu
    setTimeout(() => {
      setVoterHash(generateVoterHash());
      setStep(3);
      setIsSubmitting(false);
    }, 1500);
  };

  const handleStartOver = () => {
    setStep(0);
    setSelectedMovement(null);
    setVoterHash(null);
    setIsEncrypting(false);
    setIsSubmitting(false);
  };

  // Affichage si non éligible
  if (!IS_ELIGIBLE) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <Card variant="neo-inset" className="p-8 text-center">
          <AlertTriangle className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-800 dark:text-white">Accès refusé</h2>
          <p className="text-gray-600 dark:text-gray-300 mt-2">
            Vous n'êtes pas éligible pour voter à cette élection.
          </p>
          <p className="text-sm text-gray-500 mt-1">
            Cette décision est basée sur les règles académiques et de certification définies par votre établissement.
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-4 md:p-6 pb-24 md:pb-6">
      <Card variant="glass" className="p-6 md:p-8">
        {/* En-tête avec verrou */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-xl bg-pineapple/20 flex items-center justify-center">
            <Lock className="h-6 w-6 text-pineapple" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Isoloir numérique</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">Vote sécurisé et anonyme</p>
          </div>
        </div>

        {/* Stepper (indicateur d'étape) */}
        <div className="flex items-center mb-8">
          {['Sélection', 'Confirmation', 'Chiffrement', 'Reçu'].map((label, index) => (
            <React.Fragment key={label}>
              {index > 0 && (
                <div className={cn('h-1 flex-1 mx-1 rounded', index <= step ? 'bg-pineapple' : 'bg-gray-300 dark:bg-slate-700')} />
              )}
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    'w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium',
                    index < step
                      ? 'bg-pineapple text-white'
                      : index === step
                        ? 'bg-pineapple/20 text-pineapple border-2 border-pineapple'
                        : 'bg-gray-200 dark:bg-slate-700 text-gray-500'
                  )}
                >
                  {index < step ? <CheckCircle2 className="w-4 h-4" /> : index + 1}
                </div>
                <span className="text-xs mt-1 text-gray-500 hidden sm:block">{label}</span>
              </div>
            </React.Fragment>
          ))}
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
          >
            {/* Étape 0 : Sélection */}
            {step === 0 && (
              <div>
                <h2 className="text-lg font-semibold mb-4">Choisissez votre mouvement</h2>
                <div className="space-y-3">
                  {mockMovements.map((movement) => (
                    <button
                      key={movement.id}
                      onClick={() => handleSelectMovement(movement)}
                      className="w-full p-4 rounded-2xl bg-white dark:bg-slate-800 border-2 border-transparent hover:border-pineapple transition-all text-left"
                    >
                      <h3 className="font-medium text-gray-800 dark:text-white">{movement.name}</h3>
                      <p className="text-sm text-gray-500">Candidats : {movement.candidates.map(c => c.name).join(', ')}</p>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Étape 1 : Confirmation */}
            {step === 1 && selectedMovement && (
              <div>
                <h2 className="text-lg font-semibold mb-2">Confirmez votre choix</h2>
                <div className="p-4 rounded-2xl bg-background-light dark:bg-slate-800 mb-4">
                  <p className="font-medium text-gray-800 dark:text-white">{selectedMovement.name}</p>
                  <ul className="mt-2 space-y-1">
                    {selectedMovement.candidates.map((c) => (
                      <li key={c.id} className="text-sm text-gray-600 dark:text-gray-300">
                        {c.position} : {c.name}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="flex items-start gap-2 p-3 rounded-xl bg-amber-50 dark:bg-amber-900/20 text-amber-800 dark:text-amber-200">
                  <AlertTriangle className="h-5 w-5 shrink-0" />
                  <p className="text-sm">
                    Ce choix est définitif et ne pourra être modifié après dépôt dans l'urne.
                  </p>
                </div>
                <div className="flex gap-3 mt-6">
                  <Button variant="secondary" onClick={() => setStep(0)}>Retour</Button>
                  <Button variant="primary" onClick={handleConfirmSelection} icon={CheckCircle2}>
                    Confirmer
                  </Button>
                </div>
              </div>
            )}

            {/* Étape 2 : Chiffrement */}
            {step === 2 && (
              <div className="text-center">
                {isEncrypting ? (
                  <>
                    <Loader2 className="h-16 w-16 text-pineapple animate-spin mx-auto mb-4" />
                    <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
                      Chiffrement asymétrique en cours...
                    </h2>
                    <p className="text-sm text-gray-500">Votre bulletin est protégé par cryptographie.</p>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="h-16 w-16 text-pineapple mx-auto mb-4" />
                    <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
                      Prêt à déposer
                    </h2>
                    <p className="text-sm text-gray-500 mb-4">
                      Bulletin chiffré, aucune donnée personnelle ne sera stockée avec le vote.
                    </p>
                    <Button
                      variant="primary"
                      size="lg"
                      onClick={handleDepositBallot}
                      isLoading={isSubmitting}
                      icon={FileCheck2}
                    >
                      Déposer dans l'urne
                    </Button>
                  </>
                )}
              </div>
            )}

            {/* Étape 3 : Reçu */}
            {step === 3 && voterHash && (
              <div className="text-center">
                <CheckCircle2 className="h-16 w-16 text-emerald-500 mx-auto mb-4" />
                <h2 className="text-xl font-bold text-gray-800 dark:text-white">Vote enregistré</h2>
                <p className="text-sm text-gray-500 mb-4">Votre participation a été prise en compte.</p>
                <div className="p-4 rounded-2xl bg-background-light dark:bg-slate-800 inline-block">
                  <span className="text-sm text-gray-500">Reçu de vote :</span>
                  <p className="font-mono text-lg font-bold text-pineapple">{voterHash}</p>
                </div>
                <div className="mt-6">
                  <Button variant="secondary" onClick={handleStartOver}>
                    Retour à l'accueil
                  </Button>
                </div>
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </Card>
    </div>
  );
};