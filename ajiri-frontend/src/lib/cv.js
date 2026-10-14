export const MAX_CV_BYTES = 5 * 1024 * 1024
export function validateCV(file) {
  if (!file) return 'Choose a CV file first.'
  if (!/\.(pdf|doc|docx)$/i.test(file.name))
    return 'Use a PDF, DOC or DOCX file.'
  if (file.size > MAX_CV_BYTES) return 'Your CV must be 5 MB or smaller.'
  if (file.size === 0) return 'The selected file is empty.'
  return ''
}
