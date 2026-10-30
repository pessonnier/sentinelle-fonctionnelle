# Exploitation du lot 4 — bundle, runner et collaboration

Ce guide décrit les composants réellement livrés. Le runner Python et le
parcours navigateur sont vérifiés sur Windows. Les profils OCI et PostgreSQL
sont prêts à être qualifiés sur une machine disposant de Docker/Podman et d'une
instance PostgreSQL ; ces deux exécutions externes ne sont pas simulées.

## Export le plus simple

Dans la section **Candidats, validation et décision** d'un cas, exécuter puis
approuver un candidat. Le lien **Exporter le bundle CI** apparaît uniquement sur
cette version approuvée. Le ZIP est reproductible : mêmes entrées, mêmes octets.

Le bundle contient le manifeste et ses empreintes, la définition fonctionnelle,
le code approuvé, les métadonnées de génération, la configuration sans secret,
les modèles GitHub/GitLab et leurs guides distincts. Aucun résultat n'est écrit
dans le bundle.

## Exécution locale autonome

```powershell
sentinelle-run `
  --bundle .\sentinelle-bundle `
  --artifacts .\artifacts `
  --base-url http://127.0.0.1:8000 `
  --allow-origin http://127.0.0.1:8000 `
  --declaration manual
```

`--allow-origin` est obligatoire, ou fourni par
`SENTINELLE_FONCTIONNELLE_ALLOWED_ORIGINS`. Avant pytest, le runner refuse une
version inconnue, un fichier absent, ajouté ou modifié, une empreinte globale
différente, une cible hors politique, une sélection vide ou un délai invalide.
Il interdit le LLM d'exécution et produit `execution.json`, `junit.xml`, les
journaux et preuves Playwright sous le seul répertoire `artifacts`.

## Profil OCI isolé

`deployment/runner.Dockerfile` et `deployment/compose.runner.yml` imposent :
UID/GID 10001, racine et bundle en lecture seule, seul volume d'artefacts
inscriptible, `/tmp` éphémère, capacités supprimées, `no-new-privileges`,
limites PID/mémoire/CPU et réseau interne. Aucun socket de runtime ni volume de
conception n'est monté.

```powershell
docker compose -f deployment/compose.runner.yml build
docker compose -f deployment/compose.runner.yml --profile run run --rm runner
```

La cible de démonstration partage uniquement le réseau interne `test-only`.
Pour une cible externe, fournir un egress filtré et faire correspondre
`TARGET_BASE_URL` et `--allow-origin`. En production, référencer l'image par
digest.

## GitHub Actions et GitLab CI

- copier `deployment/github-actions.yml` dans
  `.github/workflows/functional-tests.yml` ; les PR ont `contents: read`, ne
  reçoivent aucun secret et publient `artifacts/` ;
- inclure `deployment/gitlab-ci.yml` ; le rapport JUnit et les preuves sont
  publiés même en échec, sans variable protégée dans une merge request non
  approuvée.

Les cas authentifiés utilisent un workflow séparé, une branche ou un
environnement protégé et des secrets injectés uniquement pendant le job.

## PostgreSQL, identités, rôles et concurrence

Installer l'adaptateur avec `pip install -e ".[online]"`, puis composer le cœur
avec `ProjectApplication.postgresql(dsn)`. Le DSN doit être `postgresql://` et
ne doit jamais entrer dans un bundle.

L'adaptateur crée transactionnellement `projects` (JSONB),
`project_memberships` et `sentinelle_schema`. Le sujet authentifié est fourni
par un adaptateur d'identité remplaçable. Le cœur refuse son absence en mode
`online`, filtre par appartenance et applique `owner`, `editor`, `viewer`.

Toute mutation partagée reçoit la révision lue avec `project_revision`. Une
écriture `UPDATE ... WHERE revision = ... RETURNING revision` refuse un jeton
obsolète. Le branchement HTTP OIDC n'est pas inventé : il doit construire une
`AuthenticatedIdentity` après validation cryptographique.

## Santé, journaux et rétention

`GET /health` expose l'état, le mode et la version de schéma. Chaque exécution
produit un identifiant, les précontrôles, la sélection, la durée, le code de
sortie et l'empreinte du bundle dans un JSON structuré sans secret.

La rétention est une prévisualisation par défaut :

```powershell
sentinelle-fonctionnelle purge-artifacts --root .\artifacts --days 30
sentinelle-fonctionnelle purge-artifacts --root .\artifacts --days 30 --apply
```

Seuls les répertoires avec un `execution.json` finalisé, lisible, expiré et
situé sous la racine exacte sont supprimables. Sauvegarder le volume de
conception avant migration ; sauvegarder les artefacts séparément.

## Diagnostics

- **empreinte différente** : refaire l'export depuis la version approuvée ;
- **origine refusée** : faire approuver l'origine puis l'ajouter à la politique ;
- **aucun cas sélectionné** : vérifier la déclaration CI ;
- **révision obsolète** : recharger, comparer puis rejouer la modification ;
- **pilote PostgreSQL absent** : installer l'extra `online` ;
- **qualification OCI** : installer Docker ou Podman, construire les images,
  lancer le profil `run`, puis archiver le manifeste et les résultats.
