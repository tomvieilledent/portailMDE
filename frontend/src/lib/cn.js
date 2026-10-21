/** Concatène des classes CSS en ignorant les valeurs vides. */
export function cn(...classes) {
  return classes.filter(Boolean).join(' ')
}
