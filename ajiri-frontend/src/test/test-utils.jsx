import { render as testingRender } from '@testing-library/react'
import { QueryClientProvider } from '@tanstack/react-query'
import { createApiQueryClient } from '../api/queryClient'

export { act, fireEvent, screen, waitFor, within } from '@testing-library/react'

export function render(ui, options = {}) {
  const client = createApiQueryClient()
  client.setDefaultOptions({
    ...client.getDefaultOptions(),
    queries: {
      ...client.getDefaultOptions().queries,
      retry: false,
      gcTime: Infinity,
    },
  })
  const Wrapper = options.wrapper
  return testingRender(ui, {
    ...options,
    wrapper: ({ children }) => (
      <QueryClientProvider client={client}>
        {Wrapper ? <Wrapper>{children}</Wrapper> : children}
      </QueryClientProvider>
    ),
  })
}
