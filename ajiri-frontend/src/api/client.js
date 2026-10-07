import axios from 'axios'

// Where the Django API lives. Vite replaces import.meta.env.VITE_API_BASE_URL
// with a fixed value AT BUILD TIME, taken from .env.development (npm run dev:
// the backend on another port) or .env.production (npm run build: the same
// site that serves this app, so just the relative path /api).
// See docs/CONCEPTS.md#vite-env-variables
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

// Uploaded files (CVs, cover letters) are served by the same host as the API.
// The API returns absolute URLs built from whatever scheme/host Django thinks it
// has, which can be wrong behind a proxy (http:// on an https:// site), so keep
// only the path and attach it to the origin this app already knows is right.
const MEDIA_ORIGIN = new URL(API_BASE_URL, window.location.href).origin
export const mediaUrl = (url) => MEDIA_ORIGIN + new URL(url, MEDIA_ORIGIN).pathname

// Endpoints that must NEVER carry an Authorization header — they're
// how you GET a token in the first place, or don't need one at all.
// Sending a stale/expired token here causes DRF's JWTAuthentication to
// reject the request before the view even runs, even though these
// views are AllowAny — permission and authentication are separate
// steps. See docs/CONCEPTS.md#stale-token-on-public-endpoints
const PUBLIC_ENDPOINTS = ['/accounts/login/', '/accounts/register/', '/accounts/refresh/']

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  // Required so the browser sends the httpOnly refresh_token cookie on
  // requests, and accepts Set-Cookie from responses — cross-origin
  // (5173 -> 8000) cookies are opt-in on both sides. See
  // docs/CONCEPTS.md#cors-credentials
  withCredentials: true,
})

apiClient.interceptors.request.use((config) => {
  const isPublicEndpoint = PUBLIC_ENDPOINTS.some((path) => config.url.includes(path))

  if (!isPublicEndpoint) {
    const accessToken = localStorage.getItem('access_token')
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`
    }
  }

  return config
})

// Response interceptor: if a PROTECTED request comes back 401 (access
// token expired — normal after 15 minutes, not an error condition),
// silently use the refresh_token cookie to get a new access token and
// retry the original request ONCE. Only if that also fails do we give
// up and send the user to /login. See docs/CONCEPTS.md#refresh-on-401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const isPublicEndpoint = PUBLIC_ENDPOINTS.some((path) => originalRequest.url.includes(path))

    if (error.response?.status === 401 && !isPublicEndpoint && !originalRequest._retry) {
      // Marks this request so we never attempt a second silent refresh
      // for the SAME original request — prevents an infinite loop if
      // the refreshed token still somehow fails.
      originalRequest._retry = true

      try {
        // Deliberately using plain axios here, NOT apiClient — calling
        // apiClient would run back through these same interceptors,
        // risking recursive refresh attempts if this call itself 401s.
        const refreshResponse = await axios.post(
          `${API_BASE_URL}/accounts/refresh/`,
          {},
          { withCredentials: true }
        )

        const newAccessToken = refreshResponse.data.access
        localStorage.setItem('access_token', newAccessToken)

        // Update the original request's header and resend it — the
        // user never sees the failure, the page just loads normally.
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return apiClient(originalRequest)
      } catch (refreshError) {
        // Refresh token is ALSO invalid/expired (e.g. the full 7-day
        // window passed) — nothing left to try, log the user out.
        localStorage.removeItem('access_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient