// frontend/src/shared/services/offlineQueueService.ts

export interface PendingAction {
  id: string;
  type: 'POST_CREATE' | 'MESSAGE_SEND';
  url: string;
  payload: any;
  timestamp: number;
}

const DB_NAME = 'PineappleOfflineDB';
const STORE_NAME = 'pendingActions';

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id' });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function enqueueOfflineAction(action: Omit<PendingAction, 'id' | 'timestamp'>): Promise<string> {
  const db = await openDB();
  const id = `action_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const item: PendingAction = {
    ...action,
    id,
    timestamp: Date.now(),
  };

  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const req = store.add(item);
    req.onsuccess = () => resolve(id);
    req.onerror = () => reject(req.error);
  });
}

export async function getPendingActions(): Promise<PendingAction[]> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const req = store.getAll();
    req.onsuccess = () => resolve(req.result || []);
    req.onerror = () => reject(req.error);
  });
}

export async function removePendingAction(id: string): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const req = store.delete(id);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

export async function flushOfflineQueue(token: string, tenantId: string): Promise<number> {
  const pending = await getPendingActions();
  let count = 0;

  for (const action of pending) {
    try {
      const res = await fetch(action.url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
        },
        body: JSON.stringify(action.payload),
      });

      if (res.ok) {
        await removePendingAction(action.id);
        count++;
      }
    } catch (err) {
      console.warn(`[OfflineQueue] Failed to sync action ${action.id}:`, err);
    }
  }

  return count;
}
