import { QueryClient } from '@tanstack/react-query'

// Keep private data in memory only; AuthProvider clears it on account changes.
// see docs/CONCEPTS.md#query-data-layer
export function retryRead(failureCount, error) {
  const status = error?.response?.status
  return failureCount < 1 && (!status || status >= 500)
}

export function createApiQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        gcTime: 5 * 60_000,
        retry: retryRead,
        retryDelay: 1000,
        refetchOnWindowFocus: false,
      },
      mutations: { retry: false },
    },
  })
}
