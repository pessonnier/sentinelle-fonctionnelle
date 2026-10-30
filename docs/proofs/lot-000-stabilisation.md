# Preuve — lot 0 : stabilisation du socle

Date : **6 septembre 2026**

## Objectif

Rendre le dépôt installable, testable et compréhensible depuis un environnement
Python 3.12 propre, sans mélanger la suite rapide avec les scénarios Playwright
générés.

## Acceptation vérifiée

- `pytest` cible par défaut les tests produit et documentation ;
- les scénarios Playwright générés conservent une commande distincte ;
- l’environnement de référence est figé par contraintes et contrôlé au lancement ;
- une commande unique vérifie syntaxe critique, formatage progressif, typage
  progressif, liens documentaires et tests ;
- le premier formulaire est visible sur mobile et ses champs possèdent des noms
  accessibles non ambigus ;
- le README explique installation, contrôle rapide, contrôle qualité et
  préparation du navigateur.

## Observations RED

- le `.venv` historique référençait une installation Python 3.14 supprimée ;
- `pytest` collectait les tests générés sous `tests/generated` et `outputs`, puis
  produisait six erreurs faute de Chromium ;
- FastAPI 0.116.1 changeait le statut attendu d’une validation de formulaire de
  `422` vers `400`, ce qui confirme la nécessité d’un environnement figé ;
- le contrôle Ruff complet identifie 55 fichiers à reformater et Mypy 63 erreurs
  dans 11 fichiers : cette dette est conservée explicitement pour les lots de
  refactorisation, sans réécriture massive du travail en cours ;
- deux liens commençant par `/configuration/` ont permis de distinguer dans le
  vérificateur les routes applicatives des chemins de fichiers.

## Résultat GREEN

Un nouvel environnement a été créé avec le Python 3.12 embarqué, puis installé
avec :

```powershell
python -m pip install -c requirements/constraints-py312.txt -e ".[test,quality]"
```

La commande suivante réussit depuis cet environnement neuf :

```powershell
python tools/check_quality.py
```

Résultat :

```text
versions contraintes : conformes
Ruff erreurs critiques : conforme
Ruff format, base progressive : 7 fichiers conformes
Mypy, base progressive : 6 modules conformes
liens documentaires locaux : conformes
pytest : 84 tests et 32 sous-tests réussis
```

## Fichiers du lot

- `requirements/constraints-py312.txt` ;
- `tools/check_quality.py` ;
- `tests/documentation/test_quality_baseline.py` ;
- configuration qualité de `pyproject.toml` ;
- instructions de démarrage et de contrôle du `README.md` ;
- feuille de route `docs/DEVELOPMENT_PLAN.md` ;
- corrections d’accueil dans `home.html`, `app.css` et leur test d’acceptation.

## Limites conservées

- le formatage et le typage sont volontairement progressifs : imposer Ruff et
  Mypy à tout le code aurait réécrit ou bloqué les développements fonctionnels
  non encore consolidés ;
- les scénarios Playwright générés exigent toujours l’installation explicite de
  Chromium et une cible locale active ; ils ne font pas partie de la suite
  rapide ;
- l’avertissement amont concernant l’ancien pont `TestClient` est filtré par un
  motif précis pour la combinaison verrouillée ; sa suppression technique sera
  réévaluée lors de la prochaine mise à jour contrôlée des dépendances ;
- le découpage de `web/app.py`, la généralisation des vrais libellés HTML et les
  protections réseau/CSRF appartiennent aux lots suivants.

## Revue sécurité

Le contrôleur lance chaque outil avec une liste d’arguments, `shell=False` et le
Python de l’environnement courant. Il n’installe rien, n’exécute aucun artefact
Playwright et ne suit aucun lien réseau. Les contraintes sont comparées aux
distributions réellement installées avant les autres contrôles.
