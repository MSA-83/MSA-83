import { useToast } from '../hooks/useToast'

export function ToastContainer() {
  const { toasts, removeToast } = useToast()

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`px-4 py-3 rounded-lg shadow-lg text-sm flex items-center gap-3 animate-slide-in ${
            toast.type === 'success'
              ? 'bg-green-500/90 text-white'
              : toast.type === 'error'
              ? 'bg-red-500/90 text-white'
              : 'bg-titanium-700 text-titanium-100'
          }`}
        >
          <span>{toast.message}</span>
          <button
            onClick={() => removeToast(toast.id)}
            className="ml-2 opacity-70 hover:opacity-100"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  )
}
