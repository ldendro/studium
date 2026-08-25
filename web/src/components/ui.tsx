import clsx from 'clsx'
import { LoaderCircle, SearchX } from 'lucide-react'
import type {
  ButtonHTMLAttributes,
  HTMLAttributes,
  InputHTMLAttributes,
  PropsWithChildren,
  ReactNode,
  TextareaHTMLAttributes,
} from 'react'
import type { NoticeTone } from '../lib/types'

export function Button({
  variant = 'secondary',
  size = 'medium',
  loading,
  children,
  className,
  disabled,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'small' | 'medium' | 'large'
  loading?: boolean
}) {
  return (
    <button
      className={clsx('button', `button--${variant}`, `button--${size}`, className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <LoaderCircle className="spin" size={16} aria-hidden />}
      {children}
    </button>
  )
}

export function IconButton({
  label,
  className,
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { label: string }) {
  return (
    <button className={clsx('icon-button', className)} aria-label={label} title={label} {...props}>
      {children}
    </button>
  )
}

export function Badge({
  tone = 'neutral',
  children,
  className,
}: PropsWithChildren<{ tone?: NoticeTone | 'accent' | 'blue'; className?: string }>) {
  return <span className={clsx('badge', `badge--${tone}`, className)}>{children}</span>
}

export function Panel({
  className,
  children,
  ...props
}: PropsWithChildren<HTMLAttributes<HTMLDivElement>>) {
  return (
    <section className={clsx('panel', className)} {...props}>
      {children}
    </section>
  )
}

export function Field({
  label,
  hint,
  children,
  className,
}: PropsWithChildren<{ label: string; hint?: string; className?: string }>) {
  return (
    <label className={clsx('field', className)}>
      <span className="field__label">{label}</span>
      {children}
      {hint && <span className="field__hint">{hint}</span>}
    </label>
  )
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={clsx('input', props.className)} />
}

export function Textarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={clsx('textarea', props.className)} />
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  compact = false,
}: {
  icon?: ReactNode
  title: string
  description: string
  action?: ReactNode
  compact?: boolean
}) {
  return (
    <div className={clsx('empty-state', compact && 'empty-state--compact')}>
      <div className="empty-state__icon">{icon ?? <SearchX size={24} />}</div>
      <h3>{title}</h3>
      <p>{description}</p>
      {action && <div className="empty-state__action">{action}</div>}
    </div>
  )
}

export function Skeleton({ className }: { className?: string }) {
  return <span className={clsx('skeleton', className)} aria-hidden />
}

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow: string
  title: string
  description?: string
  actions?: ReactNode
}) {
  return (
    <header className="page-header">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        {description && <p className="page-header__description">{description}</p>}
      </div>
      {actions && <div className="page-header__actions">{actions}</div>}
    </header>
  )
}

export function Progress({ value, label }: { value: number; label?: string }) {
  const normalized = Math.max(0, Math.min(1, value))
  return (
    <div className="progress" aria-label={label} role="progressbar" aria-valuenow={normalized * 100}>
      <span style={{ width: `${normalized * 100}%` }} />
    </div>
  )
}
