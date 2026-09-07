'use client';

import { useState } from 'react';
import { Database } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import DataSourceSelector from '@/components/data-source-selector';
import GeminiSettings from '@/components/gemini-settings';
import SchemaViewer from '@/components/schema-viewer';
import ChatInterface from '@/components/chat-interface';
import { useQueryLens } from '@/hooks/use-query-lens';

export default function Home() {
  const {
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
  } = useQueryLens();

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <Database className="h-6 w-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-foreground">QueryLens</h1>
                <p className="text-sm text-muted-foreground">Natural Language SQL Query Builder</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <Tabs defaultValue="dashboard" className="space-y-6">
          <TabsList className="grid w-full max-w-md grid-cols-2">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="history">History</TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-3">
              {/* Data Source Selector */}
              <div className="lg:col-span-1 space-y-6">
                <GeminiSettings
                  apiKey={geminiApiKey}
                  model={geminiModel}
                  onApiKeyChange={setGeminiApiKey}
                  onModelChange={setGeminiModel}
                />
                <DataSourceSelector 
                  onUpload={uploadFile} 
                  onManualTableCreate={createTable}
                  loading={loading} 
                />
              </div>

              {/* Main Query Area */}
              <div className="lg:col-span-2 space-y-6">
                {/* Table Selection */}
                {tables.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Select Table</CardTitle>
                      <CardDescription>Choose a dataset to query</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap gap-2">
                        {tables.map((table) => (
                          <Button
                            key={table}
                            variant={selectedTable === table ? 'default' : 'outline'}
                            onClick={() => setSelectedTable(table)}
                            className="font-mono text-sm"
                          >
                            {table}
                          </Button>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Schema Info */}
                {selectedTable && <SchemaViewer tableName={selectedTable} />}

                {/* Chat Interface */}
                {selectedTable && (
                  <ChatInterface
                    tableName={selectedTable}
                    onQuery={executeQuery}
                    loading={loading}
                  />
                )}
              </div>
            </div>
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Query History</CardTitle>
                <CardDescription>Your recent queries and results</CardDescription>
              </CardHeader>
              <CardContent>
                {queryHistory.length === 0 ? (
                  <div className="py-8 text-center">
                    <p className="text-muted-foreground">No queries yet. Start by uploading a CSV file!</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {queryHistory.map((item, idx) => (
                      <div key={idx} className="space-y-2 border-b border-border pb-4 last:border-0">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className="font-semibold text-foreground">{item.naturalLanguage}</p>
                            <p className="text-xs text-muted-foreground">
                              {item.tableName}
                              {item.createdAt ? ` · ${new Date(item.createdAt).toLocaleString()}` : ''}
                            </p>
                            <code className="block mt-2 rounded bg-muted p-2 font-mono text-xs text-muted-foreground overflow-auto">
                              {item.generatedSql}
                            </code>
                            {item.error && (
                              <p className="mt-2 text-xs text-destructive">{item.error}</p>
                            )}
                          </div>
                          {item.executed && (
                            <span className="ml-2 inline-flex items-center rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-800 dark:bg-green-900 dark:text-green-200">
                              Executed
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
