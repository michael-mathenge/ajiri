import { ToastProvider } from '../components/ui'
import { useToast } from '../hooks/useToast'
import { expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from './test-utils'
import { MemoryRouter } from 'react-router-dom'
import { useSchemaForm, schemaMessages } from '../hooks/useSchemaForm'
import {
  loginSchema,
  registerSchema,
  recoverySchema,
  profileSchema,
  uploadSchema,
  alertSchema,
  searchSchema,
  packageSchema,
  cvSchema,
} from '../lib/formSchemas'
import FormErrors from '../components/FormErrors'

function Example({ save }) {
  const { values, setValues, errors, setErrors, submit } = useSchemaForm(
    loginSchema,
    { email: '', password: '' }
  )
  return (
    <form
      noValidate
      onSubmit={submit(async (data) => {
        try {
          await save(data)
        } catch {
          setErrors({
            password: ['First server message.', 'Second server message.'],
          })
        }
      })}
    >
      <label>
        Email
        <input
          value={values.email}
          onChange={(e) => setValues({ ...values, email: e.target.value })}
        />
      </label>
      <label>
        Password
        <input
          value={values.password}
          onChange={(e) => setValues({ ...values, password: e.target.value })}
        />
      </label>
      <FormErrors errors={errors} prefix="example" />
      <button>Save</button>
    </form>
  )
}
it('validates all fields without a request, preserves input and accepts a correction', async () => {
  const save = vi.fn()
  render(
    <MemoryRouter>
      <Example save={save} />
    </MemoryRouter>
  )
  fireEvent.change(screen.getByLabelText('Email'), {
    target: { value: 'invalid' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Save' }))
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Enter a valid email address.'
  )
  expect(screen.getByRole('alert')).toHaveTextContent('Password is required.')
  expect(save).not.toHaveBeenCalled()
  expect(screen.getByLabelText('Email')).toHaveValue('invalid')
  fireEvent.change(screen.getByLabelText('Email'), {
    target: { value: 'synthetic@example.invalid' },
  })
  fireEvent.change(screen.getByLabelText('Password'), {
    target: { value: 'synthetic-pass' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Save' }))
  await waitFor(() =>
    expect(save).toHaveBeenCalledWith({
      email: 'synthetic@example.invalid',
      password: 'synthetic-pass',
    })
  )
})
it('does not submit twice during validation or a pending mutation, and retains every server error', async () => {
  let reject
  const save = vi.fn(
    () =>
      new Promise((_, fail) => {
        reject = fail
      })
  )
  render(<Example save={save} />)
  fireEvent.change(screen.getByLabelText('Email'), {
    target: { value: 'synthetic@example.invalid' },
  })
  fireEvent.change(screen.getByLabelText('Password'), {
    target: { value: 'test' },
  })
  const button = screen.getByRole('button', { name: 'Save' })
  fireEvent.click(button)
  fireEvent.click(button)
  await waitFor(() => expect(save).toHaveBeenCalledTimes(1))
  fireEvent.click(button)
  expect(save).toHaveBeenCalledTimes(1)
  reject(new Error('synthetic'))
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'First server message.'
  )
  expect(screen.getByRole('alert')).toHaveTextContent('Second server message.')
  expect(document.getElementById('example-password-error')).toBeVisible()
})
it('requires separate registration agreement and never alters password whitespace', () => {
  const values = {
    full_name: 'Synthetic Applicant',
    email: 'a@example.invalid',
    phone_number: '',
    password: '  test-password  ',
    privacy_consent: false,
    privacy_policy_version: 'privacy-draft-v1',
  }
  expect(registerSchema.safeParse(values).success).toBe(false)
  expect(
    registerSchema.parse({ ...values, privacy_consent: true }).password
  ).toBe(values.password)
  expect(
    loginSchema.parse({ email: values.email, password: values.password })
      .password
  ).toBe(values.password)
})
it('reports reset mismatch on the confirmation field but permits link-confirmation forms without credentials', () => {
  const result = recoverySchema('reset').safeParse({
    email: '',
    password: 'new',
    password_confirm: 'different',
  })
  expect(schemaMessages(result.error.issues).password_confirm).toEqual([
    'Passwords must match.',
  ])
  expect(
    recoverySchema('verify').safeParse({
      email: '',
      password: '',
      password_confirm: '',
    }).success
  ).toBe(true)
})
it('rejects invalid experience and file size/type, without treating browser metadata as content verification', () => {
  const profile = {
    full_name: '',
    phone_number: '',
    headline: '',
    location: '',
    bio: '',
    skill_names: '',
    notify_in_app: false,
    years_of_experience: '1.5',
  }
  expect(profileSchema.safeParse(profile).success).toBe(false)
  expect(
    profileSchema.safeParse({ ...profile, years_of_experience: '0' }).success
  ).toBe(true)
  expect(uploadSchema.safeParse({ cv_file: null }).success).toBe(false)
  expect(
    uploadSchema.safeParse({ cv_file: new File(['test'], 'bad.exe') }).success
  ).toBe(false)
  expect(
    uploadSchema.safeParse({ cv_file: new File(['test'], 'test.pdf') }).success
  ).toBe(true)
  expect(
    uploadSchema.safeParse({
      cv_file: { name: 'test.pdf', size: 5 * 1024 * 1024 + 1 },
    }).success
  ).toBe(false)
})
it('keeps alert false valid, limits search inputs and requires approved CV plus a nonblank letter', () => {
  expect(alertSchema.parse({ enabled: false }).enabled).toBe(false)
  expect(
    searchSchema.safeParse({
      title: 'x'.repeat(256),
      location: '',
      job_type: '',
    }).success
  ).toBe(false)
  const draft = {
    cv_version: '',
    letter_text: ' ',
    email_subject: '',
    email_body: '',
  }
  expect(packageSchema.safeParse(draft).success).toBe(false)
  expect(
    packageSchema.safeParse({
      ...draft,
      cv_version: 'synthetic-version',
      letter_text: 'Synthetic letter',
    }).success
  ).toBe(true)
})
it('allows incomplete CV drafts and retains row fields for server validation', () => {
  const draft = {
    contact: { name: '', email: '', phone: '', location: '' },
    headline: '',
    summary: '',
    skills: [],
    employment: [{ id: 'synthetic', title: '', achievements: [] }],
    education: [],
    certifications: [],
    projects: [],
  }
  expect(cvSchema.parse(draft).employment[0].achievements).toEqual([])
  expect(
    cvSchema.safeParse({ ...draft, summary: 'x'.repeat(3001) }).success
  ).toBe(false)
})
it('keeps repeated nested validation messages and their indexed paths', () => {
  expect(
    schemaMessages([
      { path: ['employment', 1, 'title'], message: 'Required.' },
      { path: ['employment', 1, 'title'], message: 'Check this row.' },
    ])
  ).toEqual({ 'employment.1.title': ['Required.', 'Check this row.'] })
})

function Notify() {
  const toast = useToast()
  return (
    <button
      onClick={() => toast('Synthetic notification', 'Action completed.')}
    >
      Notify
    </button>
  )
}
it('loads notification controls on demand without losing the message', async () => {
  render(
    <ToastProvider>
      <Notify />
    </ToastProvider>
  )
  expect(screen.queryByText('Synthetic notification')).not.toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Notify' }))
  expect(await screen.findByText('Synthetic notification')).toBeVisible()
  expect(screen.getByText('Action completed.')).toBeVisible()
  fireEvent.click(screen.getByRole('button', { name: 'Dismiss notification' }))
  await waitFor(() =>
    expect(screen.queryByText('Synthetic notification')).not.toBeInTheDocument()
  )
})
