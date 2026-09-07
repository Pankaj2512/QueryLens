import { useState, useEffect, useCallback } from 'react';
import {
  GEMINI_DEFAULT_MODEL,
  loadGeminiSettingsFromStorage,
  persistGeminiApiKey,
  persistGeminiModel,
} from '@/lib/gemini-settings';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface QueryHistoryItem {
  id?: number;
  naturalLanguage: string;
  generatedSql: string;
  tableName: string;
  executed: boolean;
  error?: string;
  createdAt?: string;
}

function getErrorMessage(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== 'object') return fallback;

  const obj = payload as Record<string, unknown>;

  if (typeof obj.detail === 'string') return obj.detail;
  if (typeof obj.message === 'string') return obj.message;

  const errorObj = obj.error;
  if (errorObj && typeof errorObj === 'object') {
    const nested = errorObj as Record<string, unknown>;
    if (typeof nested.message === 'string') return nested.message;
    if (typeof nested.code === 'string') return nested.code;
    if (Array.isArray(nested.details) && nested.details.length > 0) {
      const first = nested.details[0];
      if (first && typeof first === 'object') {
        const detail = first as Record<string, unknown>;
        if (typeof detail.message === 'string') return detail.message;
      }
    }
  }

  if (Array.isArray(obj.detail)) {
    const first = obj.detail[0];
    if (first && typeof first === 'object') {
      const detailObj = first as Record<string, unknown>;
      if (typeof detailObj.msg === 'string') return detailObj.msg;
      if (typeof detailObj.message === 'string') return detailObj.message;
    }
  }

  return fallback;
}

export function useQueryLens() {
  const [tables, setTables] = useState<string[]>([]);
  const [selectedTable, setSelectedTable] = useState<string>('');
  const [queryHistory, setQueryHistory] = useState<QueryHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [geminiApiKey, setGeminiApiKeyState] = useState('');
  const [geminiModel, setGeminiModelState] = useState(GEMINI_DEFAULT_MODEL);

  useEffect(() => {
    const { apiKey, model } = loadGeminiSettingsFromStorage();
    setGeminiApiKeyState(apiKey);
    setGeminiModelState(model);
  }, []);

  const setGeminiApiKey = useCallback((value: string) => {
    setGeminiApiKeyState(value);
    persistGeminiApiKey(value);
  }, []);

  const setGeminiModel = useCallback((value: string) => {
    const next = value.trim() || GEMINI_DEFAULT_MODEL;
    setGeminiModelState(next);
    persistGeminiModel(value);
  }, []);

  // Load tables on mount
  useEffect(() => {
    fetchTables();
  }, []);

  const fetchTables = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/tables`);
      if (!res.ok) throw new Error('Failed to fetch tables');
      const data = await res.json();
      setTables(data.tables || []);
      if (data.tables?.length > 0 && !selectedTable) {
        setSelectedTable(data.tables[0]);
      }
    } catch (error) {
      console.error('Error fetching tables:', error);
    }
  }, [selectedTable]);

  const fetchHistory = useCallback(async (tableName?: string) => {
    try {
      const params = new URLSearchParams({ limit: '100' });
      if (tableName) params.set('table_name', tableName);
      const res = await fetch(`${API_BASE}/history?${params.toString()}`);
      if (!res.ok) throw new Error('Failed to fetch history');
      const data = await res.json();
      const mapped = (data.history || []).map((item: Record<string, unknown>) => ({
        id: typeof item.id === 'number' ? item.id : undefined,
        naturalLanguage: String(item.natural_language || ''),
        generatedSql: String(item.generated_sql || ''),
        tableName: String(item.table_name || ''),
        executed: Boolean(item.executed),
        error: typeof item.error === 'string' ? item.error : undefined,
        createdAt: typeof item.created_at === 'string' ? item.created_at : undefined,
      }));
      setQueryHistory(mapped);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  }, []);

  const uploadFile = useCallback(async (file: File) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(getErrorMessage(error, 'Upload failed'));
      }

      const data = await res.json();
      console.log('[v0] File uploaded:', data);
      
      // Refresh tables
      await fetchTables();
      
      return data;
    } catch (error) {
      console.error('[v0] Upload error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [fetchTables]);

  const createTable = useCallback(async (tableData: { name: string; columns: Array<{ name: string; type: string }> }) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/create-table`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tableData),
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(getErrorMessage(error, 'Table creation failed'));
      }

      const data = await res.json();
      console.log('[v0] Table created:', data);
      
      // Refresh tables
      await fetchTables();
      
      return data;
    } catch (error) {
      console.error('[v0] Create table error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [fetchTables]);

  const executeQuery = useCallback(
    async (naturalLanguage: string, tableName: string, execute: boolean = true, offset: number = 0) => {
      setLoading(true);
      try {
        const body: Record<string, unknown> = {
          query: naturalLanguage,
          table_name: tableName,
          execute,
          limit: 100,
          offset,
        };
        const key = geminiApiKey.trim();
        const model = geminiModel.trim();
        if (key) body.gemini_api_key = key;
        if (model) body.gemini_model = model;

        const res = await fetch(`${API_BASE}/query`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });

        if (!res.ok) {
          const error = await res.json();
          throw new Error(getErrorMessage(error, 'Query failed'));
        }

        const data = await res.json();
        
        if (offset === 0) {
          // Add latest query to local history view; canonical history comes from /history.
          setQueryHistory((prev) => [
            {
              naturalLanguage,
              generatedSql: data.sql,
              tableName,
              executed: execute && data.success,
              error: !data.success ? data.error : undefined,
            },
            ...prev,
          ]);
        }

        return data;
      } catch (error) {
        console.error('[v0] Query error:', error);
        if (offset === 0) {
          setQueryHistory((prev) => [
            {
              naturalLanguage,
              generatedSql: '',
              tableName,
              executed: false,
              error: error instanceof Error ? error.message : 'Unknown error',
            },
            ...prev,
          ]);
        }
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [geminiApiKey, geminiModel]
  );

  useEffect(() => {
    fetchHistory(selectedTable || undefined);
  }, [selectedTable, fetchHistory]);

  return {
    tables,
    selectedTable,
    setSelectedTable,
    queryHistory,
    loading,
    geminiApiKey,
    setGeminiApiKey,
    geminiModel,
    setGeminiModel,
    uploadFile,
    createTable,
    executeQuery,
    refreshHistory: () => fetchHistory(selectedTable || undefined),
  };
}

export const useQueryForge = useQueryLens;
