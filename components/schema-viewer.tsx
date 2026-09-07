'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';

interface Column {
  name: string;
  type: string;
}

interface SchemaViewerProps {
  tableName: string;
}

export default function SchemaViewer({ tableName }: SchemaViewerProps) {
  const [schema, setSchema] = useState<{ columns: Column[] } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSchema = async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/schema/${tableName}`
        );
        if (!res.ok) throw new Error('Failed to fetch schema');
        const data = await res.json();
        setSchema(data);
      } catch (error) {
        console.error('[v0] Schema fetch error:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSchema();
  }, [tableName]);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Table Schema</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (!schema) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Table Schema</CardTitle>
        <CardDescription>{schema.columns.length} columns</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {schema.columns.map((col) => (
            <div key={col.name} className="flex items-center justify-between rounded-lg bg-muted p-3">
              <span className="font-mono text-sm font-semibold text-foreground">{col.name}</span>
              <Badge variant="outline" className="font-mono text-xs">
                {col.type}
              </Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
