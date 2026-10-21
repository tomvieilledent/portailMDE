# MDE Dashboard — Frontend React

Ébauche d'un frontend React reproduisant la maquette Figma de la "Maison de l'Économie".

## 📁 Structure du projet

```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.jsx         # Conteneur principal avec navigation
│   │   ├── Header.jsx            # En-tête avec logo et profil
│   │   ├── TabNavigation.jsx     # Navigation par onglets
│   │   └── pages/
│   │       ├── DashboardPage.jsx # Page accueil
│   │       ├── Companies.jsx     # Onglet Entreprises
│   │       ├── Users.jsx         # Onglet Trombinoscope
│   │       ├── Trainings.jsx     # Onglet Formations
│   │       └── News.jsx          # Onglet Veille économique
│   ├── App.jsx                   # Point d'entrée React
│   ├── main.jsx                  # Bootstrap React DOM
│   └── index.css                 # Styles Tailwind
├── index.html                    # HTML de base
├── vite.config.js                # Configuration Vite
├── tailwind.config.js            # Configuration Tailwind CSS
├── postcss.config.js             # Configuration PostCSS
└── package.json                  # Dépendances
```

## 🚀 Démarrage rapide

### 1. Installer les dépendances

```bash
cd frontend
npm install
```

### 2. Lancer le serveur de développement

```bash
npm run dev
```

Le dashboard s'ouvrira automatiquement sur `http://localhost:3000`.

### 3. Builder pour la production

```bash
npm run build
```

Les fichiers compilés seront dans le dossier `dist/`.

## 🎨 Personnalisation

### Ajouter des couleurs

Édite `tailwind.config.js` pour modifier le vert primaire :

```js
colors: {
  primary: {
    light: '#7ec843',    // Vert clair
    DEFAULT: '#5da020',  // Vert principal
    dark: '#4a7a1a',     // Vert foncé
  },
}
```

### Ajouter un nouvel onglet

1. Crée un nouveau fichier dans `src/components/pages/MonOnglet.jsx`
2. Ajoute l'import et la route dans `src/components/Dashboard.jsx`
3. Ajoute la tab dans le tableau `tabs` du Dashboard

Exemple :

```jsx
// src/components/pages/MyTab.jsx
export default function MyTab() {
  return <div>Contenu de mon onglet</div>
}
```

```jsx
// src/components/Dashboard.jsx
import MyTab from './pages/MyTab'

const tabs = [
  // ... autres tabs
  { id: 'mytab', label: 'Mon Onglet', icon: '⭐' },
]

const renderPage = () => {
  // ...
  case 'mytab':
    return <MyTab />
}
```

### Modifier les données mockées

Les données sont définies avec `useState` dans chaque page. Remplace-les par des appels API quand prêt :

```jsx
// Avant : données mockées
const [companies, setCompanies] = useState([...])

// Après : appel API
useEffect(() => {
  fetch('/api/companies')
    .then(res => res.json())
    .then(data => setCompanies(data))
}, [])
```

## 📱 Responsive Design

Le projet utilise Tailwind CSS pour un design responsive :

- `grid-cols-1` : 1 colonne par défaut
- `md:grid-cols-2` : 2 colonnes sur écrans moyens (≥768px)
- `lg:grid-cols-3` : 3 colonnes sur grands écrans (≥1024px)

## 🔗 Intégration API

Quand le backend sera prêt, remplace les données mockées par des appels REST :

```jsx
const [companies, setCompanies] = useState([])

useEffect(() => {
  fetch('http://localhost:5000/api/companies')
    .then(res => res.json())
    .then(data => setCompanies(data))
    .catch(err => console.error(err))
}, [])
```

## 📝 Composants réutilisables

- `.card` : classe CSS pour les cartes avec ombre et padding
- `.btn-primary` : bouton vert principal
- `.btn-secondary` : bouton gris secondaire
- `.badge` et `.badge-success` : badges de statut

Utilise-les partout pour une cohérence visuelle :

```jsx
<div className="card">
  <button className="btn-primary">Action</button>
  <span className="badge badge-success">Actif</span>
</div>
```

## 🛠 Technologies

- **React 18** : UI framework
- **Vite** : build tool ultra-rapide
- **Tailwind CSS** : utility-first CSS
- **Lucide React** : icônes modernes
- **JavaScript ES6+** : syntaxe moderne

## 📚 Prochaines étapes

- [ ] Connecter à l'API backend (endpoints du Stage 3)
- [ ] Ajouter authentification JWT
- [ ] Implémenter WebSocket pour messaging temps réel
- [ ] Ajouter gestion d'état (Zustand ou Context API)
- [ ] Tests unitaires avec Jest + React Testing Library
- [ ] Formulaires et validation avec React Hook Form
- [ ] Pagination et filtrage côté client
- [ ] Notifications/toasts pour actions utilisateur

## 💬 Questions ?

N'hésite pas à modifier ce code selon tes besoins. C'est une ébauche et tu peux :

- Ajouter des componentes
- Changer les couleurs
- Ajouter plus d'onglets
- Intégrer des librairies supplémentaires

Bonne chance ! 🚀
