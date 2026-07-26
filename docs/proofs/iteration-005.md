# Preuve — itération 005

## Contrat

- **Spécifications :** `EF-001`, `EF-001.2`, `EF-002`, `EF-002.1`, `ENF-013`
- **Acceptation :** `ACC-060`, `ACC-061`, `ACC-062`, `ACC-069`, `ACC-070`,
  `ACC-071`, `ACC-072`
- **Date de vérification :** 26 juillet 2026
- **Environnement :** Windows, Python 3.14, FastAPI 0.140, Uvicorn 0.51,
  SQLite

## Fichiers modifiés

- `pyproject.toml`
- `src/sentinelfonctionnelle/cli.py`
- `src/sentinelfonctionnelle/domain/hierarchy.py`
- `src/sentinelfonctionnelle/application/projects.py`
- `src/sentinelfonctionnelle/adapters/persistence/sqlite.py`
- `src/sentinelfonctionnelle/web/`
- `tests/acceptance/test_cli_serve.py`
- `tests/acceptance/test_server_settings.py`
- `tests/acceptance/test_web_local.py`

## Test RED

Commande :

```powershell
.\.venv\Scripts\python.exe -m unittest `
  tests.acceptance.test_web_local `
  tests.acceptance.test_server_settings `
  tests.acceptance.test_cli_serve -v
```

Résultat observé avant le code de production :

```text
ModuleNotFoundError: No module named 'sentinelfonctionnelle.web'
argument command: invalid choice: 'serve'
FAILED (errors=3)
```

L’échec correspondait aux deux frontières absentes : paquet web et point
d’entrée `serve`.

## Test GREEN

La commande ciblée réussit après la refonte :

```text
Ran 9 tests
OK
```

Les tests créent deux projets, un plan de test, une suite, un dossier et un
cas de test par formulaires HTTP. Une seconde composition sur le même fichier
SQLite retrouve les identifiants. Ils vérifient aussi le parent obligatoire du
cas, l’ordre `Contexte / Étapes / Données / Résultats`, l’appariement entre
étapes et résultats, le renommage, le déplacement et l’archivage récursif.

## Suite complète

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Résultat :

```text
Ran 31 tests in 2.538s
OK
```

## Point d’entrée réel

Un processus distinct a été lancé avec :

```powershell
.\.venv\Scripts\python.exe -m sentinelfonctionnelle.cli serve `
  --database <fichier-temporaire> --host 127.0.0.1 --port <port-libre>
```

La première sonde PowerShell, soumise au proxy du poste, n’a transmis aucune
requête bien que le journal Uvicorn indiquât un démarrage complet. La sonde a
été rejouée avec un client HTTP local sans proxy :

```json
{"status":"ok","mode":"local","schema_version":5}
```

Le processus et ses fichiers temporaires ont ensuite été arrêtés et supprimés.

## Inspection visuelle

- application desktop : Chrome headless, `1440 × 1000`, pages Plan et Cas,
  `clientWidth=1440`, `scrollWidth=1440` ;
- application mobile : Chrome headless, `390 × 844`, pages Plan et Cas,
  `clientWidth=390`, `scrollWidth=390` ;
- fil d’Ariane vérifié avec projet, plan, suite, dossier et cas ;
- formulaire du cas vérifié avec les valeurs héritées de la suite ;
- barre des sections mobile vérifiée en grille `2 × 2`, sans texte coupé ;
- aucun débordement horizontal constaté.

Le validateur du skill documentaire et ses tests ont ensuite réussi :

```text
OK: docs\tutorial-local.html est structurellement valide et traçable.
Ran 2 tests
OK
```

Les commandes `demo-hierarchy`, `demo-deployment --mode local` et
`demo-persistence` présentées dans le tutoriel sont couvertes par la suite
d’acceptation. La dernière suite complète compte 31 tests réussis, dont le
refus HTTP 400 d’un identifiant de parent invalide.

## Revue de sécurité et limites

- écoute par défaut sur `127.0.0.1` ;
- aucune identité transmise par formulaire en mode local ;
- requêtes SQL paramétrées et migration SQLite transactionnelle v5 ;
- échappement automatique des valeurs par Jinja ;
- le mode `online` est refusé explicitement tant que l’authentification et la
  persistance partagée ne sont pas composées ;
- cette tranche ne lance aucun navigateur de test, code généré, LLM ou charge ;
- l’interface locale n’implémente pas encore de protection CSRF : elle ne doit
  donc pas être exposée sur une interface réseau partagée.
