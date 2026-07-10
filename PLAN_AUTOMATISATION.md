# Plan d'automatisation — Site affilié 1xPartners

## Objectif

Créer un système automatisé qui :
1. Télécharge le site 1xPartners (React SPA) toutes les 48h
2. Injecte ton lien affilié en arrière-plan
3. Ajoute des balises SEO pour Google
4. Déploie automatiquement sur ton hébergement InfinityFree via FTP
5. Ne nécessite **aucune intervention manuelle** après configuration

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│ GitHub (dépôt privé)                                     │
│                                                          │
│ 📂 .github/workflows/                                    │
│    ├── scrape-deploy.yml       ← Workflow principal      │
│                                                          │
│ 📂 scripts/                                              │
│    ├── scrape.py              ← Téléchargement + rendu   │
│    └── deploy.py             ← Upload FTP                │
│                                                          │
│ 📂 site/                     ← Contenu généré            │
│    ├── index.html            ← Page avec design + SEO    │
│    ├── assets/               ← Images, CSS, polices      │
│                                                          │
└──────────────────────┬───────────────────────────────────┘
                       │
           GitHub Actions (toutes les 48h)
                       │
                       ▼
               ┌──────────────────┐
               │  Selenium +       │
               │  Chrome headless  │
               └────────┬─────────┘
                        │
                        ▼
               ┌──────────────────────────────────────┐
               │  Téléchargement du rendu React complet│
               │  - HTML final (après JS)              │
               │  - CSS, images, polices, favicon      │
               │  - Bouton "S'inscrire" → lien affilié │
               │  - Meta tags SEO injectés             │
               └────────────────┬─────────────────────┘
                                │
                                ▼
               ┌──────────────────────────────────────┐
               │  Commit automatique dans le repo      │
               │  + FTP vers InfinityFree              │
               └──────────────────────────────────────┘
                                │
                                ▼
                     ┌──────────────────┐
                     │  workshoppro.rf.gd│
                     │  ✅ Site à jour   │
                     │  ✅ Indexé Google │
                     │  ✅ Liens affiliés│
                     └──────────────────┘
```

---

## Workflow GitHub Actions (`.github/workflows/scrape-deploy.yml`)

Déclencheurs :
- ⏰ **Toutes les 48h** via cron (`0 0 */2 * *`)
- 🔄 Manuellement possible depuis l'interface GitHub

Étapes :
1. **Setup** : Python 3.12 + Chrome + ChromeDriver
2. **Scrape** : Exécute `scripts/scrape.py`
   - Lance Chrome headless
   - Navigue vers le lien affilié
   - Attend le rendu React complet
   - Sauvegarde le HTML final
   - Télécharge tous les assets (CSS, images, polices, JS)
   - Injecte le lien affilié dans tous les boutons CTA
   - Ajoute les balises SEO (title, description, Open Graph, robots)
3. **Commit & Push** : Sauvegarde les fichiers mis à jour dans le repo
4. **Déploiement FTP** : Exécute `scripts/deploy.py`
   - Upload les fichiers vers InfinityFree
   - Purge les fichiers obsolètes si nécessaire

---

## Script Python : `scripts/scrape.py`

### Étape 1 — Rendu de la page avec Selenium
- Lance Chrome en mode headless
- Navigue vers `https://affpa.top/L?tag=d_3902989m_2387c_&site=3902989&ad=2387`
- Attend le chargement complet de React (détection du DOM final)
- Capture le HTML complet après rendu JS

### Étape 2 — Extraction des assets
- Parse le HTML avec BeautifulSoup
- Télécharge tous les assets distants :
  - Images (logo, icônes, SVG)
  - Polices (fichiers .woff, .woff2, .ttf)
  - CSS (externe et inline)
  - Favicon
- Sauvegarde dans `site/assets/`

### Étape 3 — Injection du lien affilié
- Remplace tous les liens "Sign up" / "Register" / boutons CTA par :
  ```html
  <a href="https://affpa.top/L?tag=d_3902989m_2387c_&site=3902989&ad=2387"
     onclick="event.stopPropagation()"
     target="_blank"
     rel="noopener noreferrer"
     class="...">S'inscrire</a>
  ```
- Le lien est masqué visuellement (pas d'affichage de l'URL)
- Les paramètres de tracking sont préservés

### Étape 4 — SEO
Balises ajoutées dans le `<head>` :
```html
<title>1xBet Partenaires - Programme d'affiliation | Inscription</title>
<meta name="description" content="Rejoignez le programme d'affiliation 1xBet Partners. Gagnez des commissions sur le sport avec 1xbet. Inscription gratuite et rapide.">
<meta name="keywords" content="1xBet, affiliation, partenaires, sport, bookmaker, commissions">
<meta name="robots" content="index, follow">
<meta property="og:title" content="1xBet Partenaires - Programme d'affiliation">
<meta property="og:description" content="Rejoignez le programme d'affiliation 1xBet Partners.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://workshoppro.rf.gd">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="https://workshoppro.rf.gd">
```

---

## Script Python : `scripts/deploy.py`

- Importe les identifiants FTP depuis les variables d'environnement (GitHub Secrets)
- Se connecte au serveur FTP InfinityFree
- Synchronise le dossier `site/` vers la racine du serveur
- Supprime les fichiers qui n'existent plus dans le repo

---

## Configuration GitHub (à faire une fois)

### 1. Créer un dépôt privé sur GitHub
- Nom : par exemple `site-affilie-1xpartners`
- Visibilité : Privé (pour protéger les tokens)

### 2. Ajouter les Secrets GitHub
Aller dans Settings → Secrets and variables → Actions → New repository secret :

| Secret | Valeur |
|--------|--------|
| `FTP_HOST` | Serveur FTP InfinityFree |
| `FTP_USER` | Nom d'utilisateur FTP |
| `FTP_PASS` | Mot de passe FTP |
| `AFFILIATE_URL` | `https://affpa.top/L?tag=d_3902989m_2387c_&site=3902989&ad=2387` |

### 3. Activer GitHub Actions
Le workflow se lance automatiquement toutes les 48h.

---

## Fichiers du projet

```
site-affilie-1xpartners/
│
├── .github/
│   └── workflows/
│       └── scrape-deploy.yml       ← GitHub Actions
│
├── scripts/
│   ├── scrape.py                   ← Scraping + rendu React + SEO
│   ├── deploy.py                   ← Upload FTP
│   └── requirements.txt            ← Dépendances Python
│
├── site/                           ← Contenu généré (auto)
│   ├── index.html
│   └── assets/
│       ├── css/
│       ├── images/
│       ├── fonts/
│       └── js/
│
└── README.md                       ← Instructions
```

---

## Dépendances Python (`scripts/requirements.txt`)

```
selenium==4.30.0
webdriver-manager==4.0.2
requests==2.34.2
beautifulsoup4==4.15.0
lxml==5.3.0
```

---

## Calendrier d'exécution

| Phase | Action | Durée estimée |
|-------|--------|---------------|
| 1 | Création du dépôt GitHub + secrets | 10 min |
| 2 | Création des scripts Python | 30 min |
| 3 | Création du workflow GitHub Actions | 10 min |
| 4 | Test du premier déploiement | 15 min |
| 5 | Vérification site en ligne | 5 min |
| **Total** | | **~1h** |

---

## Informations nécessaires pour commencer

Pour configurer le système, j'ai besoin de :

| Info | Exemple |
|------|---------|
| **Nom d'utilisateur GitHub** | `ton-utilisateur` |
| **Serveur FTP** | `ftp.infinityfree.com` ou `ftpupload.net` |
| **Utilisateur FTP** | `if0_42068577` (ou autre) |
| **Mot de passe FTP** | `********` |
| **Dossier racine FTP** | `/htdocs` ou `/domains/workshoppro.rf.gd/public_html` |

---

## Une fois configuré — Plus rien à faire

✅ Le site est mis à jour automatiquement toutes les 48h  
✅ Le lien affilié est intégré en arrière-plan  
✅ Google indexe la page avec le bon contenu SEO  
✅ L'URL reste courte : `workshoppro.rf.gd`  
✅ Aucune maintenance manuelle requise  
