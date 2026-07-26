# Preuve — itération 004

## Périmètre

- Spécifications : `DOC-001` à `DOC-006`
- Acceptation : `ACC-054`
- Objectif observable : fournir un tutoriel HTML autonome, traçable et fidèle
  aux fonctions locales vérifiées.

## Fichiers modifiés

- `docs/SPECIFICATIONS.md`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/tutorial-local.html`
- `docs/proofs/iteration-004.md`
- `README.md`
- `skills/write-implementation-html-docs/SKILL.md`
- `skills/write-implementation-html-docs/agents/openai.yaml`
- `skills/write-implementation-html-docs/scripts/validate_html_doc.py`
- `tests/documentation/test_local_tutorial.py`
- `tests/documentation/__init__.py`

## Skill utilisé

- `write-implementation-html-docs`
- validation structurelle du skill : contrôle de secours réussi ;
- limite : `quick_validate.py` ne démarre pas sans le module externe `PyYAML`.

## Test RED

Commande :

```powershell
python -m unittest tests/documentation/test_local_tutorial.py -v
```

Résultat observé avant la création du tutoriel :

```text
FileNotFoundError: docs/tutorial-local.html
AssertionError: Le tutoriel HTML doit exister.
Ran 2 tests
FAILED (failures=1, errors=1)
```

## Test GREEN

Commande ciblée :

```powershell
python -m unittest tests/documentation/test_local_tutorial.py -v
```

Résultat :

```text
Ran 2 tests in 0.109s
OK
```

Validateur autonome :

```text
OK: docs\tutorial-local.html est structurellement valide et traçable.
```

Suite complète avec la commande documentée :

```text
Ran 12 tests in 0.800s
OK
```

## Commandes documentées

Les commandes Windows suivantes ont été exercées depuis la racine du dépôt avec
`PYTHONPATH=src` :

```powershell
py -3 -m sentinelfonctionnelle.cli demo-hierarchy
py -3 -m sentinelfonctionnelle.cli demo-deployment --mode local
py -3 -m sentinelfonctionnelle.cli demo-persistence --database <base-temporaire>
py -3 -m unittest discover -s tests -p "test_*.py" -v
```

Résultats observés :

- quatre nœuds, deux tests et identité stable après déplacement ;
- deux projets et chemin de connexion en mode local ;
- deux projets restaurés, identité conservée et un résultat historique ;
- douze tests réussis.

## Inspection visuelle

- desktop : rendu 1440 px lisible, navigation latérale et cartes alignées ;
- mobile : émulation exacte de 390 px, `innerWidth=390`,
  `clientWidth=390`, `scrollWidth=390`, règle mobile active ;
- impression : feuille `@media print` présente et navigation masquée.

La connexion au navigateur intégré a échoué pendant son initialisation. Le rendu
a donc été contrôlé avec le navigateur local en mode headless et une émulation
mobile via son protocole de débogage. Les captures ont ensuite été inspectées
visuellement.

## Limites externes

- FastAPI et l’interface web ne sont pas implémentés.
- Le tutoriel doit donc présenter la CLI locale actuelle sans simuler un
  serveur web disponible.

## Revue sécurité

Le document validé :

- ne contient aucun secret ni chemin personnel ;
- ne charge aucune ressource distante ;
- n’invente aucun fichier de configuration ;
- sépare les capacités vérifiées des fonctions planifiées ;
- avertit que `--subject` simule une identité et ne constitue pas une
  authentification réelle.
