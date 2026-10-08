// frontend/src/features/feed/VisitorFeed.tsx

import React, { useEffect, useState } from 'react';
import { Building2, Sparkles, ExternalLink, RefreshCw } from 'lucide-react';
import apiClient from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';

interface AdCreative {
  id: string;
  title: string;
  body: string;
  image_url: string;
  target_url: string;
  advertiser_name: string;
}

export const VisitorFeed: React.FC = () => {
  const [ads, setAds] = useState<AdCreative[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAds = async () => {
    setLoading(true);
    try {
      const resp = await apiClient.get(API_ENDPOINTS.ads.feed);
      setAds(resp.data);
      // Enregistrer les impressions
      resp.data.forEach((ad: AdCreative) => {
        apiClient.post(API_ENDPOINTS.ads.events, {
          ad_id: ad.id,
          event_type: 'IMPRESSION',
        }).catch(() => {});
      });
    } catch (err) {
      console.error('Erreur chargement pubs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAds();
  }, []);

  const handleAdClick = (ad: AdCreative) => {
    apiClient.post(API_ENDPOINTS.ads.events, {
      ad_id: ad.id,
      event_type: 'CLICK',
    }).catch(() => {});
    if (ad.target_url) {
      window.open(ad.target_url, '_blank');
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6 p-4">
      {/* Banner permanent pour rejoindre un établissement */}
      <div className="bg-gradient-to-r from-amber-500 to-orange-600 rounded-2xl p-6 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10 space-y-3">
          <div className="inline-flex items-center gap-2 bg-white/20 backdrop-blur-md px-3 py-1 rounded-full text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" /> Compte Visiteur
          </div>
          <h2 className="text-2xl font-bold">Débloquez vos outils de campus</h2>
          <p className="text-amber-100 text-sm">
            Rattachez-vous à votre établissement (école / université) pour accéder aux salles libres, délégués, annonces, cours et élections.
          </p>
          <a
            href="/join-school"
            className="inline-flex items-center gap-2 bg-white text-orange-600 font-bold px-5 py-2.5 rounded-xl hover:bg-amber-50 transition shadow-lg text-sm"
          >
            <Building2 className="w-4 h-4" /> Rejoindre mon établissement
          </a>
        </div>
      </div>

      {/* Header Fil de pub */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
          Fil d'actualité partenaires
        </h3>
        <button
          onClick={fetchAds}
          className="p-2 text-gray-500 hover:text-amber-500 transition rounded-lg"
          title="Rafraîchir"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Cartes publicitaires */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div key={i} className="h-64 bg-gray-200 dark:bg-gray-800 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : ads.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <p className="text-gray-500">Aucune publicité disponible pour le moment.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {ads.map((ad) => (
            <div
              key={ad.id}
              onClick={() => handleAdClick(ad)}
              className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm hover:shadow-md transition cursor-pointer group"
            >
              {ad.image_url && (
                <img
                  src={ad.image_url}
                  alt={ad.title}
                  className="w-full h-48 object-cover group-hover:scale-[1.01] transition duration-300"
                />
              )}
              <div className="p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold px-2 py-0.5 bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300 rounded uppercase tracking-wider">
                    Sponsorisé • {ad.advertiser_name}
                  </span>
                  <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-amber-500 transition" />
                </div>
                <h4 className="text-lg font-bold text-gray-900 dark:text-white group-hover:text-amber-500 transition">
                  {ad.title}
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  {ad.body}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
