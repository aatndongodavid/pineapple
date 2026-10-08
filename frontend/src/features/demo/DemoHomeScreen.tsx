import React from 'react';

export const DemoHomeScreen: React.FC = () => {
  return (
    <div className="p-6 md:p-8 bg-slate-950 min-h-screen text-slate-100 space-y-8 font-sans">
      {/* Welcome Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-slate-800 p-8 border border-slate-800 shadow-xl">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 font-semibold text-xs mb-4">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
            Établissement Démo Pineapple 🇨🇲 — Bac à Sable Interactif
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white mb-3">
            Tableau de Bord — Établissement Démo
          </h1>
          <p className="text-sm text-slate-300 leading-relaxed">
            Consultez les registres d'étudiants, les emplois du temps dynamiques, la détection des conflits de salles et les déclarations d'occupation des délégués.
          </p>
        </div>
      </div>

      {/* Core Pillars Overview (Matching Website) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Pillar 1: Scolarité & Registres */}
        <div className="bg-slate-900 rounded-2xl p-6 border border-slate-800 shadow-lg hover:border-amber-500/50 transition-all">
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center text-xl font-bold mb-4">
            🎓
          </div>
          <span className="text-xs uppercase font-extrabold text-amber-400 tracking-wider block mb-1">Effectifs Chargés</span>
          <h3 className="text-lg font-extrabold text-white mb-2">Scolarité & Registres</h3>
          <p className="text-xs text-slate-400 leading-relaxed mb-4">
            60 étudiants pré-chargés sur 4 promotions (L1, L2, L3, M1). Importation CSV et matricules officiels.
          </p>
          <div className="flex items-center justify-between text-xs font-bold pt-4 border-t border-slate-800">
            <span className="text-emerald-400">✓ 60 Registres Valides</span>
            <span className="text-slate-500">0 Doublon</span>
          </div>
        </div>

        {/* Pillar 2: Planning & Salles Intelligentes */}
        <div className="bg-slate-900 rounded-2xl p-6 border border-slate-800 shadow-lg hover:border-amber-500/50 transition-all">
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center text-xl font-bold mb-4">
            🏫
          </div>
          <span className="text-xs uppercase font-extrabold text-amber-400 tracking-wider block mb-1">Occupation Amphis</span>
          <h3 className="text-lg font-extrabold text-white mb-2">Planning & Salles Intelligentes</h3>
          <p className="text-xs text-slate-400 leading-relaxed mb-4">
            8 salles et amphis suivis en temps réel avec détection automatique des collisions de créneaux.
          </p>
          <div className="flex items-center justify-between text-xs font-bold pt-4 border-t border-slate-800">
            <span className="text-amber-400">87.5% Taux Occupation</span>
            <span className="text-emerald-400">0 Collisions</span>
          </div>
        </div>

        {/* Pillar 3: Espace Délégués & Élections */}
        <div className="bg-slate-900 rounded-2xl p-6 border border-slate-800 shadow-lg hover:border-amber-500/50 transition-all">
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center text-xl font-bold mb-4">
            🗳️
          </div>
          <span className="text-xs uppercase font-extrabold text-amber-400 tracking-wider block mb-1">Remontée Terrain</span>
          <h3 className="text-lg font-extrabold text-white mb-2">Espace Délégués & Élections</h3>
          <p className="text-xs text-slate-400 leading-relaxed mb-4">
            Déclarations d'occupation ou de libération d'amphis transmises en direct par les délégués titulaires.
          </p>
          <div className="flex items-center justify-between text-xs font-bold pt-4 border-t border-slate-800">
            <span className="text-emerald-400">12 Signalements Actifs</span>
            <span className="text-slate-400">4 Délégués</span>
          </div>
        </div>
      </div>

      {/* Real-Time Timetable & Room Status Section */}
      <div className="bg-slate-900 rounded-2xl p-6 border border-slate-800 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-extrabold text-white">📅 Emplois du Temps & Salles — Aujourd'hui</h2>
            <p className="text-xs text-slate-400">Planning de la journée pour l'Établissement Démo Pineapple</p>
          </div>
          <div className="flex gap-2">
            <span className="px-3 py-1 rounded-lg bg-slate-800 text-xs font-bold text-amber-400 border border-slate-700">
              L3 Informatique
            </span>
            <span className="px-3 py-1 rounded-lg bg-emerald-500/10 text-xs font-bold text-emerald-400 border border-emerald-500/30">
              ✓ Synchronisé Offline (PWA)
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          {/* Room Card 1 */}
          <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-extrabold text-sm text-white">Amphi A (Capacité 250)</span>
              <span className="px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-400 font-extrabold">OCCUPÉ</span>
            </div>
            <p className="text-slate-300 font-medium">Cours : INF301 — Algorithmique Avancée</p>
            <div className="flex justify-between text-slate-400">
              <span>🕒 08:00 - 10:00</span>
              <span>👨‍🏫 Dr. Fouda</span>
            </div>
            <div className="pt-2 border-t border-slate-800/80 text-[11px] text-emerald-400 font-semibold">
              📢 Délégué Jean-Pierre Eboa : « Amphi occupé par L3 INF »
            </div>
          </div>

          {/* Room Card 2 */}
          <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-extrabold text-sm text-white">Amphi B (Capacité 200)</span>
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-extrabold">LIBÉRÉ</span>
            </div>
            <p className="text-slate-300 font-medium">Cours : INF303 — Réseaux IP (Terminé à 09:30)</p>
            <div className="flex justify-between text-slate-400">
              <span>🕒 10:15 - 12:15</span>
              <span>👨‍🏫 Prof. Biya</span>
            </div>
            <div className="pt-2 border-t border-slate-800/80 text-[11px] text-emerald-400 font-semibold">
              📢 Déléguée Marie-Thérèse Mbida : « Salle libérée par l'enseignant »
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
