/** Construction des URL des fichiers envoyés. */

/** URL publique d'un fichier envoyé (le backend renvoie un chemin relatif à `/uploads`). */
export const uploadUrl = (path) => (path ? `/uploads/${path}` : null)
