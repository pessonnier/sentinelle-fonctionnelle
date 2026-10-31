# SentinelleFonctionnelle

SentinelleFonctionnelle est un outillage web destiné à transformer des indications utilisateur et des captures d’écran en scénarios de tests fonctionnels exécutables, grâce à une interaction guidée avec un LLM configurable.

Le produit sépare explicitement deux activités :

1. **la conception**, interactive, pendant laquelle l’utilisateur dialogue avec un LLM, structure ses tests et les valide individuellement ;
2. **l’exécution**, automatisable, qui lance du code Playwright généré ou personnalisé et ne sollicite un LLM d’exécution que dans des cas exceptionnels explicitement autorisés.

## Principes directeurs

- organisation hiérarchique explicite : projet, plan de test, suite de tests ou
  dossier, puis cas de test ;
- même cœur fonctionnel en déploiement local monoposte et en déploiement web
  multi-utilisateur et multi-projet ;
- isolation des projets et autorisations évaluées côté serveur ;
- types de tests configurables, dont les tests fonctionnels de performance ;
- saisie guidée adaptée aux fonctionnels métier, sans YAML obligatoire ;
- profils versionnés d’approche de test, modèles de tests, phrases d’intention
  et tags administrables ;
- description synthétique et factuelle mise à jour lors de l’édition d’un cas de test ;
- validation individuelle des tests pendant leur conception ;
- profils LLM de conception et d’exécution distincts ;
- tests exécutables sans LLM dans le cas nominal ;
- génération de code Playwright lisible, déterministe et personnalisable ;
- historisation des réussites, durées et dates d’exécution ;
- utilisation de sélecteurs stables plutôt que de coordonnées visuelles fragiles ;
- séparation stricte entre secrets, spécifications, preuves et code généré ;
- déploiement conteneurisé simple ;
- intégration native aux chaînes GitHub Actions et GitLab CI par une CLI, des codes de sortie standards et des rapports JUnit ;
- développement du produit en TDD.

## Documentation

La spécification fonctionnelle, le MVP et l’architecture logicielle sont décrits dans :

- [`docs/SPECIFICATIONS.md`](docs/SPECIFICATIONS.md)
- [`docs/REFERENCES.md`](docs/REFERENCES.md), références normatives ISO/IEC/IEEE
  29119, glossaire ISTQB et correspondance terminologique du projet ;
- [`docs/tutorial-local.html`](docs/tutorial-local.html), tutoriel HTML autonome
  du mode local actuellement disponible ;
- [`docs/tutorial-premier-test-gitlab.md`](docs/tutorial-premier-test-gitlab.md),
  premier cas guidé, génération, approbation et exécution dans GitLab CI/CD ;
- [`docs/llm/ollama.md`](docs/llm/ollama.md), installation, configuration,
  test réel et diagnostic du profil Qwen3.6 local ;
- [`docs/hr-demo.md`](docs/hr-demo.md), cible RH de démonstration, classeurs
  XLSX, génération et exécution du scénario Playwright complet ;
- [`docs/firefox-test-authoring-plugin-specifications.md`](docs/firefox-test-authoring-plugin-specifications.md),
  spécifications priorisées du futur plugin Firefox de capture et de conception ;
- [`docs/design/iteration-012-2-introspection.md`](docs/design/iteration-012-2-introspection.md),
  bénéfices, alternatives écartées, frontières et prochains choix ;
- [`docs/IMPLEMENTATION_STATUS.md`](docs/IMPLEMENTATION_STATUS.md), tableau de
  bord et liens vers les preuves.
- [`docs/DEVELOPMENT_PLAN.md`](docs/DEVELOPMENT_PLAN.md), audit du socle,
  décisions de cadrage et feuille de route priorisée.
- [`docs/operations-lot4.md`](docs/operations-lot4.md), export approuvé,
  runner autonome/OCI, modèles CI, PostgreSQL, concurrence et rétention.

## État du projet

Le développement TDD a commencé. Le cœur actuel permet de créer des plans de
test, de les organiser en suites ou dossiers, puis d'y créer et déplacer des
cas de test en conservant leur identité et leur historique (`ACC-002`,
`ACC-003`). Il fournit également les
compositions applicatives `local` et `online`, avec identité obligatoire,
filtrage multi-projet et rôles en ligne (`ACC-051`, `ACC-052`).

La persistance SQLite locale avec migrations versionnées est implémentée. Les
formulaires FastAPI distinguent maintenant les écrans Projet, Plan de test et
Cas de test. Ils permettent de créer plusieurs projets et plans, d'organiser
les suites, dossiers et cas, puis de renommer, déplacer, ordonner et archiver
les nœuds avec restauration après redémarrage (`ACC-060` à `ACC-062`,
`ACC-069` à `ACC-072`).

L’approche d’un plan n’est plus un texte libre : elle est choisie parmi des
profils versionnés décrits en YAML. L’écran **Configuration** permet de créer
un profil ou d’enregistrer une nouvelle version d’un profil existant, tandis
que les plans conservent exactement l’identifiant et la version sélectionnés
(`ACC-073`).

Chaque cas de test se rédige désormais dans un workflow pas-à-pas composé de
cartes action/validation. L’éditeur peut analyser une page HTML autorisée,
présenter ses champs, boutons, liens et titres, puis insérer leurs références
dans les étapes. Les profils, fixtures, références de secrets, politiques,
limites, pages et étapes forment une structure JSON versionnée affichable à tout
moment (`ACC-074` à `ACC-077`). Les quatre anciens formats restent lisibles et
doivent être requalifiés avant une nouvelle confirmation.

L’assistant de conception charge un catalogue YAML d’intentions fonctionnelles,
repère les informations encore manquantes et explique l’utilité de chaque
question. Après l’analyse d’une page, il indique également les actions et
validations compatibles avec chaque élément HTML. L’utilisateur peut ensuite
dialoguer avec le LLM configuré : la réponse est limitée à des propositions
structurées, acceptées une par une, puis une description factuelle est
reconstruite depuis les seuls changements retenus. Le dialogue et les décisions
sont restaurés depuis SQLite.

Les écrans **Accès aux LLM** (`/configuration/llm-access`) et **Génération de
code** (`/configuration/code-generation`) permettent respectivement de
versionner les connexions aux fournisseurs et les profils de production. Une
configuration d’accès conserve l’endpoint, le modèle et le nom de la variable
d’environnement portant la clé, jamais sa valeur. Une configuration de
génération fixe le langage, le framework, les chemins relatifs, les motifs de
fichiers, les preuves, validations et limites.
Les cas conservent les deux références `identifiant@version` dans leur JSON
(`ACC-078` à `ACC-080`).

Un fichier CSV UTF-8 ou Excel `.xlsx` peut également être associé à un cas de
test.
Chaque ligne devient un cas de saisie et l’application prévisualise un plan en
série, en lots parallèles bornés ou dans un ordre aléatoire reproductible. Le
fichier est analysé sans exécuter de formule et la liaison est restaurée depuis
SQLite (`ACC-066` à `ACC-068`).

## Démarrage local

Créer un environnement avec Python 3.12 ou ultérieur, installer le produit et
ses outils de test, puis lancer l’interface :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c requirements/constraints-py312.txt -e ".[test,quality]"
.\.venv\Scripts\python.exe -m sentinelle_fonctionnelle.cli serve
```

La vérification rapide exclut volontairement les scripts Playwright générés,
qui exigent un navigateur installé et une cible locale active :

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Pour préparer les scénarios navigateur, installer Chromium puis suivre le
parcours reproductible de [`docs/hr-demo.md`](docs/hr-demo.md) :

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m pytest tests/generated --browser chromium
```

Le contrôle complet du socle regroupe les erreurs Python critiques, le formatage
et le typage de la base progressive, les liens documentaires et la suite rapide :

```powershell
.\.venv\Scripts\python.exe tools/check_quality.py
```

Le fichier `requirements/constraints-py312.txt` fige l’environnement de
référence testé. Les plages de `pyproject.toml` restent le contrat de
compatibilité ; l’instantané ne doit être régénéré qu’après réussite de cette
commande.

Les catalogues utilisent le même geste de création : la liste occupe la largeur,
puis un bouton `+ Ajouter…` déplie le formulaire sous celle-ci sans perdre la
saisie lorsqu’il est replié. Le sélecteur **Thème** de l’en-tête propose sept
palettes (Forêt, Océan, Prune, Coucher de soleil, Graphite, Contraste élevé et
Défense — ministère des Armées) et
mémorise le choix dans le navigateur. Ces préférences de présentation ne sont ni
stockées dans SQLite, ni intégrées aux prompts ou aux exports.

Le catalogue est placé par défaut dans
`data/generation-profiles.yaml`. Son chemin peut être remplacé avec
`SENTINELLE_FONCTIONNELLE_GENERATION_PROFILES`. Les variables de clé API
référencées par les profils doivent être injectées dans l’environnement de
l’application ou du futur worker.

Le catalogue des intentions est placé par défaut dans
`data/test-intents.yaml`. Son chemin peut être remplacé avec
`SENTINELLE_FONCTIONNELLE_TEST_INTENTS`. Chaque intention versionnée décrit ses
exemples, les types de tests conseillés et les questions nécessaires ; le
catalogue peut être enrichi sans modifier le code.

L'adaptateur PostgreSQL transactionnel, les rôles et les révisions optimistes
sont disponibles dans l'extra `online`. Le branchement OIDC et la qualification
sur une instance PostgreSQL restent propres à l'environnement. Les images et le
Compose isolé sont versionnés sous `deployment/`. Une première verticale déterministe de génération Playwright est
désormais exécutable depuis un workflow confirmé et des données XLSX. Depuis la
page du prompt final, le profil Qwen3.6 128K local sur le port `11436` peut aussi
produire un candidat réel : sa réponse JSON, ses chemins et sa syntaxe sont
validés avant persistance. Le candidat, son manifeste, son prompt assaini et ses
empreintes rejoignent alors le même historique que la génération déterministe.
Deux niveaux d’analyse coexistent désormais. L’éditeur analyse sans secret le
HTML statique autorisé ; la commande `analyze-rendered-page` exécute un plan
Playwright local, authentifié et borné, puis catalogue le DOM réellement rendu.
Sur la cible RH, elle distingue automatiquement le code portail JavaScript, les
quatre champs dynamiques communs et le champ dynamique réservé au manager. Le
guide reproductible est [`docs/hr-demo.md`](docs/hr-demo.md).

Pour alimenter la base locale avec le projet d’exemple complet :

```powershell
.\.venv\Scripts\python.exe -m sentinelle_fonctionnelle.cli seed-hr-demo-project
```

Une seconde cible illustre un test de commande sur quatre écrans, avec listes
déroulantes, tableau de saisie, tableaux de restitution et calculs de remise,
frais et TVA :

```powershell
.\.venv\Scripts\python.exe -m sentinelle_fonctionnelle.cli seed-orders-demo-project
```

Le parcours et la personnalisation protégée du code généré sont détaillés dans
[`docs/orders-demo.md`](docs/orders-demo.md). Depuis l'historique d'un candidat,
seul le contenu des blocs `sentinelle:custom` est modifiable ; ces blocs peuvent
ensuite être réappliqués lors d'une nouvelle génération avec détection des
conflits de contrat.

Le **Catalogue** contient ensuite le projet **Exemple — Bureau des Talents
Intersidéraux** et ses deux cas confirmés. Depuis un cas, la section **Candidats,
validation et décision** permet de générer, comparer, télécharger, exécuter puis
approuver ou rejeter chaque version.

La verticale de génération utilise une matrice explicite de sources et de
lignes, des jetons qualifiés par source et un manifeste reproductible. La
commande `run-playwright` valide le candidat sur une cible locale, refuse une
empreinte modifiée et produit JUnit avec `execution.json`. Elle constitue une
validation individuelle locale. Une réussite ne vaut jamais approbation : la
décision humaine distincte lie la définition structurée, le fichier réellement
exécuté et son empreinte. Un candidat approuvé expose **Exporter le bundle CI**.
Le ZIP stable inclut les empreintes, la documentation et les modèles CI.
`sentinelle-run` le vérifie puis l'exécute hors du service ; le profil OCI est
décrit dans le [guide d'exploitation du lot 4](docs/operations-lot4.md).

Le skill
[`write-implementation-html-docs`](skills/write-implementation-html-docs/SKILL.md)
définit la méthode de rédaction et de validation des futurs guides HTML.

## Licence

Ce projet est distribué sous licence MIT. Consultez [`LICENSE`](LICENSE).
