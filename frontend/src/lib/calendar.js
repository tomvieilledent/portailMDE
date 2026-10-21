const pad = (n) => String(n).padStart(2, '0')

/** Date locale au format `YYYY-MM-DD` (sans passer par l'UTC, qui décalerait le jour). */
export const toISODate = (date) =>
  `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`

/** Grille d'un mois : semaines (lundi → dimanche) incluant les jours des mois voisins. */
export function buildMonthGrid(year, month) {
  const first = new Date(year, month, 1)
  const offset = (first.getDay() + 6) % 7 // lundi = 0
  const start = new Date(year, month, 1 - offset)
  const weeks = []
  for (let w = 0; w < 6; w += 1) {
    const week = []
    for (let d = 0; d < 7; d += 1) {
      const date = new Date(start.getFullYear(), start.getMonth(), start.getDate() + w * 7 + d)
      week.push({ date, iso: toISODate(date), inMonth: date.getMonth() === month })
    }
    weeks.push(week)
  }
  // Les semaines finales entièrement hors du mois sont inutiles.
  while (!weeks[weeks.length - 1].some((day) => day.inMonth)) weeks.pop()
  return weeks
}

export const WEEKDAYS = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']

export const monthLabel = (year, month) =>
  new Date(year, month, 1).toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' })

export const formatLongDate = (iso) =>
  new Date(`${iso}T00:00:00`).toLocaleDateString('fr-FR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  })

/** `HH:MM:SS` → `HH:MM` ; null reste null. */
export const shortTime = (time) => (time ? time.slice(0, 5) : null)
