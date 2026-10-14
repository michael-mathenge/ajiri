import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Remove prior screens between tests so their labels cannot affect later flows.
// see docs/CONCEPTS.md#component-flow-tests

afterEach(() => cleanup())
