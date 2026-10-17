import { StrictMode } from 'react'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import AccountRecovery from '../pages/AccountRecovery'
import apiClient from '../api/client'

vi.mock('../api/client', () => ({ default: { post: vi.fn(), get: vi.fn() } }))
beforeEach(() => {
  vi.resetAllMocks()
  window.history.replaceState({}, '', '/')
})
afterEach(() => vi.useRealTimers())
const page = mode => render(<StrictMode><MemoryRouter><AccountRecovery mode={mode} /></MemoryRouter></StrictMode>)

it('requests a reset and truthfully shows that email is disabled', async () => {
  apiClient.post.mockResolvedValue({ data: { delivery_available: false } })
  page('request-reset')
  fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'owner@example.invalid' } })
  fireEvent.click(screen.getByRole('button', { name: 'Request reset link' }))
  expect(await screen.findByRole('status')).toHaveTextContent('No email was sent')
  expect(apiClient.post).toHaveBeenCalledWith('/accounts/password-reset/request/', expect.objectContaining({ email: 'owner@example.invalid', request_id: expect.any(String) }))
})

it('retains fragment credentials in StrictMode, removes them from URL and submits once', async () => {
  window.history.replaceState({}, '', '/reset-password#uid=MQ&token=synthetic-token')
  apiClient.post.mockResolvedValue({ data: { detail: 'Password changed. Log in with your new password.' } })
  page('reset')
  expect(window.location.hash).toBe('')
  fireEvent.change(screen.getByLabelText('New password'), { target: { value: 'Strong-river-phrase-2027!' } })
  fireEvent.change(screen.getByLabelText('Confirm new password'), { target: { value: 'Strong-river-phrase-2027!' } })
  fireEvent.click(screen.getByRole('button', { name: 'Save new password' }))
  expect(await screen.findByRole('status')).toHaveTextContent('Password changed')
  expect(apiClient.post).toHaveBeenCalledTimes(1)
  expect(apiClient.post).toHaveBeenCalledWith('/accounts/password-reset/confirm/', expect.objectContaining({ uid: 'MQ', token: 'synthetic-token' }))
  expect(screen.queryByText('This link is incomplete. Request a new link.')).not.toBeInTheDocument()
  expect(screen.queryByLabelText('New password')).not.toBeInTheDocument()
})

it('shows all password errors and checks mismatch locally', async () => {
  window.history.replaceState({}, '', '/reset-password#uid=MQ&token=synthetic-token')
  apiClient.post.mockRejectedValue({ response: { data: { password: ['Too short.', 'Too common.'] } } })
  page('reset')
  fireEvent.change(screen.getByLabelText('New password'), { target: { value: 'weak' } })
  fireEvent.change(screen.getByLabelText('Confirm new password'), { target: { value: 'different' } })
  fireEvent.click(screen.getByRole('button', { name: 'Save new password' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Passwords must match')
  expect(apiClient.post).not.toHaveBeenCalled()
  fireEvent.change(screen.getByLabelText('Confirm new password'), { target: { value: 'weak' } })
  fireEvent.click(screen.getByRole('button', { name: 'Save new password' }))
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Too short. Too common.'))
})

it('requires an explicit click to verify, not page load', async () => {
  window.history.replaceState({}, '', '/verify-email#token=synthetic-token')
  apiClient.post.mockResolvedValue({ data: { detail: 'Email verified.' } })
  page('verify')
  expect(apiClient.post).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole('button', { name: 'Confirm email verification' }))
  expect(await screen.findByRole('status')).toHaveTextContent('Email verified.')
  expect(apiClient.post).toHaveBeenCalledWith('/accounts/verification/confirm/', { token: 'synthetic-token' })
})

it('missing token gives a recovery link without a mutation', () => {
  page('reset')
  expect(screen.getByRole('alert')).toHaveTextContent('incomplete')
  expect(screen.getByRole('button', { name: 'Save new password' })).toBeDisabled()
  expect(screen.getByRole('link', { name: 'Request a new link' })).toHaveAttribute('href', '/forgot-password')
  expect(apiClient.post).not.toHaveBeenCalled()
})

it('shows authenticated verification status and a truthful disabled request result', async () => {
  apiClient.get.mockResolvedValue({ data: { verified: false, delivery_available: false } })
  apiClient.post.mockResolvedValue({ data: { delivery_available: false } })
  page('verification')
  expect(await screen.findByText(/current email is not verified/)).toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Request verification link' }))
  expect(await screen.findByRole('status')).toHaveTextContent('No email was sent')
})

it('renders rate limit guidance without automatic mutation retries', async () => {
  apiClient.post.mockRejectedValue({ response: { status: 429, headers: { 'retry-after': '60' } } })
  page('request-reset')
  fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'owner@example.invalid' } })
  fireEvent.click(screen.getByRole('button', { name: 'Request reset link' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Too many requests')
  expect(screen.getByText('You can try again in 1 min.')).toBeVisible()
  expect(screen.getByRole('button', { name: 'Request reset link' })).toBeDisabled()
  expect(apiClient.post).toHaveBeenCalledTimes(1)
})

it('counts down the verification wait and requires a manual click after expiry', async () => {
  vi.useFakeTimers()
  apiClient.get.mockResolvedValue({ data: { verified: false } })
  apiClient.post.mockRejectedValue({ response: { status: 429, headers: { 'retry-after': '2270' } } })
  page('verification')
  await act(async () => {})
  const button = screen.getByRole('button', { name: 'Request verification link' })
  await act(async () => { fireEvent.click(button) })
  expect(screen.getByText('You can try again in 37 min 50 sec.')).toBeVisible()
  expect(button).toBeDisabled()
  fireEvent.submit(button.closest('form'))
  expect(apiClient.post).toHaveBeenCalledTimes(1)
  await act(async () => { vi.advanceTimersByTime(2270000) })
  expect(button).toBeEnabled()
  expect(screen.getByText(/No request has been sent automatically/)).toBeVisible()
  expect(apiClient.post).toHaveBeenCalledTimes(1)
  await act(async () => { fireEvent.click(button) })
  expect(apiClient.post).toHaveBeenCalledTimes(2)
})

it('uses elapsed clock time when a background tab resumes', async () => {
  vi.useFakeTimers()
  apiClient.post.mockRejectedValue({ response: { status: 429, headers: { 'retry-after': '60' } } })
  page('request-reset')
  fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'owner@example.invalid' } })
  const button = screen.getByRole('button', { name: 'Request reset link' })
  await act(async () => { fireEvent.click(button) })
  vi.setSystemTime(Date.now() + 120000)
  await act(async () => { vi.advanceTimersByTime(1000) })
  expect(button).toBeEnabled()
  expect(apiClient.post).toHaveBeenCalledTimes(1)
})

it('shows generic guidance without inventing a timer for an invalid retry header', async () => {
  apiClient.post.mockRejectedValue({ response: { status: 429, headers: { 'retry-after': 'invalid' } } })
  page('request-reset')
  fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'owner@example.invalid' } })
  fireEvent.click(screen.getByRole('button', { name: 'Request reset link' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Please wait a moment')
  expect(screen.queryByText(/You can try again in/)).not.toBeInTheDocument()
  expect(apiClient.post).toHaveBeenCalledTimes(1)
})

it('keeps the same request identity after a network failure and warns about duplicate delivery', async () => {
  apiClient.post.mockRejectedValue({})
  page('request-reset')
  fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'owner@example.invalid' } })
  fireEvent.click(screen.getByRole('button', { name: 'Request reset link' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('may already have been accepted')
  const first = apiClient.post.mock.calls[0][1].request_id
  fireEvent.click(screen.getByRole('button', { name: 'Request reset link' }))
  await waitFor(() => expect(apiClient.post).toHaveBeenCalledTimes(2))
  expect(apiClient.post.mock.calls[1][1].request_id).toBe(first)
})

it('shows an uncertain verification result without automatically retrying', async () => {
  apiClient.get.mockResolvedValue({ data: { verified: false } })
  apiClient.post.mockRejectedValue({ response: { status: 409, data: { detail: 'Check your inbox. Reconciliation required.' } } })
  page('verification')
  await screen.findByText(/current email is not verified/)
  fireEvent.click(screen.getByRole('button', { name: 'Request verification link' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Reconciliation required')
  expect(apiClient.post).toHaveBeenCalledTimes(1)
})
