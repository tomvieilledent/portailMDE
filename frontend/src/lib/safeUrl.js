/** Retourne l'URL si elle est en http(s), sinon `undefined` (bloque `javascript:` et autres schémas). */
export const safeHref = (url) => {
  if (!url) return undefined
  try {
    const { protocol } = new URL(url, window.location.origin)
    return protocol === 'http:' || protocol === 'https:' ? url : undefined
  } catch {
    return undefined
  }
}
