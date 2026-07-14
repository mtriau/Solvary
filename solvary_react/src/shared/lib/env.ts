export const env = {
  apiBaseUrl: (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '/api',
  wsUrl: (import.meta.env.VITE_WS_URL as string | undefined) ?? '/ws',
  appName: (import.meta.env.VITE_APP_NAME as string | undefined) ?? 'Solvary',
} as const;
