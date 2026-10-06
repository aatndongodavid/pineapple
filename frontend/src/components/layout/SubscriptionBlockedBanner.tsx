// frontend/src/components/layout/SubscriptionBlockedBanner.tsx

import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { useAuthStore } from '@/lib/store/authStore';

export const SubscriptionBlockedBanner: React.FC = () => {
  const { subscriptionState, tenant } = useAuthStore();

  if (subscriptionState !== 'EXPIRED' && subscriptionState !== 'SUSPENDED') {
    return null;
  }

  return (
    <div className="bg-amber-500 text-white px-4 py-3 shadow-md flex items-center justify-between text-sm font-medium">
      <div className="flex items-center gap-3 max-w-5xl mx-auto">
        <AlertTriangle className="w-5 h-5 shrink-0" />
        <span>
          L'abonnement de <strong>{tenant?.name || "votre établissement"}</strong> a expiré. Votre compte est actuellement en <strong>lecture seule</strong>.
        </span>
      </div>
    </div>
  );
};
