# Cible RH de démonstration et scénario Playwright

## Objectif

Le **Bureau des Talents Intersidéraux** est une petite application RH intégrée
à Sentinelle Fonctionnelle. Son code HTML est volontairement hétérogène afin
d’exercer l’analyse des pages, les données tabulaires, la génération de code et
l’exécution réelle dans un navigateur.

Le parcours nominal est :

1. se connecter comme manager ;
2. créer une fiche collaborateur avec des données issues de deux classeurs
   Excel ;
3. consulter la fiche enregistrée ;
4. contrôler les valeurs statiques et celles rendues par JavaScript.

Toutes les données sont synthétiques. Le stockage des fiches est éphémère et
redémarre avec le serveur.

## Installer le projet d’exemple dans Sentinelle

Le seeder fourni crée une arborescence complète dans la base locale utilisée par
l’application :

```powershell
.\.venv\Scripts\python.exe -m sentinelle_fonctionnelle.cli seed-hr-demo-project `
  --database .\data\sentinelle_fonctionnelle.db `
  --root . `
  --base-url http://127.0.0.1:8000
```

La commande est idempotente : elle réutilise le projet portant le même nom et
met à niveau ses workflows si l’exemple évolue. Elle affiche les identifiants
du projet, du plan et des deux cas. Dans **Catalogue**, ouvrir ensuite
**Exemple — Bureau des Talents Intersidéraux**. L’arborescence créée est :

```text
Parcours RH de démonstration
└── Parcours fonctionnels
    ├── Authentification
    │   └── Refuser une connexion invalide
    └── Gestion des collaborateurs
        └── Créer et consulter Zoé Nébuleuse
```

Le cas nominal contient 23 étapes et les catalogues des trois pages. Le cas de
refus couvre le message d’erreur de connexion. Les deux définitions sont
confirmées, disposent d’une précondition technique confirmée et permettent
d’utiliser immédiatement **Vérifier la préparation** puis **Télécharger le code
généré** depuis leur écran.

Les deux cas utilisent explicitement l’accès LLM
`ollama-qwen36-128k-11436@1` (**Ollama local 11436 — Qwen3.6 35B 128K**) et le
profil compatible `python-playwright-qwen36-11436@1`. Avant un dialogue assisté,
le bouton **Vérifier le serveur et le modèle** de la page **Accès aux LLM** doit
confirmer la présence de `qwen3.6-35b-a3b-q4_K_M_128k:latest` sur
`http://127.0.0.1:11436/v1`.

Le cas nominal livré en base contient également un échange réel avec ce profil :
Qwen relit les 23 étapes et leurs catalogues HTML, puis conserve ses questions
et deux propositions en attente dans **Dialogue avec le LLM**. Elles ne sont pas
appliquées automatiquement ; l’utilisateur garde la décision finale.

Dans la section **Génération** du cas nominal, **Ouvrir le prompt de génération**
affiche une page de lecture seule contenant les deux messages prêts pour le LLM,
le modèle Qwen sélectionné, les profils versionnés, les deux skills appliqués et
l’empreinte SHA-256. Le JSON exact est téléchargeable depuis cette page. La valeur
du champ mot de passe est remplacée par `<secret-value-redacted>` avant la
construction du prompt. Le code Playwright candidat reste accessible par
**Télécharger le code généré**, sans encombrer l’écran de rédaction.

Les classeurs XLSX restent attachés aux cas pour montrer la provenance des
données. Les valeurs injectées dans ces deux exemples sont toutefois des
littéraux synthétiques : le téléchargement unitaire actuel ne sait pas encore
assembler plusieurs sources XLSX. Cette concession rend le fichier téléchargé
directement exécutable et est limitée à cette cible de démonstration locale.

Le 1er août 2026, les deux fichiers téléchargés depuis les URL de cas ont été
exécutés tels quels dans Chromium : `2 passed in 2.20s`. Les copies contrôlées
sont conservées sous `outputs/hr-demo/generated-project/`.

## Installer le projet d’exemple dans Sentinelle

Le seeder fourni crée une arborescence complète dans la base locale utilisée par
l’application :

```powershell
.\.venv\Scripts\python.exe -m sentinelle_fonctionnelle.cli seed-hr-demo-project `
  --database .\data\sentinelle_fonctionnelle.db `
  --root . `
  --base-url http://127.0.0.1:8000
```

La commande est idempotente : elle réutilise le projet portant le même nom et
met à niveau ses workflows si l’exemple évolue. Elle affiche les identifiants
du projet, du plan et des deux cas. Dans **Catalogue**, ouvrir ensuite
**Exemple — Bureau des Talents Intersidéraux**. L’arborescence créée est :

```text
Parcours RH de démonstration
└── Parcours fonctionnels
    ├── Authentification
    │   └── Refuser une connexion invalide
    └── Gestion des collaborateurs
        └── Créer et consulter Zoé Nébuleuse
```

Le cas nominal contient 23 étapes et les catalogues des trois pages. Le cas de
refus couvre le message d’erreur de connexion. Les deux définitions sont
confirmées, disposent d’une précondition technique confirmée et permettent
d’utiliser immédiatement **Vérifier la préparation** puis **Télécharger le code
généré** depuis leur écran.

Les classeurs XLSX restent attachés aux cas pour montrer la provenance des
données. Les valeurs injectées dans ces deux exemples sont toutefois des
littéraux synthétiques : le téléchargement unitaire actuel ne sait pas encore
assembler plusieurs sources XLSX. Cette concession rend le fichier téléchargé
directement exécutable et est limitée à cette cible de démonstration locale.

Le 1er août 2026, les deux fichiers téléchargés depuis les URL de cas ont été
exécutés tels quels dans Chromium : `2 passed in 2.20s`. Les copies contrôlées
sont conservées sous `outputs/hr-demo/generated-project/`.

## Démarrer et ouvrir la cible

Depuis la racine du dépôt :

```powershell
.\.venv\Scripts\python.exe -m sentinelle_fonctionnelle.cli serve
```

Ouvrir ensuite :

- connexion : `http://127.0.0.1:8000/demo/hr/login` ;
- saisie : `http://127.0.0.1:8000/demo/hr/saisie` après connexion ;
- consultation : `http://127.0.0.1:8000/demo/hr/consultation` ;
- HTML de saisie rendu pour le manager :
  `http://127.0.0.1:8000/demo/hr/parser/saisie/manager-cactus` ;
- HTML de consultation :
  `http://127.0.0.1:8000/demo/hr/parser/consultation`.

Les deux comptes de test sont dans `outputs/hr-demo/connexion-rh.xlsx` :

| Profil | Courriel | Mot de passe | Code portail |
|---|---|---|---|
| Manager cactus | `camille.cactus@example.test` | `Cactus!2026` | `CACTUS-42` |
| Agent lama | `alex.lama@example.test` | `Lama!2026` | `LAMA-7` |

Ces secrets sont factices et réservés au banc d’essai.

## Pourquoi les champs sont différents

| Page | Champ ou contrôle | Construction | Qualité HTML | Ce que le test vérifie |
|---|---|---|---|---|
| Connexion | Courriel, mot de passe | HTML serveur statique | Libellés accessibles | Découverte et localisateurs par libellé |
| Connexion | Code du portail | JavaScript différé | Libellé injecté | Attente automatique du navigateur |
| Saisie | Matricule, prénom, nom, date | HTML serveur statique | Correcte | Saisie par libellé |
| Saisie | Type de contrat | HTML serveur statique | Ancien balisage | Robustesse sur un code imparfait |
| Saisie | Planète d’affectation | HTML serveur statique | Libellé peu exploitable | Localisateur CSS explicite |
| Saisie | Mentor | HTML serveur statique | Attribut de test stable | Localisateur `data-testid` |
| Saisie | Couleur d’aura, niveau de téléportation, quota de confettis | JavaScript différé | Correcte après rendu | Champs absents du HTML initial |
| Saisie | Nuage de compétences | Composant Web personnalisé | Champ interne injecté | Rendu JavaScript plus atypique |
| Saisie | Budget de formation, astreinte lunaire | Serveur selon la session | Accessible | Catalogue différent pour le manager |
| Saisie | Note du conseil galactique | JavaScript selon la session | Injectée seulement pour le manager | Croisement session et JavaScript |
| Consultation | Identité et informations RH | HTML serveur statique | Mélangée | Contrôle immédiat des données sauvegardées |
| Consultation | Cartes aura, téléportation, compétences | JavaScript différé | Composants dynamiques | Validation après rendu |

L’analyse HTML de l’éditeur télécharge et parse le document source : elle voit
les éléments statiques et, sur l’URL de prévisualisation manager, les champs
rendus côté serveur. L’adaptateur Playwright complète cette vue en établissant
une vraie session synthétique et en cataloguant le DOM après JavaScript.

## Cataloguer le DOM rendu

Trois plans reproductibles sont fournis :

| Plan | État obtenu | Résultat observé |
|---|---|---|
| `hr-demo-login-rendered-page-plan.json` | connexion avant saisie | 7 éléments, dont `portal-code` uniquement après JavaScript |
| `hr-demo-agent-rendered-page-plan.json` | saisie connectée comme agent | 22 éléments, dont 4 uniquement après rendu |
| `hr-demo-rendered-page-plan.json` | saisie connectée comme manager | 25 éléments, dont 5 uniquement après rendu |

Avec le serveur lancé sur le port 8775 :

```powershell
.\.venv\Scripts\python.exe -m sentinelle_fonctionnelle.cli analyze-rendered-page `
  --plan .\config\examples\hr-demo-rendered-page-plan.json `
  --base-url http://127.0.0.1:8775 `
  --output .\outputs\hr-demo\catalog-saisie-manager.json
```

Le plan ne contient que des actions et localisateurs appartenant à des listes
fermées. Il est limité à 20 actions et 120 secondes, reste sur la boucle locale
et ne peut exécuter ni JavaScript libre ni commande shell. Les identifiants,
mots de passe et valeurs résolus depuis le XLSX ne figurent jamais dans le
catalogue.

La section `discovery` de l’artefact compare le HTML serveur relu avec les mêmes
cookies au DOM rendu. Sur la saisie manager, elle isole :

- `favorite-color`, `energy-level` et `remote-days`, injectés après 180 ms ;
- `skills`, matérialisé par le composant Web `rh-skill-cloud` ;
- `manager-dynamic-note`, injecté uniquement pour la session manager.

La comparaison agent/manager ajoute exactement `manager-budget`,
`manager-comment` et `manager-dynamic-note` au profil manager. Les deux premiers
viennent du serveur ; le dernier vient de JavaScript.

Pour relier le catalogue au workflow tout en gardant la source de référence
intacte :

```powershell
.\.venv\Scripts\python.exe -m sentinelle_fonctionnelle.cli apply-page-catalog `
  --catalog .\outputs\hr-demo\catalog-saisie-manager.json `
  --workflow .\config\examples\hr-demo-workflow.json `
  --output .\outputs\hr-demo\hr-demo-workflow.rendered.json
```

La commande rapproche les éléments par stratégie, valeur de localisateur et
rôle. Les références déjà employées dans les étapes sont conservées. Si un
élément utilisé n’est plus retrouvé, l’application s’arrête au lieu de générer
un test incomplet.

## Classeur de connexion

`outputs/hr-demo/connexion-rh.xlsx` contient :

- les deux comptes valides ;
- un cas rejeté pour vérifier le traitement négatif ;
- une feuille `Mode d'emploi` ;
- des colonnes directement référencées par les jetons
  `{{data.login.email}}`, `{{data.login.password}}` et
  `{{data.login.portal_code}}`.

## Classeur de collaborateurs

`outputs/hr-demo/saisie-collaborateurs.xlsx` contient deux fiches compatibles
avec le parcours manager et une fiche agent destinée à de futurs scénarios.
Les deux cas manager référencent notamment :

- `{{data.employee.employee_number}}`, `{{data.employee.first_name}}`,
  `{{data.employee.last_name}}` ;
- `{{data.employee.department}}`, `{{data.employee.contract_type}}` ;
- `{{data.employee.favorite_color}}`, `{{data.employee.energy_level}}` ;
- `{{data.employee.skills}}`, `{{data.employee.manager_budget}}`.

Les classeurs sont reproductibles avec :

```powershell
node tools/build_hr_demo_workbooks.mjs
```

Le script applique une mise en forme lisible, fige les en-têtes, crée une table
et contrôle les erreurs de formule. Les feuilles de données restent en première
position pour être importées directement par l’application.

## Workflow fixé pour la génération

`config/examples/hr-demo-workflow.json` est l’entrée de génération de référence.
Il contient :

- l’état `confirmed` ;
- les deux sources XLSX, leur identifiant et leur colonne clé ;
- une matrice de deux associations nommées, sans jointure implicite ;
- les catalogues de connexion, saisie et consultation ;
- 23 étapes ordonnées ;
- les références de localisateurs et les jetons de données ;
- les validations de visibilité, valeur, texte et URL.

L’utilisateur peut examiner la même forme de structure à tout moment dans le
panneau **Structure de génération** de l’éditeur de cas.

## Générer le test Python Playwright

```powershell
.\.venv\Scripts\python.exe -m sentinelle_fonctionnelle.cli generate-playwright `
  --workflow .\config\examples\hr-demo-workflow.json `
  --output .\tests\generated\test_hr_demo_workflow.py
```

Le générateur :

- refuse un workflow non confirmé ;
- refuse les chemins de données absolus ou sortant du dépôt ;
- refuse une matrice incomplète ou une source dupliquée ;
- résout chaque cible par le catalogue de page ;
- sélectionne exactement les lignes déclarées pour chacun des deux cas ;
- conserve les valeurs hors du code généré ;
- produit un manifeste reproductible portant les empreintes du workflow, du
  code et des classeurs ;
- contrôle les empreintes XLSX avant la collecte pytest ;
- produit des localisateurs Playwright lisibles ;
- adapte les champs `color` et `range`, que `fill()` ne traite pas comme un
  champ texte classique.

## Exécuter le scénario

Dans un premier terminal :

```powershell
.\.venv\Scripts\python.exe -m sentinelle_fonctionnelle.cli serve `
  --host 127.0.0.1 --port 8770
```

Dans un second terminal, utiliser le runner local borné :

```powershell
.\.venv\Scripts\python.exe -m sentinelle_fonctionnelle.cli run-playwright `
  --test .\tests\generated\test_hr_demo_workflow.py `
  --base-url http://127.0.0.1:8770 `
  --output .\outputs\hr-demo\execution-local `
  --browser chromium --timeout 120
```

Le runner exige le manifeste, refuse un code modifié après génération, lance
pytest sans shell et produit `execution.json`, `junit.xml` et les journaux.

Le 30 juillet 2026, les deux cas générés ont réussi dans Chromium :
`2 passed in 3.86s`. Le rapport est conservé dans
`outputs/hr-demo/execution-012-2/`.

Le même jour, le catalogue Playwright manager a produit un workflow dérivé dont
le code généré possède exactement la même empreinte
`f5700dbbaf68fc441a7dde9ce1f001998d7903f82805efc71f9ac8aad4e89d4d`.
Ses deux cas ont réussi en 4,738 s. Le rapport est conservé dans
`outputs/hr-demo/execution-rendered-catalog/`.

## Contrôles complémentaires

Les tests d’acceptation couvrent également :

- le parcours HTTP manager et la persistance de toutes les valeurs ;
- la différence entre le HTML statique et les champs JavaScript ;
- l’import effectif des deux fichiers XLSX par le parseur tabulaire du produit ;
- la compilation et le contenu du code généré.
- le refus d’un candidat modifié après génération ;
- la production du rapport structuré et de JUnit par le runner.

## Limites connues

- L’interface de l’éditeur utilise encore l’analyse statique. L’exploration
  authentifiée est disponible par CLI et ses catalogues peuvent être appliqués
  à une copie du workflow ; son intégration interactive dans l’éditeur reste à
  réaliser.
- Le générateur implémenté est la première verticale Python
  `pytest-playwright`; les autres langages et frameworks configurables ne sont
  pas encore matérialisés.
- Les données de démonstration sont en mémoire et ne servent pas de modèle de
  stockage pour une application réelle.
- Le runner courant est une validation locale limitée à la boucle locale ; il
  ne fournit pas encore l’isolation OCI, les restrictions réseau générales ou
  la sélection de suites exigées pour la CI.

L’analyse détaillée de l’utilité, des solutions écartées et des prochains
incréments se trouve dans
`docs/design/iteration-012-2-introspection.md`.
