# Preuve — itération 006

## Contrat

- **Spécifications :** `EF-007`, `EF-007.4`
- **Acceptation :** `ACC-063`, `ACC-064`, `ACC-065`
- **Date de vérification :** 26 juillet 2026
- **Environnement :** Windows, Python 3.14, FastAPI 0.140, Uvicorn 0.51,
  SQLite, Chrome headless

## Fichiers modifiés

- `docs/SPECIFICATIONS.md`
- `src/sentinelfonctionnelle/domain/specifications.py`
- `src/sentinelfonctionnelle/domain/hierarchy.py`
- `src/sentinelfonctionnelle/application/projects.py`
- `src/sentinelfonctionnelle/adapters/persistence/sqlite.py`
- `src/sentinelfonctionnelle/web/app.py`
- `src/sentinelfonctionnelle/web/templates/project.html`
- `src/sentinelfonctionnelle/web/static/app.css`
- `tests/acceptance/test_functional_specifications.py`
- `tests/acceptance/test_web_specification_editor.py`

## Test RED

Commande :

```powershell
.\.venv\Scripts\python.exe -m unittest `
  tests.acceptance.test_functional_specifications `
  tests.acceptance.test_web_specification_editor -v
```

Résultat observé avant le code de production :

```text
ImportError: cannot import name 'OrganizationView'
POST .../specification => 404 Not Found
FAILED (errors=2, failures=1)
```

Les échecs correspondaient aux frontières absentes : modèle canonique,
organisations calculées et route de saisie.

## Test GREEN

La même commande réussit après implémentation :

```text
Ran 4 tests
OK
```

Les tests couvrent les formes pas-à-pas, Given/When/Then, tableau d’exemples et
checklist, le refus des syntaxes invalides, l’incrément de version, la
restauration SQLite et les vues par tag, exigence, règle métier et mode.

## Suite complète

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Résultat :

```text
Ran 24 tests in 1.438s
OK
```

## Point d’entrée réel et persistance

Un serveur séparé a été démarré sur `127.0.0.1:8012` avec une base temporaire.
Les formulaires HTTP réels ont créé un projet, un jeu et quatre tests, puis une
spécification différente pour chaque mode. Le processus a été arrêté et
relancé sur le même fichier.

Résultat de la sonde après migration et du contrôle restauré :

```json
{
  "health": {"status": "ok", "mode": "local", "schema_version": 3},
  "tests_restored": 4,
  "requirement_view_contains": "REQ-AUTH-01",
  "styles": [
    "Pas-à-pas",
    "Given/When/Then",
    "Tableau d’exemples",
    "Checklist"
  ]
}
```

La vue calculée par mode contient quatre groupes d’un test chacun et conserve
les identifiants des tests.

## Inspection visuelle

- écran projet et éditeur inspectés dans Chrome à `1440 × 1000` ;
- vue mobile vérifiée avec une largeur CSS réelle de `390 px` ;
- mesures desktop : `innerWidth=1440`, `clientWidth=1425`,
  `scrollWidth=1425` ;
- mesures mobile : `innerWidth=390`, `clientWidth=375`,
  `scrollWidth=375` ;
- aucun élément détecté hors du cadre dans les deux largeurs.

Le tutoriel HTML a également été relu à `1440 × 1000` et `390 × 844` :
dans les deux cas, `scrollWidth` égale `clientWidth`. Son tableau comparatif
reste défilable dans son propre conteneur lorsque l’écran est étroit.

Le validateur du skill documentaire et les commandes présentées dans le guide
ont été rejoués :

```text
OK: docs\tutorial-local.html est structurellement valide et traçable.
demo-hierarchy: OK
demo-deployment --mode local: OK
demo-persistence: project_count=2, identity_preserved=true, history_count=1
```

Le navigateur intégré Codex n’a pas pu être initialisé dans cette session
(`Cannot redefine property: process`). La vérification a été poursuivie sur un
Chrome local piloté par CDP et Playwright, sans modifier le périmètre testé.

## Revue de sécurité et limites

- les syntaxes sont analysées de manière déterministe, sans exécuter le texte ;
- Jinja échappe les valeurs saisies et SQLite utilise des requêtes paramétrées ;
- les déclarations d’exécution sont limitées à une liste autorisée ;
- les vues transversales sont calculées et ne dupliquent ni ne déplacent les
  tests ;
- une sauvegarde incrémente le numéro courant, mais l’historique complet des
  versions et l’approbation immuable relèvent encore de `EF-008` ;
- aucune exécution de test, génération Playwright ou donnée secrète n’est
  introduite par cette tranche ;
- l’absence de protection CSRF interdit toujours l’exposition du serveur local
  sur un réseau partagé.
