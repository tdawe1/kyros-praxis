const seen = new Set()
export function withIdempotency(key, fn) {
  if (seen.has(key)) return { status: 'duplicate' }
  seen.add(key)
  return fn()
}

