import { expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Subscriptions from '../pages/Subscriptions'

it('shows all proposed KES prices with explicit availability', () => {
  render(
    <MemoryRouter>
      <Subscriptions />
    </MemoryRouter>
  )
  for (const price of ['KES 0', 'KES 499', 'KES 999'])
    expect(screen.getByText(price)).toBeVisible()
  for (const plan of ['Free', 'Starter', 'Pro'])
    expect(screen.getByRole('heading', { name: plan })).toBeVisible()
  expect(screen.getAllByText('Not yet purchasable')).toHaveLength(3)
})
it('offers real navigation without a checkout or payment controls', () => {
  render(
    <MemoryRouter>
      <Subscriptions />
    </MemoryRouter>
  )
  expect(screen.getByRole('link', { name: 'Explore jobs' })).toHaveAttribute(
    'href',
    '/'
  )
  expect(screen.queryByRole('button')).not.toBeInTheDocument()
  expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
  expect(screen.getByText(/No payment details are collected/)).toBeVisible()
})
