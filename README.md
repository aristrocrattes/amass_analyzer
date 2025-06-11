# 🔍 Analyse output Amass

## 📋 Vue d'ensemble

Ce dossier contient deux scripts Python complémentaires pour analyser et visualiser les résultats de reconnaissance de domaines obtenus avec **Amass**. Ces outils permettent d'extraire, organiser et cartographier tous les domaines et sous-domaines découverts lors d'un scan de reconnaissance.

PS : Ces deux scripts ont été généré en utilisant l'IA, je ne m'approprie donc aucun mérite.

---

## 📄 Scripts Disponibles

### 1. **`amassbeautifier.py`** - Extracteur et Organisateur de Domaines

Un outil puissant pour extraire, analyser et exporter tous les domaines découverts par Amass.

#### 🎯 Fonctionnalités Principales

- **Extraction complète** : Récupère TOUS les domaines/sous-domaines du fichier Amass
- **Résolution IP** : Associe les adresses IP aux domaines correspondants
- **Catégorisation intelligente** : Classe automatiquement les domaines par fonction
- **Exports multiples** : Plusieurs formats de sortie disponibles
- **Interface claire** : Affichage organisé avec statistiques détaillées

#### 📊 Modes d'Affichage

1. **Simple** (défaut) : Liste complète avec IPs
2. **Catégorisé** : Domaines organisés par fonction
3. **Détaillé** : Relations complètes entre les éléments

#### 📂 Catégories Automatiques

- 🏠 **Domaine Principal** : Le domaine racine
- 🌐 **Web Services** : Sites web et applications
- 🔧 **API & Applications** : Services et microservices
- 📧 **Mail & Communication** : Serveurs de messagerie
- ⚙️ **Admin & Management** : Panneaux d'administration
- 🔬 **Development & Testing** : Environnements de développement
- 🖥️ **Infrastructure** : DNS, FTP, CDN, etc.
- 🌍 **Externes/Tiers** : Domaines externes
- 📋 **Autres** : Non catégorisés

#### 💾 Formats d'Export

- **Simple** : Liste des domaines seuls
- **Avec IPs** : Domaines + adresses IP associées
- **Catégorisé** : Domaines organisés par fonction
- **Clean** : Noms de domaines uniquement (un par ligne)

---

### 2. **`domain_mapper.py`** - Cartographe Visuel de Domaines

Créé des cartographies visuelles interactives des relations entre domaines.

#### 🎯 Fonctionnalités Principales

- **Cartographie Graphviz** : Diagrammes vectoriels professionnels
- **Interface HTML Interactive** : Carte web moderne et responsive
- **Affichage textuel** : Vue d'ensemble en mode console
- **Relations visuelles** : Liens entre domaines, IPs et services
- **Design moderne** : Interface utilisateur élégante

#### 🗺️ Types de Cartographies

1. **Graphviz** (défaut) : Diagrammes vectoriels (SVG, PNG, PDF)
2. **HTML Interactif** : Interface web avec contrôles dynamiques
3. **Textuel** : Arbre hiérarchique en console

#### 🎨 Interface HTML Interactive

- **Design responsive** : Compatible mobile et desktop
- **Contrôles dynamiques** :
  - Basculer la physique du réseau
  - Afficher/masquer les IPs
  - Centrer la vue
  - Exporter en PNG
  - Mode plein écran
- **Interactions** :
  - Clic sur les nœuds pour les détails
  - Survol pour l'aperçu
  - Zoom et navigation fluides
- **Statistiques en temps réel** : Compteurs animés

#### 🔗 Types de Relations Visualisées

- **Node** : Relations hiérarchiques (bleu)
- **A Record** : Résolution IPv4 (vert)
- **AAAA Record** : Résolution IPv6 (vert clair)
- **CNAME** : Alias de domaine (orange)
- **MX Record** : Serveurs de messagerie (rouge)
- **NS Record** : Serveurs DNS (violet)

---

## 🚀 Installation et Prérequis

### Prérequis Python

```bash
# Python 3.6+ requis
python3 --version
```

### Installation des Dépendances

#### Pour `amassbeautifier.py`

```bash
# Aucune dépendance externe requise
# Utilise uniquement les modules Python standard
```

#### Pour `domain_mapper.py`

```bash
# Installer Graphviz (optionnel)
pip install graphviz

# Sur Ubuntu/Debian
sudo apt-get install graphviz

# Sur macOS
brew install graphviz

# Sur CentOS/RHEL
sudo yum install graphviz
```

---

## 📘 Guide d'Utilisation

### `amassbeautifier.py` - Extracteur de Domaines

#### Syntaxe de Base

```bash
python3 amassbeautifier.py <fichier_amass.txt> [options]
```

#### Options Disponibles

```bash
--simple          # Affichage simple (défaut)
--categorized     # Affichage catégorisé par fonction
--detailed        # Affichage avec détails des relations
--export FILE     # Exporter vers un fichier
--export-ips      # Inclure les IPs dans l'export
--export-clean FILE # Exporter uniquement les noms de domaines
```

#### Exemples d'Utilisation

**Affichage simple avec statistiques :**

```bash
python3 amassbeautifier.py scan_results.txt
```

**Affichage catégorisé par fonction :**

```bash
python3 amassbeautifier.py scan_results.txt --categorized
```

**Affichage détaillé avec relations :**

```bash
python3 amassbeautifier.py scan_results.txt --detailed
```

**Export simple des domaines :**

```bash
python3 amassbeautifier.py scan_results.txt --export all_domains.txt
```

**Export avec adresses IP :**

```bash
python3 amassbeautifier.py scan_results.txt --export domains_with_ips.txt --export-ips
```

**Export format clean (pour d'autres outils) :**

```bash
python3 amassbeautifier.py scan_results.txt --export-clean clean_domains.txt
```

### `domain_mapper.py` - Cartographe Visuel

#### Syntaxe de Base

```bash
python3 domain_mapper.py <fichier_amass.txt> [options]
```

#### Options Disponibles

```bash
--graphviz         # Générer avec Graphviz (défaut)
--html             # Générer une carte interactive HTML
--text             # Affichage textuel simple
--no-ips           # Masquer les adresses IP
--show-orgs        # Afficher les organisations
--format FORMAT    # Format de sortie (svg, png, pdf)
```

#### Exemples d'Utilisation

**Cartographie Graphviz (défaut) :**

```bash
python3 domain_mapper.py scan_results.txt
```

**Cartographie interactive HTML :**

```bash
python3 domain_mapper.py scan_results.txt --html
```

**Cartographie textuelle :**

```bash
python3 domain_mapper.py scan_results.txt --text
```

**Export PNG sans IPs :**

```bash
python3 domain_mapper.py scan_results.txt --format png --no-ips
```

**Cartographie complète avec organisations :**

```bash
python3 domain_mapper.py scan_results.txt --html --show-orgs
```

---

## 📈 Exemples de Sorties

### `amassbeautifier.py` - Mode Catégorisé

```
🎯 Analyse complète des domaines (scan de example.com)
================================================================================

📂 Domaine Principal (1)
----------------------------------------
  ├── example.com → 93.184.216.34

📂 Web Services (3)
----------------------------------------
  ├── www.example.com → 93.184.216.34
  ├── app.example.com → 192.168.1.10
  ├── portal.example.com → 10.0.0.5

📂 API & Applications (2)
----------------------------------------
  ├── api.example.com → 192.168.1.20
  ├── rest.example.com → 10.0.0.15

📂 Mail & Communication (2)
----------------------------------------
  ├── mail.example.com → 192.168.1.30
  ├── webmail.example.com → 10.0.0.25

📊 Résumé: 8 domaines au total
```

### `domain_mapper.py` - Mode Textuel

```
🗺️  CARTOGRAPHIE DE EXAMPLE.COM
============================================================

🏠 DOMAINE PRINCIPAL
├── example.com
│   └── 📍 93.184.216.34

🌿 SOUS-DOMAINES (6)
├── www.example.com
│   └── 📍 93.184.216.34
├── api.example.com
│   └── 📍 192.168.1.20
├── mail.example.com
│   └── 📍 192.168.1.30

📊 RÉSUMÉ
├── Sous-domaines: 6
├── Domaines externes: 2
├── Adresses IP uniques: 8
└── Relations totales: 24
```

---

## 📁 Fichiers Générés

### `amassbeautifier.py`

- **Exports texte** : Fichiers `.txt` avec listes de domaines
- **Formats disponibles** : Simple, avec IPs, catégorisé, clean

### `domain_mapper.py`

- **Graphviz** :
  - `domain_map_example_com.svg` (défaut)
  - `domain_map_example_com.png`
  - `domain_map_example_com.pdf`
- **HTML Interactif** :
  - `domain_map_example_com.html`

---

## 🔧 Conseils d'Utilisation

### Workflow Recommandé

1. **Scan Amass** : Effectuer la reconnaissance

```bash
amass enum -d example.com -o amass_results.txt
```

2. **Analyse avec amassbeautifier** : Extraire et analyser

```bash
python3 amassbeautifier.py amass_results.txt --categorized
```

3. **Cartographie visuelle** : Créer la cartographie

```bash
python3 domain_mapper.py amass_results.txt --html
```

4. **Exports pour autres outils** : Préparer les données

```bash
python3 amassbeautifier.py amass_results.txt --export-clean domains_list.txt
```

### Optimisation des Performances

- **Gros fichiers** : Utilisez `--no-ips` pour réduire la complexité visuelle
- **Exports multiples** : Combinez les options pour générer plusieurs formats
- **HTML interactif** : Idéal pour les présentations et l'analyse collaborative

### Compatibilité

- **Systèmes** : Linux, macOS, Windows
- **Python** : 3.6+ (testé sur 3.8+)
- **Navigateurs** : Chrome, Firefox, Safari, Edge (pour HTML)

---

## 🐛 Résolution de Problèmes

### Erreurs Communes

**"Aucun domaine trouvé" :**

- Vérifiez le format du fichier Amass
- Assurez-vous que le fichier contient des données FQDN

**"Graphviz non installé" :**

```bash
pip install graphviz
sudo apt-get install graphviz  # Linux
brew install graphviz          # macOS
```

**Problèmes d'encodage :**

- Les scripts utilisent UTF-8 par défaut
- Vérifiez l'encodage de votre fichier source

### Support et Contribution

Pour signaler des bugs ou proposer des améliorations, n'hésitez pas à documenter vos retours avec :

- Version de Python utilisée
- Système d'exploitation
- Exemple de fichier d'entrée (anonymisé)
- Message d'erreur complet

---

## 📄 Licence et Crédits

Scripts développés pour l'analyse de reconnaissance de domaines dans le cadre de tests de sécurité autorisés.

**⚠️ Utilisation Responsable** : Ces outils sont destinés uniquement à des fins de sécurité légitimes et autorisées. L'utilisateur est responsable de respecter les lois et réglementations applicables.
