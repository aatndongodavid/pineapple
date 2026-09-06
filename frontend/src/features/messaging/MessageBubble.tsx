// frontend/src/features/messaging/MessageBubble.tsx

import React from 'react';
import { motion } from 'framer-motion';
import { Check, CheckCheck } from 'lucide-react';
import { cn } from '@/lib/utils';

export type MessageStatus = 'sending' | 'sent' | 'delivered' | 'read';

export interface MessageData {
  id: string;
  senderId: string;
  content: string;
  timestamp: string; // ISO
  status?: MessageStatus;
}

interface MessageBubbleProps {
  message: MessageData;
  isOwn: boolean;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message, isOwn }) => {
  const time = new Date(message.timestamp).toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn('flex w-full', isOwn ? 'justify-end' : 'justify-start')}
    >
      <div
        className={cn(
          'max-w-[80%] px-4 py-2 rounded-2xl shadow-sm',
          isOwn
            ? 'bg-pineapple text-white rounded-br-md'
            : 'bg-white dark:bg-slate-800 text-gray-800 dark:text-gray-200 rounded-bl-md'
        )}
      >
        <p className="text-sm break-words">{message.content}</p>
        <div
          className={cn(
            'flex items-center gap-1 mt-1 text-xs',
            isOwn ? 'text-white/70' : 'text-gray-400'
          )}
        >
          <span>{time}</span>
          {isOwn && message.status && (
            <span>
              {message.status === 'read' ? (
                <CheckCheck className="h-3.5 w-3.5" />
              ) : (
                <Check className="h-3.5 w-3.5" />
              )}
            </span>
          )}
        </div>
      </div>
    </motion.div>
  );
};