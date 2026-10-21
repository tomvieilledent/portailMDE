/** Génération et export d'une carte de visite à partir des informations d'un profil. */

/** Nom affiché d'une personne (prénom + nom), à défaut son email. */
function displayName(person) {
  return [person.first_name, person.last_name].filter(Boolean).join(' ') || person.email
}

/** Lignes de la carte : nom, fonction, entreprise, email, téléphone (champs vides ignorés). */
export function cardLines(person) {
  return {
    name: displayName(person),
    job: person.job_title || '',
    company: person.company?.name || '',
    email: person.email || '',
    phone: person.phone || '',
  }
}

/** Échappe une valeur de champ vCard (virgules, points-virgules, retours à la ligne). */
const vcardEscape = (value) =>
  String(value)
    .replace(/\\/g, '\\\\')
    .replace(/\n/g, '\\n')
    .replace(/,/g, '\\,')
    .replace(/;/g, '\\;')

/** Contenu d'un fichier vCard 3.0 (importable dans un carnet d'adresses). */
export function buildVCard(person) {
  const { name, job, company, email, phone } = cardLines(person)
  const lines = [
    'BEGIN:VCARD',
    'VERSION:3.0',
    `N:${vcardEscape(person.last_name || '')};${vcardEscape(person.first_name || '')};;;`,
    `FN:${vcardEscape(name)}`,
  ]
  if (company) lines.push(`ORG:${vcardEscape(company)}`)
  if (job) lines.push(`TITLE:${vcardEscape(job)}`)
  if (email) lines.push(`EMAIL;TYPE=INTERNET:${vcardEscape(email)}`)
  if (phone) lines.push(`TEL;TYPE=WORK,VOICE:${vcardEscape(phone)}`)
  lines.push('END:VCARD')
  return lines.join('\r\n') + '\r\n'
}

/** Dessine la carte (format 85 × 55 mm, 1050 × 675 px) dans un canvas. */
export function drawBusinessCard(person, canvas) {
  const { name, job, company, email, phone } = cardLines(person)
  const width = 1050
  const height = 675
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, width, height)
  ctx.fillStyle = '#3f6b16'
  ctx.fillRect(0, 0, 36, height)
  const font = 'system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
  ctx.textBaseline = 'alphabetic'
  ctx.fillStyle = '#0f172a'
  ctx.font = `700 64px ${font}`
  ctx.fillText(name, 100, 190, width - 160)
  if (job) {
    ctx.fillStyle = '#475569'
    ctx.font = `400 38px ${font}`
    ctx.fillText(job, 100, 255, width - 160)
  }
  if (company) {
    ctx.fillStyle = '#3f6b16'
    ctx.font = `600 42px ${font}`
    ctx.fillText(company, 100, 335, width - 160)
  }
  ctx.fillStyle = '#334155'
  ctx.font = `400 36px ${font}`
  let y = 500
  if (email) ctx.fillText(email, 100, y, width - 160), (y += 60)
  if (phone) ctx.fillText(phone, 100, y, width - 160)
  return canvas
}

/** Déclenche le téléchargement d'un blob sous le nom de fichier donné. */
function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

/** Nom de fichier sûr, dérivé du nom de la personne. */
const fileBase = (person) =>
  displayName(person)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-zA-Z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .toLowerCase() || 'carte-de-visite'

/** Exporte la carte générée au format PNG. */
export function exportCardPng(person) {
  const canvas = drawBusinessCard(person, document.createElement('canvas'))
  canvas.toBlob((blob) => blob && saveBlob(blob, `${fileBase(person)}.png`), 'image/png')
}

/** Exporte la carte au format vCard (.vcf). */
export function exportCardVCard(person) {
  saveBlob(
    new Blob([buildVCard(person)], { type: 'text/vcard;charset=utf-8' }),
    `${fileBase(person)}.vcf`,
  )
}
