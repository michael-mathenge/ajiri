import * as z from 'zod/mini'
import { validateCV } from './cv'

const text = (max = 255) =>
  z.string().check(z.maxLength(max, `Use ${max} characters or fewer.`))
const required = (label, max = 255) =>
  text(max).check(
    z.refine((value) => Boolean(value.trim()), `${label} is required.`)
  )
const email = z.string().check(z.email('Enter a valid email address.'))
const optionalEmail = z.union([z.literal(''), email])
export const loginSchema = z.object({
  email,
  password: required('Password', 4096),
})
export const registerSchema = z.object({
  full_name: required('Full name'),
  email,
  phone_number: text(20),
  password: z
    .string()
    .check(
      z.minLength(8, 'Use at least 8 characters.'),
      z.maxLength(4096, 'Password is too long.')
    ),
  privacy_consent: z.literal(true, {
    error: 'Read and agree to the privacy notice before registering.',
  }),
  privacy_policy_version: text(),
})
export const recoverySchema = (mode) =>
  z
    .object({
      email: mode === 'request-reset' ? email : z.string(),
      password: mode === 'reset' ? required('New password', 4096) : z.string(),
      password_confirm: z.string(),
    })
    .check(
      z.refine((v) => mode !== 'reset' || v.password === v.password_confirm, {
        error: 'Passwords must match.',
        path: ['password_confirm'],
      })
    )
export const profileSchema = z.object({
  full_name: text(),
  phone_number: text(20),
  headline: text(),
  location: text(),
  bio: z.string(),
  years_of_experience: z
    .union([z.string(), z.number()])
    .check(
      z.refine(
        (v) =>
          String(v).trim() !== '' &&
          Number.isSafeInteger(Number(v)) &&
          Number(v) >= 0,
        'Use a whole number of years, zero or more.'
      )
    ),
  skill_names: z.string(),
  notify_in_app: z.boolean(),
})
export const uploadSchema = z.object({
  cv_file: z.custom((file) => !validateCV(file), {
    error: (issue) => validateCV(issue.input),
  }),
})
export const alertSchema = z.object({ enabled: z.boolean() })
export const searchSchema = z.object({
  title: text(255),
  location: text(255),
  job_type: z.string(),
})
export const packageSchema = z.object({
  cv_version: required('Approved CV'),
  letter_text: required('Working cover letter', 10000),
  email_subject: text(255),
  email_body: text(10000),
})
// Incomplete CVs must remain saveable; approval validation stays on the server.
const month = z
  .string()
  .check(
    z.refine(
      (value) =>
        value === '' || /^(?!0000)[0-9]{4}-(0[1-9]|1[0-2])$/.test(value),
      'Choose both a month and a four-digit year, or clear the date.'
    )
  )
const row = z.looseObject({
  id: z.string(),
  start: z.optional(month),
  end: z.optional(month),
  issued: z.optional(month),
  expiry: z.optional(month),
})
export const cvSchema = z.looseObject({
  contact: z.object({
    name: text(),
    email: optionalEmail,
    phone: text(20),
    location: text(),
  }),
  headline: text(),
  summary: text(3000),
  skills: z.array(z.string()),
  employment: z
    .array(row)
    .check(z.maxLength(20, 'Use at most 20 work entries.')),
  education: z
    .array(row)
    .check(z.maxLength(15, 'Use at most 15 education entries.')),
  certifications: z
    .array(row)
    .check(z.maxLength(20, 'Use at most 20 certifications.')),
  projects: z.array(row).check(z.maxLength(20, 'Use at most 20 projects.')),
})
