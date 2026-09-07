'use client';

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';

interface QueryResultsProps {
  results: {
    columns: string[];
    data: Record<string, any>[];
    row_count: number;
    limit?: number;
    offset?: number;
    has_more?: boolean;
  };
  tableName?: string;
  onLoadMore?: () => void;
  loadingMore?: boolean;
}

export default function QueryResults({ results, tableName, onLoadMore, loadingMore = false }: QueryResultsProps) {
  const downloadCsv = () => {
    if (!results.data || results.data.length === 0) return;
    const headers = results.columns.join(',');
    const rows = results.data.map(row => 
      results.columns.map(col => {
        const val = row[col] ?? '';
        return `"${String(val).replace(/"/g, '""')}"`;
      }).join(',')
    );
    const csvContent = "data:text/csv;charset=utf-8," + encodeURIComponent([headers, ...rows].join('\n'));
    const link = document.createElement("a");
    link.setAttribute("href", csvContent);
    link.setAttribute("download", `${tableName || 'query_results'}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const downloadJson = () => {
    if (!results.data || results.data.length === 0) return;
    const jsonContent = "data:application/json;charset=utf-8," + encodeURIComponent(JSON.stringify(results.data, null, 2));
    const link = document.createElement("a");
    link.setAttribute("href", jsonContent);
    link.setAttribute("download", `${tableName || 'query_results'}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

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
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <div>
          <CardTitle className="text-base">Results</CardTitle>
          <CardDescription>
            {results.row_count} rows returned
            {typeof results.offset === 'number' && typeof results.limit === 'number'
              ? ` (offset ${results.offset}, page size ${results.limit})`
              : ''}
          </CardDescription>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={downloadCsv} className="h-7 gap-1 px-2 text-xs">
            <Download className="h-3.5 w-3.5" />
            CSV
          </Button>
          <Button variant="outline" size="sm" onClick={downloadJson} className="h-7 gap-1 px-2 text-xs">
            <Download className="h-3.5 w-3.5" />
            JSON
          </Button>
        </div>
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
