import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export const cn = (...inputs) => twMerge(clsx(inputs))
export const jobType = (value = '') => value.replaceAll('_', ' ')
export const dateLabel = (value) =>
  value
    ? new Date(value).toLocaleDateString('en-KE', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    : 'Date unavailable'
export function salaryLabel(job) {
  if (job.is_salary_negotiable) return 'Salary negotiable'
  const amount = (value) => Number(value).toLocaleString('en-KE')
  if (job.salary_min && job.salary_max)
    return `KES ${amount(job.salary_min)} – ${amount(job.salary_max)}`
  if (job.salary_min) return `From KES ${amount(job.salary_min)}`
  if (job.salary_max) return `Up to KES ${amount(job.salary_max)}`
  return 'Salary not listed'
}
