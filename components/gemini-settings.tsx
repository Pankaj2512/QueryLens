'use client';

import { KeyRound } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { GEMINI_DEFAULT_MODEL } from '@/lib/gemini-settings';

interface GeminiSettingsProps {
  apiKey: string;
  model: string;
  onApiKeyChange: (value: string) => void;
  onModelChange: (value: string) => void;
}

export default function GeminiSettings({
  apiKey,
  model,
  onApiKeyChange,
  onModelChange,
}: GeminiSettingsProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-muted">
            <KeyRound className="h-4 w-4 text-muted-foreground" />
          </div>
          <div>
            <CardTitle className="text-base">Gemini</CardTitle>
            <CardDescription className="text-xs">
              API key and model for natural-language to SQL. API key is not stored and resets on refresh.
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-1.5">
          <Label htmlFor="gemini-api-key">API key</Label>
          <Input
            id="gemini-api-key"
            type="password"
            autoComplete="off"
            placeholder="Paste your Gemini API key"
            value={apiKey}
            onChange={(e) => onApiKeyChange(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="gemini-model">Model</Label>
          <Input
            id="gemini-model"
            type="text"
            autoComplete="off"
            placeholder={GEMINI_DEFAULT_MODEL}
            value={model}
            onChange={(e) => onModelChange(e.target.value)}
          />
        </div>
      </CardContent>
    </Card>
  );
}
