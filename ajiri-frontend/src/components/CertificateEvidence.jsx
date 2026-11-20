import { useId, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'
import { apiErrors } from '../lib/errors'
import DownloadButton from './DownloadButton'
import FormErrors from './FormErrors'
import { Button, Card, Input } from './ui'

const endpoint = '/profiles/me/certificates/'
const queryKey = ['api', endpoint]
const scanLabels = {
  pending: 'Waiting for a malware scan.',
  scanning: 'Malware scan in progress.',
  clean: 'The last malware scan found no threat.',
  infected: 'Download blocked because the scan detected a threat.',
  unavailable: 'Download blocked because a scan was unavailable.',
}

function EvidenceRow({
  name,
  certification,
  evidence,
  disabled,
  onUpload,
  onRemove,
}) {
  const id = useId()
  const [file, setFile] = useState(null)
  return (
    <form
      className="stack"
      onSubmit={(event) => {
        event.preventDefault()
        if (file) onUpload(certification.id, evidence, file)
      }}
    >
      <fieldset disabled={disabled} className="stack min-w-0">
        <legend className="font-semibold">{name}</legend>
        {evidence && (
          <>
            <p>{scanLabels[evidence.scan_state] || 'Download unavailable.'}</p>
            {evidence.scan_state === 'clean' && (
              <DownloadButton
                path={`${endpoint}${certification.id}/`}
                filename="certificate.pdf"
              >
                Download PDF for {name}
              </DownloadButton>
            )}
            <Button
              type="button"
              variant="outline"
              onClick={() => onRemove(certification.id, evidence, name)}
            >
              Remove PDF for {name}
            </Button>
          </>
        )}
        <label htmlFor={id}>
          {evidence ? 'Replacement' : 'Evidence'} PDF for {name}
        </label>
        <Input
          id={id}
          type="file"
          accept=".pdf,application/pdf"
          onChange={(event) => setFile(event.target.files[0])}
        />
        <Button type="submit" disabled={!file}>
          {evidence ? 'Replace PDF for' : 'Upload PDF for'} {name}
        </Button>
      </fieldset>
    </form>
  )
}

// see docs/CONCEPTS.md#private-certificate-evidence
export default function CertificateEvidence({
  certifications,
  revision,
  savingCV,
}) {
  const client = useQueryClient()
  const evidenceQuery = useQuery({
    queryKey,
    queryFn: async ({ signal }) => {
      try {
        const { data } = await apiClient.get(endpoint, { signal })
        return data.results
      } catch (error) {
        if (error.response?.status === 404) return null
        throw error
      }
    },
    retry: false,
  })
  const [busy, setBusy] = useState(false)
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState('')
  const [uncertain, setUncertain] = useState(false)

  async function refresh() {
    const result = await evidenceQuery.refetch()
    if (result.isSuccess) setUncertain(false)
  }

  async function change(certificationId, evidence, file) {
    if (busy || savingCV || uncertain || evidenceQuery.isFetching) return
    if (
      file &&
      (!/\.pdf$/i.test(file.name) || !file.size || file.size > 5 * 1024 * 1024)
    ) {
      setMessage('')
      setErrors({ document: ['Choose a PDF between 1 byte and 5 MiB.'] })
      return
    }
    setBusy(true)
    setErrors({})
    setMessage('')
    const path = `${endpoint}${certificationId}/`
    const expected = { expected_revision: revision }
    if (evidence) {
      expected.expected_id = evidence.id
      expected.expected_hash = evidence.sha256
    }
    try {
      await client.cancelQueries({ queryKey, exact: true })
      let result
      if (file) {
        const form = new FormData()
        form.append('document', file)
        Object.entries(expected).forEach(([key, value]) =>
          form.append(key, value)
        )
        const response = await apiClient.put(path, form)
        result = response.data
      } else {
        await apiClient.delete(path, { data: { ...expected, confirm: true } })
      }
      client.setQueryData(queryKey, (rows) => {
        if (!rows) return rows
        const retained = rows.filter(
          (row) => row.certification_id !== certificationId
        )
        return result ? [...retained, result] : retained
      })
      setMessage(file ? 'Private PDF saved.' : 'Private PDF removed.')
    } catch (error) {
      setErrors(
        apiErrors(
          error,
          'Could not confirm the change. Refresh evidence before trying again.'
        )
      )
      const status = error.response?.status
      if (!status || status >= 500 || status === 409 || status === 404)
        setUncertain(true)
    } finally {
      setBusy(false)
    }
  }

  if (evidenceQuery.data === null || evidenceQuery.isPending) return null

  return (
    <Card className="stack">
      <h2>Private certificate evidence</h2>
      <p>
        Attach PDFs to saved certifications. Each PDF can be up to 5 MiB. You
        can keep up to five files and 20 MiB in total.
      </p>
      <p>
        Only you can access these PDFs. They stay separate from your CV and
        applications. A malware scan checks file safety. Ajiri does not verify
        qualifications.
      </p>
      {evidenceQuery.isError && (
        <p role="alert">Could not load private certificate evidence.</p>
      )}
      {uncertain && (
        <p>
          Refresh evidence before trying again. If the CV revision changed in
          another tab, save or copy any unsaved edits before reloading the CV.
        </p>
      )}
      <Button
        type="button"
        variant="outline"
        onClick={refresh}
        disabled={busy || evidenceQuery.isFetching}
      >
        Refresh evidence
      </Button>
      <FormErrors
        prefix="certificate-evidence"
        errors={errors}
        fieldLabels={{ document: 'PDF' }}
      />
      <p role="status">{busy ? 'Saving private evidence…' : message}</p>
      {!evidenceQuery.isError &&
        certifications.map((certification, index) => {
          const evidence = evidenceQuery.data.find(
            (row) => row.certification_id === certification.id
          )
          const name = certification.name
            ? `${certification.name} (certification ${index + 1})`
            : `Certification ${index + 1}`
          return (
            <EvidenceRow
              key={`${certification.id}:${revision}:${evidence?.id || ''}`}
              name={name}
              certification={certification}
              evidence={evidence}
              disabled={
                savingCV || busy || uncertain || evidenceQuery.isFetching
              }
              onUpload={change}
              onRemove={(id, row, label) => {
                if (
                  window.confirm(
                    `Remove the private PDF for ${label}? Backups follow separate retention.`
                  )
                ) {
                  change(id, row)
                }
              }}
            />
          )
        })}
    </Card>
  )
}
