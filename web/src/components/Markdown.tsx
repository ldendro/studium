import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { useMemo } from 'react'

marked.setOptions({
  gfm: true,
  breaks: false,
})

export function Markdown({ value, className = '' }: { value: string; className?: string }) {
  const html = useMemo(() => {
    const rendered = marked.parse(value, { async: false }) as string
    return DOMPurify.sanitize(rendered, {
      USE_PROFILES: { html: true },
      ADD_ATTR: ['target'],
    })
  }, [value])

  return <div className={`markdown ${className}`} dangerouslySetInnerHTML={{ __html: html }} />
}
