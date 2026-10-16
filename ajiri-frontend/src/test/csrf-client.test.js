import { beforeEach, expect, it, vi } from 'vitest'

let client, adapter, calls
const ok = (config, data = {}) => Promise.resolve({ config, data, status: 200, statusText: 'OK', headers: {} })
const fail = (config, status, data = {}) => Promise.reject({ config, response: { status, data } })
beforeEach(async () => {
  vi.resetModules()
  localStorage.clear()
  calls = []
  const axios = (await import('axios')).default
  adapter = vi.fn((config) => {
    calls.push(config)
    if (config.url.endsWith('/csrf/')) return ok(config, { csrfToken: 'masked-token' })
    return ok(config, { access: 'new-access' })
  })
  axios.defaults.adapter = adapter
  client = (await import('../api/client')).default
})

it('bootstraps without a stale JWT, attaches CSRF and renews after login', async () => {
  localStorage.setItem('access_token', 'stale')
  await client.post('/accounts/login/', {})
  const login = calls.find(c => c.url === '/accounts/login/')
  expect(login.headers['X-CSRFToken']).toBe('masked-token')
  expect(login.headers.Authorization).toBeUndefined()
  const bootstraps = calls.filter(c => c.url.endsWith('/csrf/'))
  expect(bootstraps).toHaveLength(2)
  expect(bootstraps.every(c => !c.headers.Authorization && c.withCredentials)).toBe(true)
})

it('retries an identified CSRF rejection once and preserves existing session', async () => {
  localStorage.setItem('access_token', 'existing')
  const base = adapter.getMockImplementation()
  let posts = 0
  adapter.mockImplementation(config => config.url === '/accounts/logout/'
    ? (++posts, fail(config, 403, { code: 'csrf_failed' })) : base(config))
  await expect(client.post('/accounts/logout/', {})).rejects.toMatchObject({ response: { status: 403 } })
  expect(posts).toBe(2)
  expect(localStorage.getItem('access_token')).toBe('existing')
})

it('shares one silent refresh across parallel expired requests', async () => {
  localStorage.setItem('access_token', 'old')
  const base = adapter.getMockImplementation()
  let refreshes = 0
  adapter.mockImplementation(async config => {
    if (config.url.endsWith('/refresh/')) {
      refreshes++
      await Promise.resolve()
      return ok(config, { access: 'new' })
    }
    if (config.url.startsWith('/protected')) {
      return config.headers.Authorization === 'Bearer new' ? ok(config) : fail(config, 401)
    }
    return base(config)
  })
  await Promise.all([client.get('/protected-one'), client.get('/protected-two')])
  expect(refreshes).toBe(1)
  expect(localStorage.getItem('access_token')).toBe('new')
})

it.each([403, 429, null])('does not erase access on a refresh failure %s', async status => {
  localStorage.setItem('access_token', 'existing')
  const base = adapter.getMockImplementation()
  adapter.mockImplementation(config => {
    if (config.url === '/protected') return fail(config, 401)
    if (config.url.endsWith('/refresh/')) return status ? fail(config, status) : Promise.reject({ config })
    return base(config)
  })
  await expect(client.get('/protected')).rejects.toBeDefined()
  expect(localStorage.getItem('access_token')).toBe('existing')
})

it('does not retry ordinary forbidden mutations', async () => {
  adapter.mockImplementation(config => fail(config, 403))
  await expect(client.post('/jobs/1/apply/')).rejects.toBeDefined()
  expect(adapter).toHaveBeenCalledTimes(1)
})
