import apiClient from '../api/client'

// Anchors cannot attach the access token. Fetch through the existing client first.
// see docs/CONCEPTS.md#authenticated-document-downloads
export async function downloadFile(path, filename) {
  let response
  try {
    response = await apiClient.get(path, { responseType: 'blob' })
  } catch (error) {
    if (error.response?.data instanceof Blob) {
      try {
        error.response.data = JSON.parse(await error.response.data.text())
      } catch {
        /* Use a readable fallback below. */
      }
    }
    throw new Error(
      error.response?.data?.detail ||
        'Could not download the document. Please try again.'
    )
  }
  const url = URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = url
  const disposition = response.headers?.['content-disposition'] || ''
  const encoded = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1]
  const plain = disposition.match(/filename="([^"]+)"|filename=([^;]+)/i)
  let serverName
  try {
    serverName = encoded
      ? decodeURIComponent(encoded)
      : plain?.[1] || plain?.[2]
  } catch {
    /* Use the supplied fallback. */
  }
  link.download = serverName ? serverName.split(/[\\/]/).pop() : filename
  document.body.append(link)
  link.click()
  link.remove()
  // Give the browser time to start the download before releasing the blob.
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
