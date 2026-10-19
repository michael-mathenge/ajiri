import { expect, it } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import FormErrors from '../components/FormErrors'
import { apiErrors } from '../lib/errors'

it('labels fields and separates every nested message without changing association IDs', () => {
  const errors = apiErrors({ response: { data: { password: ['Too short.', 'Too common.'],
    phone_number: ['Check number.'], employment: [{ title: ['Required.'], organisation: ['Required employer.'] }] } } })
  render(<FormErrors errors={errors} prefix="register" />)
  const field = document.getElementById('register-password-error')
  expect(field.querySelector('strong')).toHaveTextContent('Password:')
  expect(within(field).getAllByRole('listitem')).toHaveLength(2)
  expect(screen.getByText('Phone number:')).toBeVisible()
  for (const message of ['Too short.', 'Too common.', 'Required.', 'Required employer.'])
    expect(screen.getByText(message)).toBeVisible()
})
