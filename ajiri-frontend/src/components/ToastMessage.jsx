import * as ToastPrimitive from '@radix-ui/react-toast'
import { X } from 'lucide-react'
import { Button } from './ui'

export default function ToastMessage({ toast }) {
  return (
    <ToastPrimitive.Provider swipeDirection="right">
      <ToastPrimitive.Root key={toast.key} className="toast" defaultOpen>
        <ToastPrimitive.Title className="font-semibold">
          {toast.title}
        </ToastPrimitive.Title>
        {toast.description && (
          <ToastPrimitive.Description className="muted">
            {toast.description}
          </ToastPrimitive.Description>
        )}
        <ToastPrimitive.Close asChild>
          <Button variant="ghost" aria-label="Dismiss notification">
            <X size={18} />
          </Button>
        </ToastPrimitive.Close>
      </ToastPrimitive.Root>
      <ToastPrimitive.Viewport className="toast-viewport" />
    </ToastPrimitive.Provider>
  )
}
