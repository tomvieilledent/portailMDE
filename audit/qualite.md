# Audit Qualité et RGPD

## Tour 1 — note : 63/100
À corriger :
- [majeur] frontend/src — aucune page mentions légales / politique de confidentialité, ni information ou consentement à la collecte (email, nom, téléphone, carte de visite) → ajouter les pages et liens (pied de page, connexion)
- [majeur] backend/app/services/users.py:155 — suppression uniquement logique (deleted_at), données personnelles conservées indéfiniment, pas d'anonymisation ni de suppression des fichiers avatar/carte → anonymiser les champs personnels et supprimer les fichiers à la suppression
- [majeur] backend/app/api/v1/users.py — pas d'export des données personnelles (accès/portabilité) ni de suppression de compte par l'utilisateur lui-même (interdite en users.py:158) → endpoints export et auto-suppression/demande d'effacement
- [mineur] backend/app/services/mailer.py:39 — le backend console journalise le corps des emails (liens de réinitialisation, données perso) → ne journaliser que le sujet, interdire console en production
- [mineur] backend/app/services/mailer.py:56 — adresse email du destinataire dans les journaux d'erreur → masquer ou utiliser un identifiant
- [mineur] backend/app/services/auth.py:88 — durée de conservation définie pour les jetons et actualités (config.py:27) mais aucune pour comptes supprimés/messages/notifications → définir et purger (tâche planifiée)
Corrigé depuis le tour précédent : (premier tour)
Corrections appliquées : pages légales + liens + mention à la connexion ; anonymisation à la suppression (fichiers effacés) ; export et auto-suppression (/users/me) ; mailer sans corps ni email en clair, console interdit en production ; purge quotidienne (jetons, notifications 90 j, messages supprimés 30 j).

## Tour 2 — note : 97/100
À corriger :
- [mineur] backend/app/services/users.py:180 — l'anonymisation conserve les messages du compte supprimé (contenu et pièces jointes, Message.author_id) sans purge ni mention dans la politique → supprimer/anonymiser ces messages ou documenter leur conservation
Corrigé depuis le tour précédent : pages légales + liens + mention à la connexion ; anonymisation à la suppression avec effacement des fichiers avatar/carte ; export (/users/me/export) et auto-suppression (/users/me) avec UI profil ; mailer sans corps ni email en clair, console/memory refusés en production ; purge quotidienne planifiée (jetons, notifications 90 j, messages supprimés 30 j). Pas de régression constatée (tests non exécutés : python absent du shell).
Corrections appliquées : anonymisation vide et détache les messages du compte supprimé (contenu, pièces jointes effacées, soft-delete puis purge).

## Tour 3 — note : 100/100
À corriger : aucun
Corrigé depuis le tour précédent : anonymisation des messages du compte supprimé (users.py:_anonymize : contenu vidé, pièces jointes effacées, auteur détaché via author_id nullable, soft-delete puis purge à 30 j), couvert par test_delete_own_account_erases_messages. Pas de régression constatée (tests non exécutés : pytest absent du shell).
