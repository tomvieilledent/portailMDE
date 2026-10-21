// Applique le thème avant le premier rendu pour éviter un flash blanc.
try {
  const saved = localStorage.getItem('theme')
  const dark = saved ? saved === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches
  document.documentElement.classList.toggle('dark', dark)
} catch {
  /* stockage indisponible */
}
