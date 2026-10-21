# Quiz de révision — Review technique MDE Dashboard

**150 questions** (120 backend + 30 frontend). Les réponses sont **masquées** : clique sur une question (▶) pour la dérouler. Idéal pour t'auto-interroger.

> Astuce : lis la question, formule ta réponse **à voix haute**, puis déroule pour vérifier.

---

# PARTIE BACKEND (120)

## A. Architecture & couches (1–15)

<details><summary><b>B1.</b> Décris l'architecture globale du backend.</summary>

API Flask en couches : **resources** (HTTP) → **services** (métier) → **facades** (SQL) → **ORM/base**. Chaque couche ne parle qu'à la suivante.
</details>

<details><summary><b>B2.</b> Pourquoi une architecture en couches ?</summary>

Séparation des responsabilités : testabilité, remplaçabilité (changer de base sans toucher aux resources), et une seule raison de changer par fichier.
</details>

<details><summary><b>B3.</b> Que contient le dossier <code>api/resources</code> ?</summary>

Les endpoints HTTP, une classe <code>Resource</code> par thème et une méthode par verbe HTTP (get/post/patch/delete).
</details>

<details><summary><b>B4.</b> Rôle exact d'une resource ?</summary>

Lire la requête, authentifier (JWT), autoriser (<code>_can</code>), valider, déléguer au service, renvoyer un dict + code HTTP.
</details>

<details><summary><b>B5.</b> À quoi sert la couche services (<code>layer.py</code>) ?</summary>

Exposer les cas d'usage métier via une interface stable, indépendante du transport HTTP. Elle enveloppe les facades.
</details>

<details><summary><b>B6.</b> À quoi sert une facade ?</summary>

Encapsuler tous les accès SQLAlchemy (CRUD, transactions) et renvoyer des <code>dict</code> sérialisables — jamais d'objet ORM.
</details>

<details><summary><b>B7.</b> Quel type de donnée circule entre l'API et les services ?</summary>

Des objets Python (arguments à la descente, <code>dict</code> à la remontée). **Pas de JSON** : le JSON n'existe qu'entre le client et l'API.
</details>

<details><summary><b>B8.</b> Qui convertit le JSON en objets Python ?</summary>

La couche API (Flask-RESTful) fait <code>JSON ↔ dict</code>. La facade fait <code>objet ORM ↔ dict</code>.
</details>

<details><summary><b>B9.</b> Comment une URL est-elle reliée à une resource ?</summary>

Dans <code>app.py</code> via <code>api.add_resource(MaResource, '/mon-url')</code>. Une resource peut avoir plusieurs alias d'URL.
</details>

<details><summary><b>B10.</b> Qu'est-ce que la fonction <code>create_app()</code> ?</summary>

Une *application factory* : elle construit et configure l'app Flask à la demande (utile pour dev/tests/prod avec des configs différentes).
</details>

<details><summary><b>B11.</b> Pourquoi Flask-RESTful plutôt que des routes Flask brutes ?</summary>

Il structure l'API en classes/méthodes (une ressource = une classe, un verbe = une méthode), plus lisible que des dizaines de <code>@app.route</code>.
</details>

<details><summary><b>B12.</b> Combien de couches et lesquelles ?</summary>

Quatre : API (resources), Services, Facades de persistance, ORM. + la base en dessous.
</details>

<details><summary><b>B13.</b> Où est la logique temps réel dans l'architecture ?</summary>

Dans <code>api/socket_events/</code> (handlers Socket.IO), au même niveau que les resources (couche API), s'appuyant sur les mêmes services/facades.
</details>

<details><summary><b>B14.</b> Qu'est-ce qui garantit qu'un module est chargé au démarrage ?</summary>

<code>app.py</code> importe explicitement les modèles ORM et les handlers de sockets pour que SQLAlchemy connaisse les tables et Socket.IO enregistre les événements.
</details>

<details><summary><b>B15.</b> Le backend est-il monolithique ou microservices ?</summary>

Monolithique modulaire : une seule application Flask, mais découpée en couches et modules par domaine.
</details>

## B. Authentification & JWT (16–33)

<details><summary><b>B16.</b> Comment fonctionne l'authentification ?</summary>

Par JWT : au login le serveur renvoie un access token + un refresh token ; le client envoie l'access token en <code>Authorization: Bearer</code>.
</details>

<details><summary><b>B17.</b> Différence access token / refresh token ?</summary>

L'access token (court) accède aux ressources ; le refresh token (long) sert uniquement à obtenir un nouvel access token via <code>/auth/refresh</code>.
</details>

<details><summary><b>B18.</b> Où est stockée l'identité dans le token ?</summary>

Dans le claim standard <code>sub</code> (l'<code>id</code> de l'utilisateur), récupéré via <code>get_jwt_identity()</code>.
</details>

<details><summary><b>B19.</b> Comment protège-t-on une route ?</summary>

Avec le décorateur maison <code>@jwt_required()</code> (dans <code>jwt_helpers.py</code>).
</details>

<details><summary><b>B20.</b> Pourquoi un décorateur JWT maison et pas celui de la lib ?</summary>

Pour renvoyer nos erreurs JSON normalisées (<code>{error:{code,message}}</code>) au lieu du format par défaut de la librairie.
</details>

<details><summary><b>B21.</b> Comment marche la déconnexion ?</summary>

On ajoute le <code>jti</code> du token à la <code>BLOCKLIST</code> ; un callback vérifie ce <code>jti</code> à chaque requête.
</details>

<details><summary><b>B22.</b> C'est quoi un <code>jti</code> ?</summary>

*JWT ID* : un identifiant unique inscrit dans le token. On stocke le <code>jti</code> (pas le token entier) pour révoquer.
</details>

<details><summary><b>B23.</b> Où sont stockés les tokens révoqués ?</summary>

Dans un <code>set()</code> Python **en mémoire** (<code>state.py</code>), **pas** en base de données. Perdu au redémarrage, non partagé.
</details>

<details><summary><b>B24.</b> Comment stockez-vous les mots de passe ?</summary>

Hashés avec <code>werkzeug.security.generate_password_hash</code> ; vérification via <code>check_password_hash</code>. Jamais en clair.
</details>

<details><summary><b>B25.</b> Où est validé le format de l'email / la longueur du mot de passe ?</summary>

Dans le modèle de domaine <code>User</code> (setters), avant la persistance : email via <code>email-validator</code>, mot de passe 8–256 caractères.
</details>

<details><summary><b>B26.</b> Comment marche le "mot de passe oublié" ?</summary>

<code>/auth/forgot-password</code> génère un JWT court (15 min) avec claim <code>purpose=pwd_reset</code> et envoie un lien ; <code>/auth/reset-password</code> vérifie ce claim.
</details>

<details><summary><b>B27.</b> Comment évitez-vous l'énumération de comptes ?</summary>

<code>/auth/forgot-password</code> renvoie toujours le même message, que le compte existe ou non.
</details>

<details><summary><b>B28.</b> Empêche-t-on un access token de servir à réinitialiser un mot de passe ?</summary>

Oui : le reset vérifie explicitement <code>purpose == 'pwd_reset'</code> ; un access token normal n'a pas ce claim.
</details>

<details><summary><b>B29.</b> Comment authentifie-t-on une connexion WebSocket ?</summary>

Le client passe le token dans <code>auth</code> à la connexion ; <code>handle_connect</code> le vérifie (<code>verify_token</code>) et refuse la connexion si invalide.
</details>

<details><summary><b>B30.</b> Que renvoie <code>/auth/register</code> ?</summary>

L'utilisateur créé + un access token + un refresh token → l'utilisateur est connecté immédiatement.
</details>

<details><summary><b>B31.</b> Quelle clé signe les tokens ? Où est-elle définie ?</summary>

<code>JWT_SECRET_KEY</code>, lue depuis l'environnement (<code>.env</code>). Après le correctif d'audit, l'app **refuse de démarrer** sans elle.
</details>

<details><summary><b>B32.</b> Que se passe-t-il si on change la clé JWT et qu'on redémarre ?</summary>

Tous les tokens existants deviennent invalides (signature non vérifiable) → les utilisateurs doivent se reconnecter.
</details>

<details><summary><b>B33.</b> Le décorateur gère-t-il le cas "refresh token" ?</summary>

Oui : <code>jwt_required(refresh=True)</code> exige un refresh token (utilisé par <code>/auth/refresh</code>).
</details>

## C. Rôles & permissions (34–41)

<details><summary><b>B34.</b> Quels rôles existent ?</summary>

Super admin, staff (droits granulaires), admin d'entreprise, utilisateur standard.
</details>

<details><summary><b>B35.</b> Quelles sont les permissions granulaires ?</summary>

<code>manage_companies</code>, <code>manage_users</code>, <code>manage_trainings</code>, <code>manage_news</code>.
</details>

<details><summary><b>B36.</b> Comment stocke-t-on les permissions d'un staff ?</summary>

En CSV dans la colonne <code>permissions</code> de la table <code>users</code>.
</details>

<details><summary><b>B37.</b> Comment vérifie-t-on un droit dans le code ?</summary>

Le helper <code>_can(user, permission)</code> : <code>True</code> si super admin, sinon si la permission est dans sa liste.
</details>

<details><summary><b>B38.</b> Un super admin a-t-il toutes les permissions ?</summary>

Oui, implicitement — <code>_can</code> renvoie toujours <code>True</code> pour lui.
</details>

<details><summary><b>B39.</b> C'est quoi un admin d'entreprise ?</summary>

Un utilisateur dont l'<code>admin_id</code> ou l'<code>admin_email</code> correspond à une entreprise ; il gère les comptes de **sa** société uniquement.
</details>

<details><summary><b>B40.</b> Le rôle "patron" est-il stocké en base ?</summary>

Non : il est **déduit** (l'utilisateur administre-t-il une entreprise ?). Le backend n'a pas de champ <code>role</code>.
</details>

<details><summary><b>B41.</b> Un admin d'entreprise peut-il créer des comptes partout ?</summary>

Non, uniquement dans sa propre entreprise. Seuls super admin et staff <code>manage_users</code> créent partout.
</details>

## D. Base de données, ORM & migrations (42–56)

<details><summary><b>B42.</b> Quel ORM utilisez-vous ?</summary>

SQLAlchemy.
</details>

<details><summary><b>B43.</b> Quelle base de données ?</summary>

SQLite en dev (<code>data.db</code>), PostgreSQL en prod, choisi via <code>DATABASE_URL</code>.
</details>

<details><summary><b>B44.</b> Comment passe-t-on de SQLite à PostgreSQL ?</summary>

En définissant <code>DATABASE_URL=postgresql://...</code>. Le driver <code>psycopg2</code> est déjà installé, aucun code à changer.
</details>

<details><summary><b>B45.</b> Qui possède le schéma de la base ?</summary>

Alembic (migrations). <code>db.py</code> ne crée jamais les tables ; on lance <code>alembic upgrade head</code>.
</details>

<details><summary><b>B46.</b> Pourquoi Alembic plutôt que <code>create_all()</code> ?</summary>

Pour versionner le schéma et gérer son évolution de façon reproductible. <code>create_all</code> ne gère pas les migrations.
</details>

<details><summary><b>B47.</b> Comment les tests obtiennent-ils leur schéma ?</summary>

Directement depuis les métadonnées ORM (<code>Base.metadata.create_all</code>) sur une base SQLite temporaire (<code>conftest.py</code>).
</details>

<details><summary><b>B48.</b> Comment sont générés les identifiants ?</summary>

Des UUID (chaînes de 36 caractères) générés côté application, pas des entiers auto-incrémentés.
</details>

<details><summary><b>B49.</b> Pourquoi des UUID ?</summary>

Non devinables, générables côté client, pas de collision entre instances, pas de fuite d'info sur le volume.
</details>

<details><summary><b>B50.</b> Comment gérez-vous la suppression ?</summary>

Soft-delete : un flag <code>is_active</code> passe à <code>False</code> au lieu d'un vrai <code>DELETE</code> (sauf news/notifications qui sont supprimées réellement).
</details>

<details><summary><b>B51.</b> À quoi servent <code>deactivate_by</code> / <code>delete_by</code> ?</summary>

À tracer l'id de l'utilisateur qui a désactivé/supprimé l'enregistrement (traçabilité).
</details>

<details><summary><b>B52.</b> Combien de tables et quelles principales ?</summary>

14 : users, companies, trainings, training_sessions, formation_users, conversations, conversation_participants, messages, notifications, news, saved_news, events, invitations, site_content.
</details>

<details><summary><b>B53.</b> Comment stockez-vous les participants d'une conversation ?</summary>

En CSV dans <code>participant_ids</code> sur la table <code>conversations</code> (source de vérité). La table <code>conversation_participants</code> existe mais n'est pas remplie par l'API.
</details>

<details><summary><b>B54.</b> C'est quoi <code>engine</code> et <code>SessionLocal</code> dans <code>db.py</code> ?</summary>

<code>engine</code> = moteur de connexion à la base ; <code>SessionLocal</code> = fabrique de sessions transactionnelles.
</details>

<details><summary><b>B55.</b> C'est quoi <code>Base</code> (declarative_base) ?</summary>

La classe parente de tous les modèles ORM ; elle collecte les métadonnées (description de toutes les tables).
</details>

<details><summary><b>B56.</b> Pourquoi horodater en UTC ?</summary>

Pour éviter les ambiguïtés de fuseau ; la conversion en heure locale se fait à l'affichage côté front.
</details>

## E. Facades, services & modèles (57–68)

<details><summary><b>B57.</b> Quelle est la différence entre modèle de domaine et modèle ORM ?</summary>

Le modèle de domaine (<code>backend/models/</code>) **valide** les règles métier sans base ; le modèle ORM (<code>persistence/models.py</code>) **décrit les tables** SQL.
</details>

<details><summary><b>B58.</b> Pourquoi séparer domaine et ORM ?</summary>

La validation ne dépend pas de la base. On valide l'objet de domaine avant de persister via la facade.
</details>

<details><summary><b>B59.</b> Que renvoient les facades ?</summary>

Des <code>dict</code> (via <code>_to_dict()</code>), jamais des objets ORM.
</details>

<details><summary><b>B60.</b> Pourquoi renvoyer des dict et pas des objets ORM ?</summary>

Éviter les erreurs de session détachée, faciliter la sérialisation JSON, découpler de SQLAlchemy.
</details>

<details><summary><b>B61.</b> Comment gérez-vous les transactions ?</summary>

Via le context manager <code>session_scope()</code> : commit en sortie propre, rollback sur exception, close systématique.
</details>

<details><summary><b>B62.</b> C'est quoi <code>layer.py</code> ?</summary>

Le fichier qui contient toutes les classes de service (la couche service).
</details>

<details><summary><b>B63.</b> À quoi servent les helpers <code>to_csv</code> / <code>from_csv</code> ?</summary>

Sérialiser/désérialiser des listes (participants, documents, permissions) stockées en chaîne CSV.
</details>

<details><summary><b>B64.</b> Le modèle <code>Message</code> de domaine valide quoi ?</summary>

Le contenu : chaîne non vide, ≤ 5000 caractères.
</details>

<details><summary><b>B65.</b> C'est quoi <code>_to_dict()</code> ?</summary>

Une méthode privée de chaque facade qui transforme une ligne ORM en dictionnaire sérialisable.
</details>

<details><summary><b>B66.</b> Y a-t-il une faiblesse dans la couche service ?</summary>

Oui : souvent un simple passe-plat vers la facade, parfois court-circuitée (resources appelant <code>service.facade.xxx</code>). Point d'amélioration.
</details>

<details><summary><b>B67.</b> Où est effectué le hashage du mot de passe ?</summary>

Dans la <code>UserFacade</code> (couche persistance), pour que les couches au-dessus restent sans logique cryptographique.
</details>

<details><summary><b>B68.</b> <code>from __future__ import annotations</code>, ça fait quoi ?</summary>

Rend les annotations de type "paresseuses" (chaînes non évaluées) : types modernes et références en avant sans erreur à l'exécution.
</details>

## F. Chat temps réel & état (69–84)

<details><summary><b>B69.</b> Quelle techno pour le chat ?</summary>

Socket.IO (Flask-SocketIO côté serveur, socket.io-client côté front).
</details>

<details><summary><b>B70.</b> C'est quoi une "room" ?</summary>

Un canal logique Socket.IO. Chaque user rejoint une room perso <code>user:&lt;id&gt;</code> et une room par groupe <code>conversation:&lt;id&gt;</code>.
</details>

<details><summary><b>B71.</b> À quoi sert la room personnelle ?</summary>

Livrer messages directs et notifications à tous les appareils d'un même utilisateur.
</details>

<details><summary><b>B72.</b> Que se passe-t-il à la connexion socket ?</summary>

Vérif du token, enregistrement du <code>sid</code>, join de la room perso, auto-join des rooms de toutes ses conversations de groupe.
</details>

<details><summary><b>B73.</b> Message direct vs message de groupe ?</summary>

Groupe → diffusé à <code>conversation:&lt;id&gt;</code> ; direct → envoyé aux rooms perso de l'expéditeur ET du destinataire.
</details>

<details><summary><b>B74.</b> Comment empêchez-vous d'écrire dans une conversation non autorisée ?</summary>

Chaque action (send, typing, mark_read) vérifie <code>is_participant(conversation_id, user_id)</code>.
</details>

<details><summary><b>B75.</b> C'est quoi un <code>sid</code> ?</summary>

L'identifiant unique de session d'une connexion socket ; on mappe <code>sid → user_id</code>.
</details>

<details><summary><b>B76.</b> Comment gérez-vous la présence en ligne ?</summary>

Un compteur en mémoire <code>ONLINE_USERS</code> (nombre de connexions par user) dans <code>state.py</code>.
</details>

<details><summary><b>B77.</b> Pourquoi un compteur et pas un booléen ?</summary>

Un utilisateur peut être connecté sur plusieurs appareils ; on ne le passe hors ligne qu'à la dernière déconnexion.
</details>

<details><summary><b>B78.</b> Un message WebSocket est-il persisté ?</summary>

Oui : <code>handle_send_message</code> appelle la facade pour l'enregistrer en base avant de le diffuser.
</details>

<details><summary><b>B79.</b> Le chat passe-t-il aussi par REST ?</summary>

Oui : endpoints REST pour l'historique et la gestion ; le WebSocket sert au temps réel.
</details>

<details><summary><b>B80.</b> Qui peut renommer un groupe / gérer ses membres ?</summary>

Seulement le créateur (<code>creator_id</code>) ; les autres peuvent seulement quitter.
</details>

<details><summary><b>B81.</b> Comment gérez-vous "en train d'écrire" ?</summary>

Événement <code>typing</code> relayé aux autres participants, jamais renvoyé à l'expéditeur (<code>include_self=False</code>).
</details>

<details><summary><b>B82.</b> Comment gérez-vous les accusés de lecture ?</summary>

Événement <code>mark_read</code> : marque lu en base puis diffuse <code>messages_read</code> aux concernés.
</details>

<details><summary><b>B83.</b> Que contient <code>state.py</code> ?</summary>

<code>BLOCKLIST</code> (tokens révoqués) et <code>ONLINE_USERS</code> (présence), tous deux en mémoire.
</details>

<details><summary><b>B84.</b> Peut-on joindre un fichier à un message ?</summary>

Oui : le message porte <code>file_url</code> et <code>file_name</code> ; il doit avoir du texte OU une pièce jointe.
</details>

## G. Uploads (85–91)

<details><summary><b>B85.</b> Où sont stockés les fichiers uploadés ?</summary>

Sur le disque, sous <code>backend/uploads/</code>, dans des sous-dossiers par type.
</details>

<details><summary><b>B86.</b> Comment sécurisez-vous les uploads ?</summary>

Liste blanche d'extensions + <code>secure_filename()</code> + renommage en UUID + confinement au dossier uploads.
</details>

<details><summary><b>B87.</b> Comment sont servis les fichiers ?</summary>

Par la route <code>/uploads/&lt;path&gt;</code> qui renvoie le fichier depuis le dossier d'upload.
</details>

<details><summary><b>B88.</b> Pourquoi renommer en UUID ?</summary>

Éviter les collisions de noms et empêcher la devinette / l'écrasement de fichiers existants.
</details>

<details><summary><b>B89.</b> Que se passe-t-il quand on remplace une image ?</summary>

L'ancien fichier est supprimé du disque (<code>_cleanup_replaced_upload</code> / <code>delete_uploaded_file</code>).
</details>

<details><summary><b>B90.</b> Comment évitez-vous la suppression d'un fichier arbitraire (path traversal) ?</summary>

<code>delete_uploaded_file</code> vérifie via <code>resolve()</code> que le chemin est bien à l'intérieur du dossier uploads.
</details>

<details><summary><b>B91.</b> Différence entre nom d'image et nom de document uploadés ?</summary>

Image = <code>uuid.ext</code> ; document/pièce jointe = <code>uuid__nom-original.ext</code> pour garder un lien lisible.
</details>

## H. News, agenda, mailer & scheduler (92–101)

<details><summary><b>B92.</b> D'où viennent les actualités ?</summary>

De flux RSS français (INPI, Journal Officiel, BOFiP, Douanes…) parsés avec <code>feedparser</code>.
</details>

<details><summary><b>B93.</b> À quelle fréquence la synchro des news tourne-t-elle ?</summary>

Une fois par jour (APScheduler), + endpoint <code>/news/sync</code> pour forcer.
</details>

<details><summary><b>B94.</b> Que fait <code>sync_all()</code> avant de récupérer les news ?</summary>

Il purge les articles de plus de 30 jours (fenêtre glissante).
</details>

<details><summary><b>B95.</b> Comment évitez-vous les news en double ?</summary>

<code>facade.url_exists(url)</code> ignore un article dont l'URL est déjà en base.
</details>

<details><summary><b>B96.</b> À quoi sert la table <code>saved_news</code> ?</summary>

Un instantané complet de l'article sauvegardé par un utilisateur, indépendant de <code>news</code>, pour survivre à la purge.
</details>

<details><summary><b>B97.</b> C'est quoi l'export d'agenda ?</summary>

Une fiche HTML imprimable des événements et sessions publics du mois à venir, dans <code>uploads/exports/</code>.
</details>

<details><summary><b>B98.</b> Quand l'export d'agenda est-il généré ?</summary>

Automatiquement le 25 de chaque mois (cron APScheduler), ou à la demande via <code>/exports/monthly</code>.
</details>

<details><summary><b>B99.</b> Comment fonctionne le mailer ?</summary>

Un wrapper <code>smtplib</code> configuré par variables d'environnement ; sans <code>SMTP_HOST</code> c'est un no-op qui renvoie <code>False</code>.
</details>

<details><summary><b>B100.</b> Le mailer peut-il faire planter une requête ?</summary>

Non : il n'émet jamais d'exception, il logge et renvoie <code>False</code> en cas d'échec.
</details>

<details><summary><b>B101.</b> À quoi servent les emails ?</summary>

Réinitialisation de mot de passe et formulaire de contact.
</details>

## I. Erreurs, config, CORS & serveur (102–110)

<details><summary><b>B102.</b> Quel est le format des erreurs de l'API ?</summary>

Toujours <code>{"error": {"code", "message", "details?"}}</code> avec des codes normalisés.
</details>

<details><summary><b>B103.</b> Pourquoi normaliser les erreurs ?</summary>

Pour que le front les traite de façon uniforme quel que soit l'endpoint.
</details>

<details><summary><b>B104.</b> Comment gérez-vous le CORS ?</summary>

Flask-CORS, origines lues depuis <code>CORS_ORIGINS</code> (défaut <code>*</code> en dev).
</details>

<details><summary><b>B105.</b> Comment est configurée l'app ?</summary>

Par variables d'environnement (<code>.env</code> via python-dotenv) : <code>JWT_SECRET_KEY</code>, <code>DATABASE_URL</code>, SMTP, <code>FRONTEND_URL</code>…
</details>

<details><summary><b>B106.</b> C'est quoi le monkey patching (eventlet) ?</summary>

Remplacer à l'exécution <code>socket</code>/<code>threading</code> par des versions asynchrones, pour servir de vrais WebSockets.
</details>

<details><summary><b>B107.</b> Pourquoi le monkey patch tout en haut de <code>run.py</code> ?</summary>

Il faut patcher avant que Flask/SQLAlchemy n'importent <code>socket</code>/<code>threading</code>, sinon l'async ne prend pas.
</details>

<details><summary><b>B108.</b> Quel serveur en production ?</summary>

Gunicorn (WSGI) avec worker eventlet pour supporter les WebSockets.
</details>

<details><summary><b>B109.</b> À quoi sert <code>/status</code> ?</summary>

Un health check (<code>{"ok": true}</code>) pour vérifier que le serveur répond.
</details>

<details><summary><b>B110.</b> Comment le front connaît-il l'API ?</summary>

Une spec OpenAPI est exposée sur <code>/openapi.json</code> avec une UI Swagger sur <code>/docs</code>.
</details>

## J. Tests, Postman & outils (111–115)

<details><summary><b>B111.</b> Comment le projet est-il testé ?</summary>

Avec pytest : base isolée depuis les métadonnées ORM, ~345 cas couvrant auth, permissions, facades, sockets, exports.
</details>

<details><summary><b>B112.</b> Qu'est-ce que Postman apporte au projet ?</summary>

Une collection de ~56 requêtes + un environnement de variables pour tester l'API à la main et la documenter de façon exécutable.
</details>

<details><summary><b>B113.</b> À quoi sert <code>api/test.html</code> ?</summary>

Une page de test manuel du WebSocket (dev), qui ouvre une connexion Socket.IO. Pas utilisée en prod.
</details>

<details><summary><b>B114.</b> Postman vs Swagger, quelle différence ?</summary>

Postman = requêtes exécutables importables + variables ; Swagger = doc interactive générée depuis la spec OpenAPI. Complémentaires.
</details>

<details><summary><b>B115.</b> Pourquoi le scheduler ne tourne-t-il pas pendant les tests ?</summary>

Il n'est démarré que hors mode test et une seule fois par instance (garde sur <code>WERKZEUG_RUN_MAIN</code> / <code>RUN_SCHEDULER</code>).
</details>

## K. Questions pièges backend (116–120)

<details><summary><b>B116. 🎯</b> "Entre tes couches internes, c'est du JSON ?"</summary>

**Non.** Le JSON n'existe qu'entre le client et l'API. En dessous ce sont des objets Python (arguments et <code>dict</code>). Piège classique.
</details>

<details><summary><b>B117. 🎯</b> "Ton chat scale-t-il sur plusieurs serveurs ?"</summary>

Non en l'état : présence et blocklist sont en mémoire locale. Il faudrait Redis comme backend Socket.IO et pour l'état partagé.
</details>

<details><summary><b>B118. 🎯</b> "Un utilisateur désactivé peut-il encore agir avec son token ?"</summary>

Après le correctif d'audit, non : le callback JWT revérifie <code>is_active</code>. Coût : une requête base par requête authentifiée (à mettre en cache si trafic).
</details>

<details><summary><b>B119. 🎯</b> "Le CSV de participants, pourquoi c'est risqué ?"</summary>

Pas de clé étrangère, pas d'intégrité, et race condition ("lost update") si deux modifications concurrentes réécrivent la chaîne. Une table de jointure serait plus propre.
</details>

<details><summary><b>B120. 🎯</b> "Deux personnes s'inscrivent sur la dernière place en même temps ?"</summary>

Sans verrou, condition de course : on lit le compteur puis on insère → dépassement possible de <code>max_participants</code>. Il faudrait une transaction/contrainte atomique.
</details>

---

# PARTIE FRONTEND (30)

## L. React, Vite & structure (F1–F8)

<details><summary><b>F1.</b> Quelle techno frontend ?</summary>

React 18 (SPA), bundler Vite, style Tailwind CSS, client temps réel socket.io-client.
</details>

<details><summary><b>F2.</b> Sur quel port tourne le front et comment parle-t-il au back ?</summary>

Port 3000. Vite **proxifie** <code>/api</code> → backend <code>:8000</code> et <code>/socket.io</code> → backend, donc pas de CORS ni de port 8000 exposé.
</details>

<details><summary><b>F3.</b> Qu'est-ce qu'une SPA ?</summary>

Single Page Application : une seule page HTML, la navigation et le rendu se font côté client en JavaScript sans recharger la page.
</details>

<details><summary><b>F4.</b> À quoi sert <code>lib/api.js</code> ?</summary>

Un client HTTP centralisé : ajoute le token JWT, encode/parse le JSON, normalise les erreurs, expose une méthode par endpoint.
</details>

<details><summary><b>F5.</b> À quoi sert <code>lib/socket.js</code> ?</summary>

Gérer une connexion Socket.IO **singleton** partagée, avec le token JWT passé dans <code>auth</code>.
</details>

<details><summary><b>F6.</b> À quoi sert l'<code>AuthContext</code> ?</summary>

Exposer <code>user</code>, <code>login</code>, <code>logout</code>, le rôle et les permissions à toute l'app via le Context React.
</details>

<details><summary><b>F7.</b> Comment est structuré le code front ?</summary>

Pages, composants réutilisables, modales, un contexte d'auth, et une couche <code>lib</code> (client API + socket).
</details>

<details><summary><b>F8.</b> Pourquoi un proxy Vite plutôt qu'appeler <code>:8000</code> directement ?</summary>

Pour n'exposer qu'un port, éviter le CORS, et garder la même origine entre front et API.
</details>

## M. Client API & authentification (F9–F20)

<details><summary><b>F9.</b> Où est stocké le token JWT côté front ?</summary>

Dans <code>localStorage</code> (<code>access_token</code> / <code>refresh_token</code>), géré par <code>lib/api.js</code>.
</details>

<details><summary><b>F10.</b> Comment le token est-il envoyé au backend ?</summary>

<code>lib/api.js</code> ajoute automatiquement l'en-tête <code>Authorization: Bearer &lt;token&gt;</code> sur les requêtes authentifiées.
</details>

<details><summary><b>F11.</b> Comment le front gère-t-il un upload de fichier ?</summary>

Avec un <code>FormData</code> : il n'encode pas en JSON et laisse le navigateur poser le <code>Content-Type</code> (avec la boundary).
</details>

<details><summary><b>F12.</b> Que fait le front quand l'API renvoie 401 ?</summary>

Il efface les tokens et émet un événement <code>auth:logout</code> → l'UI repasse à l'écran de connexion.
</details>

<details><summary><b>F13.</b> Pourquoi le 401 est-il important pour l'UX ?</summary>

Il permet au front de détecter une session expirée et de déconnecter proprement, au lieu d'afficher une erreur serveur.
</details>

<details><summary><b>F14.</b> Comment la session est-elle restaurée au rechargement de la page ?</summary>

Au montage, si un token existe, l'<code>AuthProvider</code> appelle <code>/users/me</code> pour récupérer le profil.
</details>

<details><summary><b>F15.</b> C'est quoi <code>ApiError</code> ?</summary>

Une classe d'erreur enrichie (message backend + status HTTP) pour afficher proprement les erreurs.
</details>

<details><summary><b>F16.</b> À quoi sert <code>mediaUrl()</code> ?</summary>

Préfixer les chemins d'images relatifs (<code>/uploads/…</code>) vers le backend, sinon le navigateur les résout sur <code>:3000</code> → 404.
</details>

<details><summary><b>F17.</b> Comment le front détermine-t-il le rôle "patron" ?</summary>

Il le **déduit** en cherchant si l'utilisateur administre une entreprise (<code>findAdministeredCompany</code>), car le backend n'a pas de champ rôle.
</details>

<details><summary><b>F18.</b> Comment le front vérifie-t-il une permission ?</summary>

<code>can(perm)</code> dans l'<code>AuthContext</code> : <code>true</code> si super admin, sinon si la permission est dans <code>user.permissions</code>.
</details>

<details><summary><b>F19.</b> Que fait le front à la déconnexion ?</summary>

Appelle <code>/auth/logout</code> (révoque le jti), déconnecte le socket, efface les tokens, réinitialise l'utilisateur.
</details>

<details><summary><b>F20.</b> L'inscription connecte-t-elle automatiquement ?</summary>

Oui : <code>register</code> stocke les tokens renvoyés et établit la session directement.
</details>

## N. Socket & temps réel (F21–F26)

<details><summary><b>F21.</b> Combien de connexions socket le front ouvre-t-il ?</summary>

Une seule (singleton) partagée par toute l'app.
</details>

<details><summary><b>F22.</b> Quand le socket se connecte-t-il ?</summary>

Une fois l'utilisateur authentifié (<code>connectSocket()</code> appelé dans <code>establishSession</code>).
</details>

<details><summary><b>F23.</b> Comment le socket s'authentifie-t-il ?</summary>

Le token JWT est passé dans l'objet <code>auth</code> à la connexion ; le backend le vérifie dans <code>handle_connect</code>.
</details>

<details><summary><b>F24.</b> Quels transports le socket utilise-t-il ?</summary>

<code>websocket</code> en priorité, avec repli sur <code>polling</code>.
</details>

<details><summary><b>F25.</b> Que se passe-t-il au logout côté socket ?</summary>

<code>disconnectSocket()</code> ferme la connexion et remet le singleton à <code>null</code>.
</details>

<details><summary><b>F26.</b> Le front reçoit-il les nouveaux messages en temps réel sans rafraîchir ?</summary>

Oui : il écoute les événements Socket.IO (<code>new_message</code>, <code>presence</code>, <code>invitation</code>…) émis par le backend.
</details>

## O. Questions pièges frontend (F27–F30)

<details><summary><b>F27. 🎯</b> "Stocker le JWT dans localStorage, quel risque ?"</summary>

Accessible en JavaScript → vol du token en cas de faille **XSS**. Plus sûr : cookie <code>httpOnly</code> + <code>SameSite</code>. (Atténué ici : pas de <code>dangerouslySetInnerHTML</code>.)
</details>

<details><summary><b>F28. 🎯</b> "Le rôle patron vient du backend ?"</summary>

Non : le backend n'a pas de champ rôle. Le front le **déduit** en listant les entreprises et en cherchant celle que l'utilisateur administre.
</details>

<details><summary><b>F29. 🎯</b> "Pourquoi ne pas invalider la session sur toute erreur réseau ?"</summary>

On ne déconnecte que sur un **401** réel. Une coupure réseau / backend momentanément indisponible ne doit pas jeter l'utilisateur dehors.
</details>

<details><summary><b>F30. 🎯</b> "Le front fait-il confiance à son calcul de permissions pour la sécurité ?"</summary>

Non — le <code>can()</code> côté front ne sert qu'à l'affichage (masquer des boutons). La **vraie** autorisation est vérifiée côté backend (<code>_can</code>). Le front n'est jamais une barrière de sécurité.
</details>

---

*Astuce finale : les questions marquées 🎯 sont les pièges — ce sont celles qui font la différence en review. Entraîne-toi surtout dessus.*
