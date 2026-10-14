import { useState } from 'react'
import { Button } from './ui'
import { downloadFile } from '../lib/download'

export default function DownloadButton({ path, filename, children }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const download = async () => {
    if (busy) return
    setBusy(true)
    setError('')
    try {
      await downloadFile(path, filename)
    } catch (error) {
      setError(error.message)
    } finally {
      setBusy(false)
    }
  }
  return (
    <div>
      <Button variant="outline" disabled={busy} onClick={download}>
        {busy ? 'Preparing download…' : children}
      </Button>
      {error && (
        <p role="alert" className="error-text mt-2">
          {error}
        </p>
      )}
    </div>
  )
}
