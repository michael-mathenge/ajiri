import { useEffect, useState } from 'react'
import apiClient from '../api/client'

export function useApiResource(url) {
  const [state, setState] = useState({ data: null, error: '' })
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    // Cancel obsolete requests so a slow old filter cannot replace newer results.
    // see docs/CONCEPTS.md#effect-cleanup
    apiClient
      .get(url, { signal: controller.signal })
      .then(({ data }) => {
        if (!controller.signal.aborted)
          setState({ data, error: '', url, attempt })
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setState({
            data: null,
            error:
              error.response?.data?.detail ||
              'Please check your connection and try again.',
            url,
            attempt,
          })
      })
    return () => controller.abort()
  }, [url, attempt])
  const loading = state.url !== url || state.attempt !== attempt
  return {
    data: loading ? null : state.data,
    error: loading ? '' : state.error,
    loading,
    retry: () => setAttempt((value) => value + 1),
  }
}
