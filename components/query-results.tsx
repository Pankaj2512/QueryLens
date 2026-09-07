'use client';

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';

interface QueryResultsProps {
  results: {
    columns: string[];
    data: Record<string, any>[];
    row_count: number;
    limit?: number;
    offset?: number;
    has_more?: boolean;
  };
  onLoadMore?: () => void;
  loadingMore?: boolean;
}

export default function QueryResults({ results, onLoadMore, loadingMore = false }: QueryResultsProps) {
  if (!results.data || results.data.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <p className="text-muted-foreground">No results found</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Results</CardTitle>
        <CardDescription>
          {results.row_count} rows returned
          {typeof results.offset === 'number' && typeof results.limit === 'number'
            ? ` (offset ${results.offset}, page size ${results.limit})`
            : ''}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ScrollArea className="w-full">
          <Table className="w-full text-sm">
            <TableHeader>
              <TableRow className="border-b border-border">
                {results.columns.map((col) => (
                  <TableHead key={col} className="whitespace-nowrap px-4 py-2 font-semibold">
                    {col}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {results.data.map((row, idx) => (
                <TableRow key={idx} className="border-b border-border hover:bg-muted/50">
                  {results.columns.map((col) => (
                    <TableCell key={`${idx}-${col}`} className="whitespace-nowrap px-4 py-2">
                      <code className="rounded bg-muted px-2 py-1 font-mono text-xs text-foreground">
                        {String(row[col] ?? 'NULL')}
                      </code>
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </ScrollArea>
        {results.has_more && onLoadMore && (
          <div className="mt-4 flex justify-end">
            <Button onClick={onLoadMore} disabled={loadingMore} variant="outline" size="sm">
              {loadingMore ? 'Loading...' : 'Load more'}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
