// frontend/src/lib/store/tenantStore.ts

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface TenantState {
  tenantId: string | null;
  campusName: string | null;
  setTenant: (tenantId: string, campusName?: string) => void;
  clearTenant: () => void;
}

export const useTenantStore = create<TenantState>()(
  persist(
    (set) => ({
      tenantId: null,
      campusName: null,
      setTenant: (tenantId, campusName) => set({ tenantId, campusName }),
      clearTenant: () => set({ tenantId: null, campusName: null }),
    }),
    {
      name: 'pineapple-tenant-storage', // clé localStorage
    }
  )
);