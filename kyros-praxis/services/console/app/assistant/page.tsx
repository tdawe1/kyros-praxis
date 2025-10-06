'use client';

import { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import {
  Button,
  TextArea,
  Layer,
  Tile,
  InlineNotification,
} from '@carbon/react';
import {
  Send,
  Bot,
} from '@carbon/icons-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const sendMessage = useMutation({
    mutationFn: async (content: string) => {
      const response = await fetch('/api/v1/assistant/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content }),
      });
      if (!response.ok) {
        throw new Error('Failed to send message');
      }
      return response.json();
    },
    onSuccess: (data) => {
      setMessages(prev => [...prev, {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
      }]);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);
    
    // Send to AI assistant
    sendMessage.mutate(input);
    setInput('');
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="cds--content" data-testid="assistant-page">
      <div style={{ maxWidth: '800px', margin: '0 auto', height: 'calc(100vh - 200px)', display: 'flex', flexDirection: 'column' }}>
        <div style={{ marginBottom: '1rem' }}>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Bot size={32} />
            AI Assistant
          </h1>
          <p style={{ color: 'var(--cds-text-secondary)' }}>
            Chat with your AI assistant for help with tasks and questions
          </p>
        </div>

        {/* Messages */}
        <div style={{ 
          flex: 1, 
          overflowY: 'auto', 
          border: '1px solid var(--cds-border-subtle)', 
          borderRadius: '8px',
          padding: '1rem',
          marginBottom: '1rem',
          backgroundColor: 'var(--cds-field-01)'
        }}>
          {messages.length === 0 ? (
            <div style={{ textAlign: 'center', color: 'var(--cds-text-secondary)', padding: '2rem' }}>
              <Bot size={48} style={{ marginBottom: '1rem' }} />
              <p>Start a conversation with your AI assistant</p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                style={{
                  marginBottom: '1rem',
                  padding: '0.75rem',
                  borderRadius: '8px',
                  backgroundColor: message.role === 'user' 
                    ? 'var(--cds-interactive-01)' 
                    : 'var(--cds-field-02)',
                  color: message.role === 'user' 
                    ? 'white' 
                    : 'var(--cds-text-primary)',
                  marginLeft: message.role === 'user' ? '25%' : '0',
                  marginRight: message.role === 'assistant' ? '25%' : '0',
                }}
              >
                <div style={{ fontSize: '0.875rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>
                  {message.role === 'user' ? 'You' : 'Assistant'}
                </div>
                <div>{message.content}</div>
                <div style={{ fontSize: '0.75rem', opacity: 0.7, marginTop: '0.25rem' }}>
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem' }}>
          <TextArea
            labelText=""
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message here..."
            rows={2}
            style={{ flex: 1 }}
            disabled={sendMessage.isPending}
          />
          <Button
            type="submit"
            renderIcon={Send}
            disabled={!input.trim() || sendMessage.isPending}
            data-testid="send-message"
          >
            {sendMessage.isPending ? 'Sending...' : 'Send'}
          </Button>
        </form>

        {sendMessage.isError && (
          <InlineNotification
            kind="error"
            title="Failed to send message"
            subtitle={sendMessage.error?.message}
            style={{ marginTop: '1rem' }}
          />
        )}
      </div>
    </div>
  );
}