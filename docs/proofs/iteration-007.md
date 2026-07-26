# Preuve — itération 007

## Contrat

- **Spécifications :** `EF-007.2`, `EF-007.5`
- **Acceptation :** `ACC-066`, `ACC-067`, `ACC-068`
- **Date de vérification :** 26 juillet 2026
- **Environnement :** Windows, Python 3.14, FastAPI 0.140, SQLite,
  Chrome headless, artifact-tool 2.8.6

## Fichiers modifiés

- `docs/SPECIFICATIONS.md`
- `src/sentinelfonctionnelle/domain/tabular_data.py`
- `src/sentinelfonctionnelle/adapters/tabular.py`
- `src/sentinelfonctionnelle/domain/hierarchy.py`
- `src/sentinelfonctionnelle/application/projects.py`
- `src/sentinelfonctionnelle/adapters/persistence/sqlite.py`
- `src/sentinelfonctionnelle/web/app.py`
- `src/sentinelfonctionnelle/web/templates/project.html`
- `src/sentinelfonctionnelle/web/static/app.css`
- `docs/examples/modele-donnees-tests.xlsx`
- `tests/acceptance/test_tabular_test_data.py`
- `tests/acceptance/test_web_tabular_data.py`

## Test RED

```powershell
.\.venv\Scripts\python.exe -m unittest `
  tests.acceptance.test_tabular_test_data `
  tests.acceptance.test_web_tabular_data -v
```

Résultat observé avant le code de production :

```text
ModuleNotFoundError: No module named 'sentinelfonctionnelle.adapters.tabular'
POST .../data-binding => 404 Not Found
FAILED (failures=1, errors=1)
```

## Test GREEN

La même commande réussit après implémentation :

```text
Ran 5 tests
OK
```

Les tests couvrent l’équivalence CSV/XLSX, un véritable classeur généré,
les limites, les formules refusées, les trois stratégies, la graine
reproductible, la concurrence bornée, l’interface et le redémarrage SQLite.

## Suite complète

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Résultat :

```text
Ran 29 tests in 2.547s
OK
```

## Classeur d’exemple

Le classeur `docs/examples/modele-donnees-tests.xlsx` a été créé avec
artifact-tool. Les onglets `Données` et `Aide` ont tous deux été rendus et
inspectés visuellement. L’inspection de `Données!A1:E6` retrouve cinq colonnes
et cinq cas, sans formule ni erreur de calcul. Le parseur de production relit
ensuite ce fichier avec les mêmes en-têtes et cinq lignes.

## Point d’entrée réel

Un serveur séparé a été lancé sur `127.0.0.1:8013` avec une base temporaire.
Depuis un véritable navigateur, les formulaires ont créé un projet, un jeu et
un test, puis téléversé le classeur d’exemple en `multipart/form-data` avec la
stratégie parallèle et une concurrence de 2.

Résultat observé :

```json
{
  "health": {"status": "ok", "mode": "local", "schema_version": 4},
  "filename": "modele-donnees-tests.xlsx",
  "cases": 5,
  "columns": 5,
  "mode": "Parallèle",
  "batches": 3,
  "max_parallelism": 2
}
```

Après arrêt et redémarrage sur le même fichier SQLite, le nom, les cinq lignes,
l’empreinte, la stratégie et les trois lots sont réapparus.

## Inspection visuelle

- application à `1440 × 1000` : `scrollWidth=1425`,
  `clientWidth=1425`, aucun élément hors cadre ;
- application à une largeur CSS réelle de `390 px` :
  `scrollWidth=375`, `clientWidth=375` ; le tableau conserve volontairement
  son défilement horizontal dans son propre conteneur ;
- tutoriel à `1440 × 1000` puis `390 × 844` : aucune barre horizontale sur la
  page et scénario tabulaire lisible ;
- le navigateur intégré n’a pas pu initialiser sa session
  (`Cannot redefine property: process`) ; la vérification a donc été poursuivie
  sur Chrome local piloté par CDP et Playwright.

## Revue de sécurité et limites

- 2 Mio, 50 colonnes, 1 000 cas et 4 000 caractères par cellule au maximum ;
- CSV strictement UTF-8 ; extensions limitées à `.csv` et `.xlsx` ;
- taille décompressée XLSX et nombre de composants bornés ;
- formules Excel refusées, macros et connexions jamais interprétées ;
- seul le tableau canonique et son empreinte sont persistés, pas un fichier
  actif susceptible d’être exécuté ;
- la graine rend l’ordre aléatoire reproductible et l’échantillon est sans
  remise ;
- la concurrence est limitée à 20 et ne déclenche pas encore de processus :
  cette tranche produit le plan destiné au futur runner.
