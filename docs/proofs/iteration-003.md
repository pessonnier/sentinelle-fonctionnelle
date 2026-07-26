# Preuve — itération 003

## Périmètre

- Spécifications : `EF-001`, `EF-002`, `ENF-001`, `ENF-013`
- Acceptation : `ACC-053`
- Objectif observable : restaurer deux projets, une arborescence déplacée et
  son historique après redémarrage sur le même fichier SQLite.

## Fichiers modifiés

- `docs/SPECIFICATIONS.md`
- `docs/IMPLEMENTATION_STATUS.md`
- `README.md`
- `src/sentinelfonctionnelle/application/projects.py`
- `src/sentinelfonctionnelle/application/persistence_demo.py`
- `src/sentinelfonctionnelle/adapters/persistence/sqlite.py`
- `src/sentinelfonctionnelle/adapters/persistence/in_memory.py`
- `src/sentinelfonctionnelle/adapters/persistence/__init__.py`
- `src/sentinelfonctionnelle/cli.py`
- `tests/acceptance/test_sqlite_persistence.py`
- `tests/acceptance/test_cli_hierarchy.py`

## Test RED

Commande :

```powershell
python -m unittest tests/acceptance/test_sqlite_persistence.py tests/acceptance/test_cli_hierarchy.py -v
```

Résultat observé avant le code de production :

```text
AttributeError:
type object 'ProjectApplication' has no attribute 'sqlite'

sentinelfonctionnelle: error: argument command: invalid choice:
'demo-persistence'

Ran 4 tests
FAILED (failures=1, errors=1)
```

Les commandes historiques de hiérarchie et de parité restent vertes.

## Test GREEN

Commande ciblée :

```powershell
python -m unittest tests/acceptance/test_sqlite_persistence.py tests/acceptance/test_cli_hierarchy.py -v
```

Premier résultat intermédiaire : la restauration fonctionnait, mais Windows
refusait de supprimer la base temporaire car `sqlite3.Connection` validait la
transaction sans fermer le fichier. L’adaptateur ferme désormais explicitement
la connexion après commit ou rollback.

Résultat final :

```text
Ran 4 tests in 0.655s
OK
```

## Suite complète

Commande :

```powershell
python -m unittest discover -s tests -p 'test_*.py' -v
```

Résultat :

```text
Ran 10 tests in 0.610s
OK
```

La vérification syntaxique `python -m compileall -q src tests` réussit.

## Point d’entrée réel

Commande :

```powershell
$env:PYTHONPATH = "src"
python -m sentinelfonctionnelle.cli demo-persistence `
  --database C:\tmp\sentinel-acc053.db
```

Résultat après création, fermeture et réouverture de la base :

```json
{
  "history_count": 1,
  "identity_preserved": true,
  "project_count": 2,
  "restored_path": [
    "Régression",
    "Paiement refusé"
  ]
}
```

## Limites externes

- SQLite est fourni par la bibliothèque standard Python.
- PostgreSQL et FastAPI restent hors de cette tranche.

## Revue sécurité

Le fichier de base est une donnée locale de conception.

- toutes les valeurs passent par des requêtes paramétrées ;
- les clés étrangères sont activées sur chaque connexion ;
- chaque opération d’écriture utilise une transaction ;
- la migration possède une version stable et peut être rejouée ;
- une version de schéma plus récente est explicitement refusée ;
- chaque connexion est fermée après commit ou rollback ;
- aucun secret n’est ajouté au schéma.
