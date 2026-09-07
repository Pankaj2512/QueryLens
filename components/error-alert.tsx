'use client';

import { AlertCircle, XCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';

interface ErrorAlertProps {
  title?: string;
  description: string;
  onDismiss?: () => void;
  details?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export default function ErrorAlert({
  title = 'Error',
  description,
  onDismiss,
  details,
  actionLabel,
  onAction,
}: ErrorAlertProps) {
  return (
    <Alert variant="destructive" role="alert">
      <AlertCircle className="h-4 w-4" />
      <div className="flex flex-1 flex-col gap-2">
        <AlertTitle>{title}</AlertTitle>
        <AlertDescription>{description}</AlertDescription>
        {details && (
          <details className="text-sm opacity-80">
            <summary className="cursor-pointer font-medium">View Details</summary>
            <code className="block mt-2 whitespace-pre-wrap break-words bg-destructive/10 p-2 rounded text-xs">
              {details}
            </code>
          </details>
        )}
      </div>
      <div className="flex gap-2 ml-4 flex-shrink-0">
        {actionLabel && onAction && (
          <Button size="sm" variant="outline" onClick={onAction}>
            {actionLabel}
          </Button>
        )}
        {onDismiss && (
          <Button
            size="sm"
            variant="ghost"
            onClick={onDismiss}
            className="text-destructive hover:text-destructive"
            aria-label="Dismiss error"
          >
            <XCircle className="h-4 w-4" />
          </Button>
        )}
      </div>
    </Alert>
  );
}
