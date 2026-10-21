import { useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'

export function useApiQuery(url) {
  const query = useQuery({
    queryKey: ['api', url],
    queryFn: async ({ signal }) => {
      const response = await apiClient.get(url, { signal })
      return response.data
    },
  })
  return {
    data: query.isError ? null : query.data,
    loading: query.isPending,
    error: query.isError
      ? query.error?.response?.data?.detail ||
        'Please check your connection and try again.'
      : '',
    retry: () => query.refetch(),
  }
}

export function useApiInvalidation() {
  const client = useQueryClient()
  // Profile edits affect matches, CV approval affects selection, and preparation
  // affects application lists. Refresh mounted reads; mark other cached reads stale.
  return () => client.invalidateQueries({ queryKey: ['api'] })
}
