export class ApiError extends Error {
  readonly status: number
  readonly detail: unknown

  constructor(status: number, message: string, detail?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

type ApiOptions = Omit<RequestInit, 'body'> & {
  body?: unknown
}

export async function api<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const headers = new Headers(options.headers)
  let body: BodyInit | undefined
  if (options.body instanceof FormData || typeof options.body === 'string') {
    body = options.body
  } else if (options.body !== undefined) {
    headers.set('Content-Type', 'application/json')
    body = JSON.stringify(options.body)
  }

  const response = await fetch(path, { ...options, headers, body })
  const contentType = response.headers.get('content-type') ?? ''
  const payload: unknown = contentType.includes('application/json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    const detail =
      typeof payload === 'object' && payload !== null && 'detail' in payload
        ? (payload as { detail: unknown }).detail
        : payload
    const message =
      typeof detail === 'string' ? detail : `Request failed with status ${response.status}`
    throw new ApiError(response.status, message, detail)
  }
  return payload as T
}

export async function upload<T>(
  path: string,
  formData: FormData,
  onProgress?: (progress: number) => void,
): Promise<T> {
  if (!onProgress) {
    return api<T>(path, { method: 'POST', body: formData })
  }
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest()
    request.open('POST', path)
    request.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress(event.loaded / event.total)
    }
    request.onerror = () => reject(new ApiError(0, 'The upload could not be completed.'))
    request.onload = () => {
      let payload: unknown
      try {
        payload = JSON.parse(request.responseText)
      } catch {
        payload = request.responseText
      }
      if (request.status >= 200 && request.status < 300) {
        resolve(payload as T)
      } else {
        const message =
          typeof payload === 'object' && payload !== null && 'detail' in payload
            ? String((payload as { detail: unknown }).detail)
            : `Upload failed with status ${request.status}`
        reject(new ApiError(request.status, message, payload))
      }
    }
    request.send(formData)
  })
}
