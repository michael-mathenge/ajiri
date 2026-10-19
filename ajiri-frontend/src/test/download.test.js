import { afterEach, expect, it, vi } from 'vitest'
import apiClient from '../api/client'
import { downloadFile } from '../lib/download'

vi.mock('../api/client', () => ({ default: { get: vi.fn() } }))
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); vi.useRealTimers() })

it.each([
  ['attachment; filename="First_Middle_Last_CV_Company.docx"', 'First_Middle_Last_CV_Company.docx'],
  ["attachment; filename*=utf-8''Zo%C3%AB_Name_CV.docx", 'Zoë_Name_CV.docx'],
  ['', 'Fallback.docx'],
])('honors safe server download labels with a readable fallback: %s', async (header, expected) => {
  vi.useFakeTimers()
  apiClient.get.mockResolvedValue({ data: new Blob(['synthetic']), headers: { 'content-disposition': header } })
  vi.stubGlobal('URL', { createObjectURL: vi.fn(() => 'blob:synthetic'), revokeObjectURL: vi.fn() })
  let name
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function () { name = this.download })
  await downloadFile('/synthetic/document/', 'Fallback.docx')
  expect(name).toBe(expected)
  expect(apiClient.get).toHaveBeenCalledWith('/synthetic/document/', { responseType: 'blob' })
  vi.runAllTimers()
})
