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
- modèles de tests, phrases d’intention et tags administrables ;
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
- [`docs/IMPLEMENTATION_STATUS.md`](docs/IMPLEMENTATION_STATUS.md), tableau de
  bord et liens vers les preuves.

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

Chaque cas de test peut désormais être spécifié sous quatre formes adaptées aux
métiers — pas-à-pas, Given/When/Then, tableau d’exemples ou checklist — tout en
alimentant un même modèle canonique versionné. L’arbre reste l’organisation
primaire et des vues calculées par tag, exigence, règle métier ou mode, avec
recherche textuelle, facilitent les revues transversales (`ACC-063` à
`ACC-065`).

Un fichier CSV UTF-8 ou Excel `.xlsx` peut également être associé à un cas de
test.
Chaque ligne devient un cas de saisie et l’application prévisualise un plan en
série, en lots parallèles bornés ou dans un ordre aléatoire reproductible. Le
fichier est analysé sans exécuter de formule et la liaison est restaurée depuis
SQLite (`ACC-066` à `ACC-068`).

Lancer l’interface locale après installation éditable :

```powershell
.\.venv\Scripts\python.exe -m sentinelle_fonctionnelle.cli serve
```

Le déploiement partagé PostgreSQL avec authentification, les fonctions LLM, la
génération Playwright et les déploiements conteneurisés restent à réaliser.

Le skill
[`write-implementation-html-docs`](skills/write-implementation-html-docs/SKILL.md)
définit la méthode de rédaction et de validation des futurs guides HTML.

## Licence

Ce projet est distribué sous licence MIT. Consultez [`LICENSE`](LICENSE).
