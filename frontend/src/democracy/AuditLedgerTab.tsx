// frontend/src/features/democracy/AuditLedgerTab.tsx

import React from 'react';
import { motion } from 'framer-motion';
import { Card } from '@/components/ui/Card';
import { cn } from '@/lib/utils';

// ---------- Types ----------
interface AuditEntry {
  id: string;
  timestamp: string; // ISO string
  action: string;
  hash: string; // hash complet ou tronqué
}

// Données simulées (à remplacer par un appel API)
const mockAuditEntries: AuditEntry[] = [
  {
    id: 'a1',
    timestamp: '2027-03-15T08:00:00Z',
    action: 'Voting opened',
    hash: 'a3f9c2b1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9',
  },
  {
    id: 'a2',
    timestamp: '2027-03-15T08:05:12Z',
    action: 'Vote registered',
    hash: 'b7e2d3c4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c',
  },
  {
    id: 'a3',
    timestamp: '2027-03-15T08:12:45Z',
    action: 'Vote registered',
    hash: 'c4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2',
  },
  {
    id: 'a4',
    timestamp: '2027-03-15T08:20:03Z',
    action: 'Vote registered',
    hash: 'd9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1',
  },
  {
    id: 'a5',
    timestamp: '2027-03-15T18:00:00Z',
    action: 'Voting closed',
    hash: 'e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8',
  },
];

// Fonction utilitaire pour formater la date
function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString('fr-FR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

// Tronque le hash pour l'affichage
function truncateHash(hash: string, chars = 16): string {
  if (hash.length <= chars) return hash;
  return `${hash.substring(0, chars / 2)}...${hash.substring(hash.length - chars / 2)}`;
}

// ---------- Composant ----------
export const AuditLedgerTab: React.FC = () => {
  return (
    <Card variant="neo-extruded" className="p-4 md:p-6 overflow-x-auto">
      <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">
        Election Audit Ledger
      </h2>
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-gray-300 dark:border-slate-700">
            <th className="px-4 py-2 text-left font-medium text-gray-500 dark:text-gray-400">Horodatage</th>
            <th className="px-4 py-2 text-left font-medium text-gray-500 dark:text-gray-400">Action</th>
            <th className="px-4 py-2 text-left font-medium text-gray-500 dark:text-gray-400">Empreinte cryptographique</th>
          </tr>
        </thead>
        <tbody>
          {mockAuditEntries.map((entry) => (
            <tr
              key={entry.id}
              className={cn(
                'border-b border-gray-200 dark:border-slate-800 hover:bg-pineapple/5 transition-colors'
              )}
            >
              <td className="px-4 py-3 text-gray-700 dark:text-gray-300 font-mono text-xs">
                {formatDate(entry.timestamp)}
              </td>
              <td className="px-4 py-3 text-gray-800 dark:text-white font-medium">
                {entry.action}
              </td>
              <td className="px-4 py-3 text-gray-600 dark:text-gray-400 font-mono text-xs">
                {truncateHash(entry.hash)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
};