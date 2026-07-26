# Preuve — itération 002

## Périmètre

- Spécifications : `EF-001`, `EF-001.1`, `ENF-008`, `ENF-013`
- Acceptation : `ACC-051`, `ACC-052`
- Objectif observable : isoler les projets entre utilisateurs en mode en ligne
  et exercer les mêmes cas d’usage en modes local et en ligne.

## Fichiers modifiés

- `docs/SPECIFICATIONS.md`
- `docs/IMPLEMENTATION_STATUS.md`
- `README.md`
- `src/sentinelfonctionnelle/application/projects.py`
- `src/sentinelfonctionnelle/application/deployment_demo.py`
- `src/sentinelfonctionnelle/adapters/persistence/in_memory.py`
- `src/sentinelfonctionnelle/domain/hierarchy.py`
- `src/sentinelfonctionnelle/cli.py`
- fichiers `__init__.py` concernés
- `tests/acceptance/test_deployment_modes.py`
- `tests/acceptance/test_cli_hierarchy.py`

## Test RED

Commande :

```powershell
python -m unittest tests/acceptance/test_deployment_modes.py tests/acceptance/test_cli_hierarchy.py -v
```

Résultat observé avant le code de production de cette itération :

```text
ModuleNotFoundError:
No module named 'sentinelfonctionnelle.application.projects'

sentinelfonctionnelle: error: argument command: invalid choice:
'demo-deployment'

Ran 3 tests
FAILED (failures=1, errors=1)
```

Le test historique `demo-hierarchy` reste vert pendant ce RED.

## Test GREEN

Commande ciblée :

```powershell
python -m unittest tests/acceptance/test_deployment_modes.py tests/acceptance/test_cli_hierarchy.py -v
```

Résultat :

```text
Ran 6 tests in 0.434s
OK
```

## Suite complète

Commande :

```powershell
python -m unittest discover -s tests -p 'test_*.py' -v
```

Résultat :

```text
Ran 8 tests in 0.787s
OK
```

La vérification syntaxique `python -m compileall -q src tests` réussit.

## Points d’entrée réels

Commandes :

```powershell
$env:PYTHONPATH = "src"
python -m sentinelfonctionnelle.cli demo-deployment --mode local
python -m sentinelfonctionnelle.cli demo-deployment --mode online --subject alice
```

Les deux commandes retournent les mêmes résultats métier :

```json
{
  "node_count": 2,
  "project_names": [
    "Projet principal",
    "Projet secondaire"
  ],
  "test_path": [
    "Connexion",
    "Connexion réussie"
  ],
  "test_set_name": "Parcours critiques"
}
```

Seul le champ `mode` diffère. La commande en ligne sans `--subject` est refusée :

```text
Le mode online exige une identité via --subject.
OBSERVED_EXIT=1
```

## Limites externes

- Les adaptateurs SQLite, PostgreSQL et FastAPI ne sont pas encore implémentés.
- Cette tranche vérifie le cœur applicatif partagé et l’autorisation avec un
  dépôt en mémoire remplaçable.
- Le fournisseur d’identité en ligne reste un adaptateur à choisir.

## Revue sécurité

La frontière d’autorisation est centralisée dans `ProjectApplication`.

- l’absence d’identité en ligne est refusée ;
- les listes sont filtrées par appartenance ;
- un identifiant direct non autorisé produit le même résultat qu’un projet
  absent et ne révèle aucun contenu ;
- le rôle `viewer` peut consulter mais pas créer un plan de test ;
- le mode local résout une identité implicite mais passe par les mêmes contrôles.

L’objet `AuthenticatedIdentity` représente une identité déjà vérifiée. Seul le
futur adaptateur web sera autorisé à le construire depuis une session ou un
jeton validé ; la CLI actuelle est un point d’entrée de développement.
