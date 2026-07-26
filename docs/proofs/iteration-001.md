# Preuve — itération 001

## Périmètre

- Spécifications : `EF-001`, `EF-002`, `EF-007`
- Acceptation : `ACC-002`, `ACC-003`
- Objectif observable : créer une suite, une sous-suite et deux tests, puis
  déplacer un test en conservant son identifiant et son historique.

## Fichiers modifiés

- `.gitignore`
- `pyproject.toml`
- `src/sentinelfonctionnelle/domain/hierarchy.py`
- `src/sentinelfonctionnelle/application/hierarchy_demo.py`
- `src/sentinelfonctionnelle/cli.py`
- fichiers `__init__.py` des paquets
- `tests/acceptance/test_hierarchy.py`
- `tests/acceptance/test_cli_hierarchy.py`
- `docs/IMPLEMENTATION_STATUS.md`
- `README.md`

## Test RED

Commande :

```powershell
python -m unittest tests/acceptance/test_hierarchy.py -v
```

Résultat observé avant tout code de production :

```text
ModuleNotFoundError: No module named 'sentinelfonctionnelle'
Ran 1 test
FAILED (errors=1)
```

L'échec est celui attendu : le contrat comportemental est chargé, mais le
domaine n'existe pas encore.

## Test GREEN

Commande ciblée :

```powershell
python -m unittest tests/acceptance/test_hierarchy.py -v
```

Résultat :

```text
Ran 2 tests in 0.001s
OK
```

## Suite complète

Commande :

```powershell
python -m unittest discover -s tests -p 'test_*.py' -v
```

Résultat :

```text
test_demo_hierarchy_exercises_creation_and_move ... ok
test_acc_002_creates_a_suite_subsuite_and_two_tests ... ok
test_acc_003_move_preserves_identity_and_result_history ... ok
Ran 3 tests in 0.133s
OK
```

La vérification syntaxique `python -m compileall -q src tests` réussit également.

## Point d'entrée réel

Commande :

```powershell
$env:PYTHONPATH = "src"
python -m sentinelfonctionnelle.cli demo-hierarchy
```

Résultat observable :

```json
{
  "moved_test": {
    "history_count": 1,
    "id": "<identifiant stable>",
    "original_id": "<même identifiant stable>",
    "path": [
      "Régression",
      "Paiement refusé"
    ]
  },
  "node_count": 4,
  "test_count": 2
}
```

Le point d'entrée crée une suite, une sous-suite et deux tests. Il rattache un
résultat au second test, le déplace, puis expose la conservation de son
identifiant et de son historique.

## Limites externes

- Python 3.14 est disponible.
- `pytest` et FastAPI ne sont pas installés ; cette première tranche utilise
  uniquement la bibliothèque standard.
- La persistance SQLite et l'interface web ne font pas partie de cette première
  tranche comportementale.

## Revue sécurité

Cette tranche ne navigue pas, ne traite aucun secret et n'exécute aucun code
généré. Aucune surface sensible supplémentaire n'est introduite.
