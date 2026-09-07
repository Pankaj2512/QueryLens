'use client';

import { useState } from 'react';
import { Upload, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import FileUploadPanel from './file-upload-panel';
import ManualTableBuilder from './manual-table-builder';

interface DataSourceSelectorProps {
  onUpload: (file: File) => Promise<void>;
  onManualTableCreate: (tableData: { name: string; columns: Array<{ name: string; type: string }> }) => Promise<void>;
  loading: boolean;
}

export default function DataSourceSelector({
  onUpload,
  onManualTableCreate,
  loading,
}: DataSourceSelectorProps) {
  const [activeTab, setActiveTab] = useState<'upload' | 'manual'>('upload');

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Add Data Source</CardTitle>
        <CardDescription>Upload a CSV file or create a table manually</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'upload' | 'manual')}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="upload" className="flex items-center gap-2">
              <Upload className="h-4 w-4" />
              <span className="hidden sm:inline">Upload CSV</span>
              <span className="sm:hidden">Upload</span>
            </TabsTrigger>
            <TabsTrigger value="manual" className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              <span className="hidden sm:inline">Build Manual</span>
              <span className="sm:hidden">Manual</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="space-y-4">
            <FileUploadPanel onUpload={onUpload} loading={loading} />
          </TabsContent>

          <TabsContent value="manual" className="space-y-4">
            <ManualTableBuilder onCreateTable={onManualTableCreate} loading={loading} />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
