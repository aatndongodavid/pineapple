// frontend/src/features/auth/PineappleCard.tsx

import React, { useRef, useState } from 'react';
import { motion, useMotionValue, useTransform, useSpring } from 'framer-motion';
import { ShieldCheck, User, GraduationCap, IdCard, Building } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PineappleCardProps {
  firstName: string;
  lastName: string;
  matricule: string;
  faculty: string;
  filiere: string;
  academicYear: string;
  campusName: string;
  status: string; // "Étudiant certifié" etc.
  verificationUrl?: string;
  className?: string;
}

/**
 * Génère un QR code SVG simple (damier) basé sur un hash de la chaîne.
 * C'est une version de démonstration, remplaçable par une vraie librairie.
 */
function generateQRPattern(data: string, size = 21): boolean[][] {
  // Simple hash pour générer des bits pseudo-aléatoires
  let hash = 0;
  for (let i = 0; i < data.length; i++) {
    const chr = data.charCodeAt(i);
    hash = ((hash << 5) - hash) + chr;
    hash |= 0;
  }
  const grid: boolean[][] = [];
  for (let y = 0; y < size; y++) {
    const row: boolean[] = [];
    for (let x = 0; x < size; x++) {
      // Fonction pseudo-aléatoire
      const value = Math.sin(hash + x * 12.9898 + y * 78.233) * 43758.5453;
      const bit = (Math.abs(value) % 1) > 0.5;
      row.push(bit);
    }
    grid.push(row);
  }
  // Ajouter des carrés de positionnement grossiers (coins supérieur gauche, supérieur droit, inférieur gauche)
  for (let dy = 0; dy < 7; dy++) {
    for (let dx = 0; dx < 7; dx++) {
      if (dx < 7 && dy < 7) {
        const border = dx === 0 || dx === 6 || dy === 0 || dy === 6;
        grid[dy][dx] = border;
        grid[dy][size - 1 - dx] = border;
        grid[size - 1 - dy][dx] = border;
      }
    }
  }
  return grid;
}

export const PineappleCard: React.FC<PineappleCardProps> = ({
  firstName,
  lastName,
  matricule,
  faculty,
  filiere,
  academicYear,
  campusName,
  status,
  verificationUrl = `https://verify.pineapple.cm/student/${matricule}`,
  className,
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const rotateX = useSpring(useTransform(y, [-0.5, 0.5], [-8, 8]), { stiffness: 200, damping: 20 });
  const rotateY = useSpring(useTransform(x, [-0.5, 0.5], [8, -8]), { stiffness: 200, damping: 20 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width - 0.5;
    const py = (e.clientY - rect.top) / rect.height - 0.5;
    x.set(px);
    y.set(py);
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  const qrGrid = generateQRPattern(verificationUrl);

  return (
    <motion.div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{ rotateX, rotateY, transformStyle: 'preserve-3d' }}
      whileHover={{ scale: 1.02 }}
      className={cn(
        'relative w-full max-w-md mx-auto rounded-2xl p-6',
        'bg-gradient-to-br from-white/20 to-white/5 backdrop-blur-md border border-white/30 shadow-neo-extruded dark:shadow-neo-dark-extruded',
        className
      )}
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-800 dark:text-white">Carte Étudiant</h3>
          <p className="text-xs text-gray-500 dark:text-gray-400">Pineapple ID</p>
        </div>
        <ShieldCheck className="h-6 w-6 text-pineapple" />
      </div>

      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 space-y-3">
          <div className="flex items-center gap-2">
            <User className="h-5 w-5 text-pineapple" />
            <span className="font-medium text-gray-800 dark:text-white">
              {firstName} {lastName}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <IdCard className="h-5 w-5 text-pineapple" />
            <span className="text-sm text-gray-700 dark:text-gray-300">{matricule}</span>
          </div>
          <div className="flex items-center gap-2">
            <Building className="h-5 w-5 text-pineapple" />
            <span className="text-sm text-gray-700 dark:text-gray-300">{campusName}</span>
          </div>
          <div className="flex items-center gap-2">
            <GraduationCap className="h-5 w-5 text-pineapple" />
            <span className="text-sm text-gray-700 dark:text-gray-300">{faculty} - {filiere}</span>
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">Année : {academicYear}</div>
        </div>

        <div className="flex flex-col items-center justify-between">
          {/* QR Code */}
          <div className="w-24 h-24 bg-white rounded-lg p-1 shadow-inner">
            <svg viewBox={`0 0 21 21`} className="w-full h-full">
              {qrGrid.map((row, y) =>
                row.map((cell, x) =>
                  cell ? <rect key={`${x}-${y}`} x={x} y={y} width={1} height={1} fill="black" /> : null
                )
              )}
            </svg>
          </div>
          <span className="text-[10px] text-gray-500 mt-2">Vérification</span>
        </div>
      </div>

      {/* Badge certifié holographique */}
      <div className="mt-5 flex justify-center">
        <span
          className={cn(
            'inline-flex items-center px-4 py-1.5 rounded-full text-sm font-medium',
            'bg-gradient-to-r from-emerald-400/20 via-emerald-500/10 to-emerald-400/20 border border-emerald-300/50',
            'text-emerald-800 dark:text-emerald-200',
            'shadow-[0_0_15px_rgba(16,185,129,0.3)]'
          )}
        >
          <ShieldCheck className="h-4 w-4 mr-2" />
          {status}
        </span>
      </div>
    </motion.div>
  );
};