import { useEffect, useState } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { createApiQueryClient } from '../api/queryClient'

// Public screens do not download or initialize the private read cache.
// see docs/CONCEPTS.md#deferred-private-query-cache
export default function PrivateQueryProvider({ children }) {
  const [client] = useState(createApiQueryClient)
  useEffect(() => () => client.clear(), [client])
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}
