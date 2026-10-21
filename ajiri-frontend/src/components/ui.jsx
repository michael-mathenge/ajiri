import { lazy, Suspense, useState } from 'react'
import { ToastContext } from '../hooks/useToast'
import { Slot } from '@radix-ui/react-slot'
import { cva } from 'class-variance-authority'
import { ArrowLeft, ArrowRight, SearchX } from 'lucide-react'
import { cn } from '../lib/utils'

const buttonVariants = cva('btn', {
  variants: {
    variant: {
      default: 'btn-primary',
      outline: 'btn-outline',
      ghost: 'btn-ghost',
    },
  },
  defaultVariants: { variant: 'default' },
})

// Slot keeps a linked button as one accessible anchor, rather than nested controls.
// see docs/CONCEPTS.md#composable-ui
export function Button({
  asChild = false,
  variant,
  className,
  type = 'button',
  ...props
}) {
  const Component = asChild ? Slot : 'button'
  return (
    <Component
      {...(!asChild && { type })}
      className={cn(buttonVariants({ variant }), className)}
      {...props}
    />
  )
}
export function Input({ className, ...props }) {
  return <input className={cn('input', className)} {...props} />
}
export function Select({ className, ...props }) {
  return <select className={cn('input', className)} {...props} />
}
export function Textarea({ className, ...props }) {
  return <textarea className={cn('input', className)} {...props} />
}
export function Card({ className, ...props }) {
  return <div className={cn('card', className)} {...props} />
}
export function Badge({ className, ...props }) {
  return <span className={cn('badge', className)} {...props} />
}
export function MatchScore({ score }) {
  if (score == null) return null
  return (
    <Badge className={score >= 70 ? 'badge-success' : ''}>
      {score}% skill match
    </Badge>
  )
}
export function ApplicationStatus({ status }) {
  const labels = {
    draft: 'Draft',
    ready_for_review: 'Ready for review',
    sent: 'Sent',
    dismissed: 'Dismissed',
  }
  return (
    <Badge className={status === 'sent' ? 'badge-success' : ''}>
      {labels[status] || status}
    </Badge>
  )
}
export function Skeleton({ className, ...props }) {
  return (
    <div aria-hidden="true" className={cn('skeleton', className)} {...props} />
  )
}
export function LoadingState({ label = 'Loading…' }) {
  return (
    <div role="status" aria-label={label} className="stack">
      <span className="sr-only">{label}</span>
      {[1, 2, 3].map((i) => (
        <Card key={i}>
          <Skeleton className="h-5 w-2/3" />
          <Skeleton className="mt-4 h-4 w-1/2" />
          <Skeleton className="mt-4 h-4 w-1/3" />
        </Card>
      ))}
    </div>
  )
}
export function EmptyState({ title, children, action }) {
  return (
    <Card className="empty-state">
      <SearchX size={32} aria-hidden="true" />
      <h2>{title}</h2>
      <p className="muted">{children}</p>
      {action}
    </Card>
  )
}
export function ErrorState({ children, onRetry }) {
  return (
    <Card className="error-panel" role="alert">
      <h2>Something went wrong</h2>
      <p>{children}</p>
      {onRetry && (
        <Button variant="outline" onClick={onRetry}>
          Try again
        </Button>
      )}
    </Card>
  )
}
export function Pagination({ page, hasNext, hasPrevious, onChange }) {
  return (
    <nav className="pagination" aria-label="Pagination">
      <Button
        variant="outline"
        disabled={!hasPrevious}
        onClick={() => onChange(page - 1)}
      >
        <ArrowLeft size={16} aria-hidden="true" />
        Previous
      </Button>
      <span aria-live="polite">Page {page}</span>
      <Button
        variant="outline"
        disabled={!hasNext}
        onClick={() => onChange(page + 1)}
      >
        Next
        <ArrowRight size={16} aria-hidden="true" />
      </Button>
    </nav>
  )
}
// Notifications need their primitives only after an action produces a toast.
// see docs/CONCEPTS.md#schema-forms
const ToastMessage = lazy(() => import('./ToastMessage'))

export function ToastProvider({ children }) {
  const [toast, setToast] = useState(null)
  return (
    <ToastContext.Provider
      value={(title, description) =>
        setToast({ title, description, key: Date.now() })
      }
    >
      {children}
      {toast && (
        <Suspense fallback={null}>
          <ToastMessage toast={toast} />
        </Suspense>
      )}
    </ToastContext.Provider>
  )
}
