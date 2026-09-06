// frontend/src/features/admin/DemocracyControlScreen.tsx

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus,
  Vote,
  CheckCircle,
  XCircle,
  Lock,
  ShieldCheck,
  Calendar,
  Settings,
  BarChart3,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';

// Types
type ElectionStatus = 'CAMPAIGN' | 'VOTING_OPEN' | 'VOTING_CLOSED' | 'RESULTS_PUBLISHED';

interface Movement {
  id: string;
  name: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
}

interface Election {
  id: string;
  title: string;
  type: string;
  status: ElectionStatus;
  movements: Movement[];
  votingStartAt?: string;
  votingEndAt?: string;
}

const mockElections: Election[] = [
  {
    id: 'e1',
    title: 'Élection BDE ENSPD 2027',
    type: 'BDE',
    status: 'CAMPAIGN',
    movements: [
      { id: 'm1', name: 'Mouvement Bleu', status: 'APPROVED' },
      { id: 'm2', name: 'Alliance Innovation', status: 'PENDING' },
    ],
  },
  {
    id: 'e2',
    title: 'Élection Délégué L3',
    type: 'Délégué',
    status: 'VOTING_OPEN',
    movements: [
      { id: 'm3', name: 'Liste A', status: 'APPROVED' },
      { id: 'm4', name: 'Liste B', status: 'APPROVED' },
    ],
  },
];

const statusLabels: Record<ElectionStatus, string> = {
  CAMPAIGN: 'Campagne',
  VOTING_OPEN: 'Vote ouvert',
  VOTING_CLOSED: 'Dépouillement',
  RESULTS_PUBLISHED: 'Résultats publiés',
};

const statusVariants: Record<ElectionStatus, 'info' | 'success' | 'warning' | 'default'> = {
  CAMPAIGN: 'info',
  VOTING_OPEN: 'success',
  VOTING_CLOSED: 'warning',
  RESULTS_PUBLISHED: 'default',
};

export const DemocracyControlScreen: React.FC = () => {
  const [elections, setElections] = useState<Election[]>(mockElections);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newElection, setNewElection] = useState({
    title: '',
    type: 'BDE',
    startDate: '',
    endDate: '',
    filieres: [] as string[],
    niveaux: [] as string[],
  });

  const handleCreateElection = () => {
    // Simulation de création
    const election: Election = {
      id: `e${Date.now()}`,
      title: newElection.title || 'Nouvelle élection',
      type: newElection.type,
      status: 'CAMPAIGN',
      movements: [],
    };
    setElections([...elections, election]);
    setShowCreateModal(false);
    setNewElection({ title: '', type: 'BDE', startDate: '', endDate: '', filieres: [], niveaux: [] });
  };

  const handleApproveMovement = (electionId: string, movementId: string) => {
    setElections((prev) =>
      prev.map((e) =>
        e.id === electionId
          ? {
              ...e,
              movements: e.movements.map((m) =>
                m.id === movementId ? { ...m, status: 'APPROVED' } : m
              ),
            }
          : e
      )
    );
  };

  const handleRejectMovement = (electionId: string, movementId: string) => {
    setElections((prev) =>
      prev.map((e) =>
        e.id === electionId
          ? {
              ...e,
              movements: e.movements.map((m) =>
                m.id === movementId ? { ...m, status: 'REJECTED' } : m
              ),
            }
          : e
      )
    );
  };

  const handleTallyResults = (electionId: string) => {
    setElections((prev) =>
      prev.map((e) =>
        e.id === electionId ? { ...e, status: 'RESULTS_PUBLISHED' } : e
      )
    );
  };

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
            <Vote className="h-7 w-7 text-pineapple" />
            Democracy Control
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Gestion des élections et des mouvements</p>
        </div>
        <Button variant="primary" onClick={() => setShowCreateModal(true)} icon={Plus}>
          Créer une élection
        </Button>
      </motion.div>

      {/* Indicateur de sécurité */}
      <Card variant="glass" className="p-4 flex items-center gap-3">
        <ShieldCheck className="h-6 w-6 text-emerald-500" />
        <div className="text-sm text-gray-600 dark:text-gray-300">
          Les bulletins de vote sont chiffrés de bout en bout. Même les administrateurs ne peuvent pas
          voir le choix des électeurs. Audit immuable activé.
        </div>
        <Lock className="h-5 w-5 text-gray-400 ml-auto" />
      </Card>

      {/* Liste des élections */}
      <div className="space-y-4">
        {elections.map((election) => (
          <Card key={election.id} variant="neo-extruded" className="p-5">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold text-gray-800 dark:text-white">{election.title}</h3>
                <p className="text-sm text-gray-500">{election.type}</p>
              </div>
              <Badge variant={statusVariants[election.status]}>{statusLabels[election.status]}</Badge>
            </div>

            {/* Mouvements */}
            <div className="mt-3 space-y-2">
              {election.movements.map((movement) => (
                <div key={movement.id} className="flex items-center justify-between p-3 rounded-xl bg-background-light dark:bg-slate-800">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{movement.name}</span>
                  <div className="flex items-center gap-2">
                    {movement.status === 'PENDING' && (
                      <>
                        <Button variant="primary" size="sm" onClick={() => handleApproveMovement(election.id, movement.id)} icon={CheckCircle}>
                          Approuver
                        </Button>
                        <Button variant="secondary" size="sm" onClick={() => handleRejectMovement(election.id, movement.id)} icon={XCircle}>
                          Rejeter
                        </Button>
                      </>
                    )}
                    {movement.status === 'APPROVED' && <Badge variant="success">Approuvé</Badge>}
                    {movement.status === 'REJECTED' && <Badge variant="danger">Rejeté</Badge>}
                  </div>
                </div>
              ))}
              {election.movements.length === 0 && (
                <p className="text-sm text-gray-500">Aucun mouvement soumis pour cette élection.</p>
              )}
            </div>

            {/* Actions selon statut */}
            <div className="mt-4 flex items-center justify-end">
              {election.status === 'VOTING_CLOSED' && (
                <Button variant="primary" onClick={() => handleTallyResults(election.id)} icon={BarChart3}>
                  Tally Results
                </Button>
              )}
              {election.status !== 'VOTING_CLOSED' && (
                <span className="text-xs text-gray-400">Le dépouillement sera disponible après la clôture du vote.</span>
              )}
            </div>
          </Card>
        ))}
      </div>

      {/* Modale de création */}
      <AnimatePresence>
        {showCreateModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
            onClick={() => setShowCreateModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 20 }}
              className="bg-white dark:bg-slate-900 rounded-2xl p-6 w-full max-w-lg shadow-neo-extruded dark:shadow-neo-dark-extruded"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Créer une élection</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Titre</label>
                  <input
                    type="text"
                    value={newElection.title}
                    onChange={(e) => setNewElection({ ...newElection, title: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-pineapple"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Type</label>
                  <select
                    value={newElection.type}
                    onChange={(e) => setNewElection({ ...newElection, type: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-pineapple"
                  >
                    <option value="BDE">BDE</option>
                    <option value="Délégué">Délégué</option>
                    <option value="Autre">Autre</option>
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Début</label>
                    <input
                      type="datetime-local"
                      value={newElection.startDate}
                      onChange={(e) => setNewElection({ ...newElection, startDate: e.target.value })}
                      className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-pineapple"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Fin</label>
                    <input
                      type="datetime-local"
                      value={newElection.endDate}
                      onChange={(e) => setNewElection({ ...newElection, endDate: e.target.value })}
                      className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-pineapple"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Règles d'éligibilité (filières/niveaux)</label>
                  <textarea
                    value={newElection.filieres.join(', ')}
                    onChange={(e) => setNewElection({ ...newElection, filieres: e.target.value.split(',').map(s => s.trim()) })}
                    rows={3}
                    className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-slate-800 border border-white/20 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-pineapple"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <Button variant="secondary" onClick={() => setShowCreateModal(false)}>Annuler</Button>
                <Button variant="primary" onClick={handleCreateElection} icon={Plus}>Créer</Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};