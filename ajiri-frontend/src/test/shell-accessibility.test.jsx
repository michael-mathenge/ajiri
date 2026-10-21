import { expect, it, vi } from 'vitest'
import { render, screen } from './test-utils'
import { MemoryRouter } from 'react-router-dom'
import AppShell from '../components/AppShell'
import { AuthContext } from '../hooks/useAuth'

it('keeps all visible brand words in the home link accessible name', () => {
  render(
    <MemoryRouter>
      <AuthContext.Provider value={{ signedIn: false, setSignedIn: vi.fn() }}>
        <AppShell />
      </AuthContext.Provider>
    </MemoryRouter>
  )
  const brand = screen.getByRole('link', { name: 'Ajiri Kenya home' })
  expect(brand).toHaveTextContent(/ajiri.*KENYA/)
  expect(brand).toHaveAttribute('href', '/')
})
