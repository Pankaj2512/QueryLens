'use client';

import { useState } from 'react';
import { Trash2, Plus, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FieldGroup, FieldLabel } from '@/components/ui/field';
import { Card, CardContent } from '@/components/ui/card';
import { toast } from '@/hooks/use-toast';

const SQL_TYPES = ['TEXT', 'INTEGER', 'REAL', 'BOOLEAN', 'DATE'];

interface Column {
  id: string;
  name: string;
  type: string;
}

interface Row {
  id: string;
  values: Record<string, string>;
}

interface ManualTableBuilderProps {
  onCreateTable: (tableData: { name: string; columns: Array<{ name: string; type: string }> }) => Promise<void>;
  loading: boolean;
}

export default function ManualTableBuilder({ onCreateTable, loading }: ManualTableBuilderProps) {
  const [tableName, setTableName] = useState('');
  const [columns, setColumns] = useState<Column[]>([
    { id: '1', name: 'id', type: 'INTEGER' },
    { id: '2', name: 'name', type: 'TEXT' },
  ]);
  const [rows, setRows] = useState<Row[]>([{ id: '1', values: {} }]);
  const [nextColId, setNextColId] = useState(3);
  const [nextRowId, setNextRowId] = useState(2);

  const addColumn = () => {
    const newId = String(nextColId);
    setColumns([...columns, { id: newId, name: `column_${newId}`, type: 'TEXT' }]);
    setNextColId(nextColId + 1);
    
    // Add empty value for new column in all rows
    setRows(
      rows.map((row) => ({
        ...row,
        values: { ...row.values, [newId]: '' },
      }))
    );
  };

  const removeColumn = (id: string) => {
    if (columns.length === 1) {
      toast({ description: 'You must have at least one column', variant: 'destructive' });
      return;
    }
    
    setColumns(columns.filter((col) => col.id !== id));
    setRows(
      rows.map((row) => {
        const { [id]: _, ...rest } = row.values;
        return { ...row, values: rest };
      })
    );
  };

  const updateColumnName = (id: string, name: string) => {
    setColumns(columns.map((col) => (col.id === id ? { ...col, name } : col)));
  };

  const updateColumnType = (id: string, type: string) => {
    setColumns(columns.map((col) => (col.id === id ? { ...col, type } : col)));
  };

  const addRow = () => {
    const newId = String(nextRowId);
    const newValues: Record<string, string> = {};
    columns.forEach((col) => {
      newValues[col.id] = '';
    });
    setRows([...rows, { id: newId, values: newValues }]);
    setNextRowId(nextRowId + 1);
  };

  const removeRow = (id: string) => {
    if (rows.length === 1) {
      toast({ description: 'You must have at least one row', variant: 'destructive' });
      return;
    }
    setRows(rows.filter((row) => row.id !== id));
  };

  const updateRowValue = (rowId: string, colId: string, value: string) => {
    setRows(
      rows.map((row) =>
        row.id === rowId
          ? { ...row, values: { ...row.values, [colId]: value } }
          : row
      )
    );
  };

  const handleCreate = async () => {
    if (!tableName.trim()) {
      toast({ description: 'Please enter a table name', variant: 'destructive' });
      return;
    }

    if (columns.length === 0) {
      toast({ description: 'Please add at least one column', variant: 'destructive' });
      return;
    }

    // Validate column names
    const columnNames = columns.map((col) => col.name.trim());
    if (columnNames.some((name) => !name)) {
      toast({ description: 'All columns must have names', variant: 'destructive' });
      return;
    }

    if (new Set(columnNames).size !== columnNames.length) {
      toast({ description: 'Column names must be unique', variant: 'destructive' });
      return;
    }

    try {
      await onCreateTable({
        name: tableName.trim(),
        columns: columns.map((col) => ({ name: col.name.trim(), type: col.type })),
      });
      
      toast({ description: 'Table created successfully!' });
      
      // Reset form
      setTableName('');
      setColumns([
        { id: '1', name: 'id', type: 'INTEGER' },
        { id: '2', name: 'name', type: 'TEXT' },
      ]);
      setRows([{ id: '1', values: {} }]);
      setNextColId(3);
      setNextRowId(2);
    } catch (error) {
      toast({
        description: error instanceof Error ? error.message : 'Failed to create table',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Table Name */}
      <FieldGroup>
        <FieldLabel>Table Name</FieldLabel>
        <Input
          placeholder="e.g., customers, products, sales"
          value={tableName}
          onChange={(e) => setTableName(e.target.value)}
          disabled={loading}
          className="font-mono"
        />
      </FieldGroup>

      {/* Columns Definition */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold">Columns</h3>
          <Button
            size="sm"
            variant="outline"
            onClick={addColumn}
            disabled={loading}
            className="gap-2"
          >
            <Plus className="h-4 w-4" />
            Add Column
          </Button>
        </div>

        <div className="space-y-2 max-h-64 overflow-y-auto">
          {columns.map((col, idx) => (
            <div key={col.id} className="flex gap-2 items-end">
              <div className="flex-1">
                <label className="text-xs text-muted-foreground">Column {idx + 1} Name</label>
                <Input
                  placeholder="Column name"
                  value={col.name}
                  onChange={(e) => updateColumnName(col.id, e.target.value)}
                  disabled={loading}
                  className="font-mono text-sm mt-1"
                />
              </div>
              <div className="w-32">
                <label className="text-xs text-muted-foreground">Type</label>
                <Select value={col.type} onValueChange={(type) => updateColumnType(col.id, type)} disabled={loading}>
                  <SelectTrigger className="text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {SQL_TYPES.map((type) => (
                      <SelectItem key={type} value={type}>
                        {type}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => removeColumn(col.id)}
                disabled={loading || columns.length === 1}
                className="text-destructive hover:text-destructive"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      </div>

      {/* Data Preview (optional) */}
      {rows.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">Sample Data (Optional)</h3>
            <Button
              size="sm"
              variant="outline"
              onClick={addRow}
              disabled={loading}
              className="gap-2"
            >
              <Plus className="h-4 w-4" />
              Add Row
            </Button>
          </div>

          <div className="border border-border rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted">
                    {columns.map((col) => (
                      <th key={col.id} className="px-3 py-2 text-left font-semibold text-xs">
                        {col.name}
                      </th>
                    ))}
                    <th className="px-3 py-2 w-10" />
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.id} className="border-b border-border last:border-0 hover:bg-muted/50">
                      {columns.map((col) => (
                        <td key={`${row.id}-${col.id}`} className="px-3 py-2">
                          <Input
                            type={col.type === 'INTEGER' ? 'number' : col.type === 'BOOLEAN' ? 'checkbox' : 'text'}
                            placeholder="Value"
                            value={row.values[col.id] || ''}
                            onChange={(e) => updateRowValue(row.id, col.id, e.target.value)}
                            disabled={loading}
                            className="h-8 text-xs"
                          />
                        </td>
                      ))}
                      <td className="px-2">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => removeRow(row.id)}
                          disabled={loading || rows.length === 1}
                          className="h-8 w-8 p-0 text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Create Button */}
      <Button
        onClick={handleCreate}
        disabled={loading || !tableName.trim() || columns.length === 0}
        className="w-full gap-2"
        size="lg"
      >
        <Check className="h-4 w-4" />
        Create Table
      </Button>
    </div>
  );
}
