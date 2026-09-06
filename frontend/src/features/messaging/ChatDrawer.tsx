// frontend/src/features/messaging/ChatDrawer.tsx

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Send, Paperclip, Info } from 'lucide-react';
import { MessageBubble, MessageData } from './MessageBubble';
import { cn } from '@/lib/utils';

interface ChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  contactName: string;
  contextLabel?: string; // ex: "Marketplace : iPhone 13"
  initialMessages?: MessageData[];
  currentUserId: string;
  onSendMessage?: (content: string) => void;
}

export const ChatDrawer: React.FC<ChatDrawerProps> = ({
  isOpen,
  onClose,
  contactName,
  contextLabel,
  initialMessages = [],
  currentUserId,
  onSendMessage,
}) => {
  const [messages, setMessages] = useState<MessageData[]>(initialMessages);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Scroll automatique vers le bas à chaque nouveau message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus sur le champ à l'ouverture
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [isOpen]);

  const handleSend = () => {
    const content = inputValue.trim();
    if (!content) return;

    const newMessage: MessageData = {
      id: `msg-${Date.now()}`,
      senderId: currentUserId,
      content,
      timestamp: new Date().toISOString(),
      status: 'sent',
    };

    setMessages((prev) => [...prev, newMessage]);
    setInputValue('');
    onSendMessage?.(content);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-end md:items-center md:justify-end bg-black/50 backdrop-blur-sm"
          onClick={onClose}
        >
          {/* Tiroir / Modale */}
          <motion.div
            initial={{ y: '100%', opacity: 0.5 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: '100%', opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className={cn(
              'w-full md:w-[420px] h-[85vh] md:h-[80vh] md:mr-4 md:mb-4',
              'bg-white dark:bg-slate-900 rounded-t-3xl md:rounded-3xl',
              'shadow-neo-extruded dark:shadow-neo-dark-extruded flex flex-col overflow-hidden'
            )}
            onClick={(e) => e.stopPropagation()}
          >
            {/* En-tête */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80">
              <div className="min-w-0">
                <h3 className="font-semibold text-gray-800 dark:text-white truncate">
                  {contactName}
                </h3>
                {contextLabel && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                    <Info className="inline h-3 w-3 mr-1" />
                    {contextLabel}
                  </p>
                )}
              </div>
              <button
                onClick={onClose}
                className="p-1 rounded-full hover:bg-pineapple/10"
                aria-label="Fermer"
              >
                <X className="h-5 w-5 text-gray-500" />
              </button>
            </div>

            {/* Zone des messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-background-light dark:bg-slate-950">
              {messages.length === 0 && (
                <div className="text-center text-gray-500 text-sm mt-8">
                  Aucun message. Commencez la discussion !
                </div>
              )}
              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} isOwn={msg.senderId === currentUserId} />
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Zone de saisie */}
            <div className="flex items-center gap-2 p-3 border-t border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900">
              <button className="p-2 rounded-full hover:bg-pineapple/10 text-gray-500">
                <Paperclip className="h-5 w-5" />
              </button>
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Écrivez un message..."
                className="flex-1 px-4 py-2 rounded-xl bg-background-light dark:bg-slate-800 border border-white/20 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-pineapple"
              />
              <button
                onClick={handleSend}
                disabled={!inputValue.trim()}
                className={cn(
                  'p-2 rounded-full bg-pineapple text-white disabled:opacity-50',
                  'hover:bg-emerald-600 transition-colors'
                )}
                aria-label="Envoyer"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};