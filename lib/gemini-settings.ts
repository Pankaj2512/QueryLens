export const GEMINI_DEFAULT_MODEL = 'gemini-2.0-flash';

const STORAGE_KEY_MODEL = 'querylens.geminiModel';

export function loadGeminiSettingsFromStorage(): { apiKey: string; model: string } {
  if (typeof window === 'undefined') {
    return { apiKey: '', model: GEMINI_DEFAULT_MODEL };
  }
  return {
    // API key intentionally not persisted to reduce secret-at-rest risk.
    apiKey: '',
    model: localStorage.getItem(STORAGE_KEY_MODEL) ?? localStorage.getItem('queryforge.geminiModel') ?? GEMINI_DEFAULT_MODEL,
  };
}

export function persistGeminiApiKey(value: string) {
  // Intentionally a no-op to avoid persisting sensitive keys.
  void value;
}

export function persistGeminiModel(value: string) {
  if (typeof window === 'undefined') return;
  const v = value.trim() || GEMINI_DEFAULT_MODEL;
  localStorage.setItem(STORAGE_KEY_MODEL, v);
}
