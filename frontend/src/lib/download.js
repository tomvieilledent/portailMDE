import { tokens } from './tokens'

/** Télécharge un fichier protégé (en-tête Authorization) puis le propose à l'utilisateur. */
export async function downloadFile(url, filename) {
  const response = await fetch(url, { headers: { Authorization: `Bearer ${tokens.access}` } })
  if (!response.ok) throw new Error('Téléchargement impossible')
  const objectUrl = URL.createObjectURL(await response.blob())
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = filename
  link.click()
  URL.revokeObjectURL(objectUrl)
}
