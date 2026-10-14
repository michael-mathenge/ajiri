# Ajiri design system

Phase 1 uses JavaScript/JSX, Tailwind CSS 4 (Vite plugin), lucide-react and locally owned shadcn-style components built on Radix Dialog, Toast and Slot. Components are adapted for Ajiri rather than installed as an opaque UI runtime. Native inputs and selects retain mobile keyboard and picker behaviour. No TypeScript migration or backend runtime changes are required.

## Tokens

Tokens live in `ajiri-frontend/src/index.css`; `[data-theme=dark]` overrides semantic colours. Use semantic tokens, not per-page colour literals.

| Token | Light | Dark | Usage |
| --- | --- | --- | --- |
| `--background` | `#f5f7f6` | `#101e1b` | Page |
| `--surface` | `#ffffff` | `#182b26` | Cards and controls |
| `--foreground` | `#172e2a` | `#edf6f1` | Main text |
| `--muted` | `#526762` | `#b2c8bf` | Supporting text |
| `--primary` | `#0b6255` | `#8ce0bf` | Actions, links, focus |
| `--primary-foreground` | `#ffffff` | `#102c23` | Primary action text |
| `--soft` | `#e6f3ee` | `#233f34` | Match badges, subtle emphasis |
| `--danger` | `#b42332` | `#ffacb4` | Errors |
| `--input-border` | `#7c918a` | `#789c89` | Identifiable control boundaries |

System fonts avoid external font requests. Type scale: 14, 16, 18, 22px and a fluid 32–54px display heading. Spacing uses a 4px base (`--space`); standard gaps are 16, 20, 24, 28 and 32px. Card radius is 16px, controls approximately 10px; shadows are subtle and never the only boundary.

## Components

Import from `src/components/ui.jsx` and hooks from `src/hooks`.

| Component | Usage rule |
| --- | --- |
| `Button` | `default`, `outline`, `ghost`; use `asChild` with a Link for navigation. Defaults to type=button. Set type=submit explicitly. |
| `Input`, `Select`, `Textarea` | Always supply an associated visible label and a stable id. Native select is intentional for low-bandwidth mobile forms. |
| `Badge` | Short supplementary text, never the only explanation of a state. |
| `Card` | Group related content; headings describe the group. |
| `Dialog` | Supply trigger, title and description. Radix traps focus, supports Escape and restores trigger focus. |
| `ToastProvider`, `useToast()` | App-level brief confirmations; persistent errors stay inline. Toasts are dismissible. |
| `Skeleton`, `LoadingState` | Announce a single loading status; decorative placeholders are hidden from assistive technology. |
| `EmptyState` | Explain why the list is empty and provide a useful next action. |
| `ErrorState` | Show a readable error and offer a retry for failed reads. |
| `Pagination` | Use API next/previous flags; never infer that more records exist. |
| `MatchScore` | Accepts number or null. Null is hidden; zero is shown. 70%+ receives strong-match styling. |
| `ApplicationStatus` | Text labels for draft, ready_for_review, sent and dismissed. |
| `AppShell` | Responsive nav, skip link, main landmark, theme control and footer. |

Example:

```jsx
import { Link } from 'react-router-dom'
import { Button, Card, Input } from './components/ui'

<Card>
  <label htmlFor="title">Job title</label>
  <Input id="title" name="title" />
  <Button asChild><Link to="/applications">Review applications</Link></Button>
</Card>
```

## Interaction and accessibility

- Start with a single column. At 640px jobs form two columns; at 900px the desktop nav, full search form and detail sidebar appear.
- Controls have at least 44px height. Keep input text at 16px to avoid automatic mobile zoom.
- Text uses AA contrast pairs; preserve primary/primary-foreground and muted/surface pairings. Error text must remain readable on both surfaces.
- Use visible focus rings. Do not remove outlines except on the programmatically focused main landmark.
- Icon-only controls need accessible labels; decorative icons use aria-hidden.
- Mobile navigation uses an ordinary disclosure button, not an ARIA menu. Collapsed links are removed from keyboard navigation by display:none.
- Motion respects prefers-reduced-motion. Loading skeletons do not animate in that mode.
- Theme defaults to the system preference on first visit; explicit selection persists. Initial HTML applies it before React renders.
- Job descriptions render as text with preserved line breaks; do not introduce untrusted HTML rendering.

## Data and authentication

Keep `src/api/client.js` as the single API client. Existing JWT refresh/cookie behaviour is unchanged. Route guards use local access-token presence for navigation only; Django remains the authority. Expired access tokens still reach the interceptor and silently refresh. Login returns to the requested internal route.

Job search submits title, location and job_type to the existing API. Search filters and page live in the URL; changing filters resets pagination. API reads cancel when obsolete, preventing stale filter responses from replacing newer results. Applications and Notifications use the same loading/error/empty/pagination patterns while their feature work remains in Phase 2.

Route-level lazy imports defer screen code. No web font, image library, backend service or production Node process is added. PythonAnywhere serves the built static files as before.

## Verification (PowerShell)

```powershell
cd C:\dev\ajiri\ajiri-frontend
npm ci
npm run lint
npm run build
$env:VITE_API_BASE_URL = 'http://localhost:8000/api'
npm run dev
```

Expected: install succeeds, lint reports no warnings/errors, build exits 0. With the local Django server running, open the Vite URL. Keep hostnames consistent (localhost on both sides) so existing cookies/CORS settings apply.

Backend checks required before commits:

```powershell
cd C:\dev\ajiri\ajiri-backend
$env:DEBUG = 'True'
$env:EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
```

Expected: system check has no issues; 19 tests pass. In a restrictive sandbox, point TEMP and TMP to an existing writable directory before tests.

Regenerate the committed build in a fresh shell without a development API URL:

```powershell
cd C:\dev\ajiri
Remove-Item Env:VITE_API_BASE_URL -ErrorAction SilentlyContinue
.\ajiri-backend\scripts\build_frontend.ps1
```

Before merging, verify in the browser at 360px, 390px and desktop width: logged-out redirects; login return path; invalid credentials; theme persistence; keyboard focus; dialog Escape/focus restoration; filters, empty results, pagination and Back; job detail and application preparation; existing application and notification actions. Backend schema/API gaps remain Phase 2 work.
