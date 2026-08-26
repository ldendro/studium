import type { ReactNode } from 'react'
import { PageHeader, Panel } from '../components/ui'

export function PlaceholderPage({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string
  title: string
  description: string
  children?: ReactNode
}) {
  return (
    <div className="page">
      <PageHeader eyebrow={eyebrow} title={title} description={description} />
      <Panel className="placeholder-panel">{children}</Panel>
    </div>
  )
}
