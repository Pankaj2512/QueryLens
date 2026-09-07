'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Spinner } from '@/components/ui/spinner';
import QueryResults from './query-results';

interface ChatInterfaceProps {
  tableName: string;
  onQuery: (query: string, tableName: string, execute?: boolean, offset?: number) => Promise<any>;
  loading: boolean;
}

interface Message {
  type: 'user' | 'assistant' | 'error';
  content: string;
  sql?: string;
  results?: any;
  query?: string;
  tableName?: string;
}

export default function ChatInterface({ tableName, onQuery, loading }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [localLoading, setLocalLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [loadingMoreForMessage, setLoadingMoreForMessage] = useState<number | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading || localLoading) return;

    const query = input.trim();
    setInput('');
    setLocalLoading(true);

    // Add user message
    setMessages((prev) => [...prev, { type: 'user', content: query }]);

    try {
      console.log('[v0] Executing query:', query);
      const result = await onQuery(query, tableName, true, 0);
      
      if (result.success) {
        setMessages((prev) => [
          ...prev,
          {
            type: 'assistant',
            content: `Generated SQL and executed successfully. Found ${result.results?.row_count || 0} rows.`,
            sql: result.sql,
            results: result.results,
            query,
            tableName,
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            type: 'error',
            content: result.error || 'Failed to execute query',
            sql: result.sql,
          },
        ]);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      console.error('[v0] Query error:', error);
      setMessages((prev) => [
        ...prev,
        {
          type: 'error',
          content: errorMessage,
        },
      ]);
    } finally {
      setLocalLoading(false);
    }
  };

  const handleLoadMore = async (messageIndex: number) => {
    const message = messages[messageIndex];
    if (!message?.query || !message?.tableName || !message.results?.has_more) return;

    setLoadingMoreForMessage(messageIndex);
    try {
      const nextOffset = Number(message.results.offset || 0) + Number(message.results.limit || 100);
      const result = await onQuery(message.query, message.tableName, true, nextOffset);
      if (!result.success || !result.results) return;

      setMessages((prev) =>
        prev.map((msg, idx) => {
          if (idx !== messageIndex || !msg.results) return msg;
          const existingData = Array.isArray(msg.results.data) ? msg.results.data : [];
          const incomingData = Array.isArray(result.results.data) ? result.results.data : [];
          return {
            ...msg,
            content: `Generated SQL and executed successfully. Found ${existingData.length + incomingData.length} rows.`,
            results: {
              ...result.results,
              data: [...existingData, ...incomingData],
              row_count: existingData.length + incomingData.length,
            },
          };
        })
      );
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      setMessages((prev) => [...prev, { type: 'error', content: errorMessage }]);
    } finally {
      setLoadingMoreForMessage(null);
    }
  };

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle>Query Builder</CardTitle>
        <CardDescription>Ask a question about your data in natural language</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col gap-4">
        {/* Messages */}
        <div className="flex h-96 flex-col gap-3 overflow-y-auto rounded-lg bg-muted/30 p-4">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center text-center">
              <div>
                <p className="text-sm text-muted-foreground">Start by asking a question about your data</p>
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => (
                <div key={idx} className="space-y-2">
                  <div className={`rounded-lg p-3 ${
                    msg.type === 'user'
                      ? 'ml-auto bg-primary text-primary-foreground'
                      : msg.type === 'error'
                      ? 'bg-destructive/10 text-destructive'
                      : 'bg-card border border-border'
                  } max-w-xs`}>
                    <p className="text-sm">{msg.content}</p>
                  </div>
                  {msg.sql && (
                    <div className="ml-0 rounded-lg bg-muted p-3">
                      <p className="mb-2 text-xs font-semibold text-muted-foreground">Generated SQL:</p>
                      <code className="block overflow-auto font-mono text-xs text-foreground">
                        {msg.sql}
                      </code>
                    </div>
                  )}
                  {msg.results && (
                    <div className="ml-0">
                      <QueryResults
                        results={msg.results}
                        onLoadMore={msg.results?.has_more ? () => handleLoadMore(idx) : undefined}
                        loadingMore={loadingMoreForMessage === idx}
                      />
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="space-y-3">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="What do you want to know? E.g., 'Show me all records from 2024'"
            disabled={loading || localLoading}
            rows={3}
            className="resize-none"
          />
          <Button
            type="submit"
            disabled={!input.trim() || loading || localLoading}
            className="w-full"
          >
            {localLoading ? (
              <>
                <Spinner className="mr-2 h-4 w-4" />
                Analyzing...
              </>
            ) : (
              <>
                <Send className="mr-2 h-4 w-4" />
                Send Query
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
