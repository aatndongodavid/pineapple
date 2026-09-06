// frontend/src/components/layout/MainLayout.tsx

import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { MobileNav } from './MobileNav';
import { OfflineBanner } from '@/components/pwa/OfflineBanner';
import { ChatDrawer } from '@/features/messaging/ChatDrawer';
import { useMessagingStore } from '@/lib/store/messagingStore';
import { useAuthStore } from '@/lib/store/authStore';

export const MainLayout: React.FC = () => {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const activeConversationId = useMessagingStore((state) => state.activeConversationId);
  const conversations = useMessagingStore((state) => state.conversations);
  const currentUser = useAuthStore((state) => state.user);

  // Retrouve la conversation active pour le ChatDrawer
  const activeConversation = conversations.find(
    (conv) => conv.id === activeConversationId
  );

  return (
    <div className="min-h-screen flex bg-background-light dark:bg-background-dark">
      {/* Barre latérale visible uniquement sur desktop */}
      <Sidebar />

      {/* Contenu principal */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header avec callback pour ouvrir la messagerie */}
        <Header onChatClick={() => setIsChatOpen(true)} />

        {/* Zone de contenu avec padding adapté (mobile / desktop) */}
        <main className="flex-1 overflow-y-auto pb-20 md:pb-8 px-4 md:px-6 pt-4 md:pt-6">
          <Outlet />
        </main>
      </div>

      {/* Navigation mobile basse */}
      <MobileNav />

      {/* Bandeau hors‑ligne */}
      <OfflineBanner />

      {/* Tiroir de messagerie, rendu uniquement si une conversation est active */}
      {activeConversation && (
        <ChatDrawer
          isOpen={isChatOpen}
          onClose={() => setIsChatOpen(false)}
          contactName={activeConversation.contactName || 'Conversation'}
          contextLabel={activeConversation.contextLabel}
          currentUserId={currentUser?.id || ''}
          // Les messages sont récupérés par le store, on ne les passe pas ici
          initialMessages={[]}
        />
      )}
    </div>
  );
};