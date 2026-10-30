# Preuve — lot 4 : exécution portable et collaboration

Date : **9 septembre 2026**

## Résultat obtenu

- seul un candidat approuvé dont l'exécution réussie vise l'empreinte exacte
  peut être exporté ;
- l'archive est stable à l'octet et le manifeste couvre chaque fichier et
  l'empreinte globale ;
- le runner autonome refuse format, fichier, empreinte, origine ou sélection
  invalides, écrit hors du bundle et interdit le LLM d'exécution ;
- les modèles GitHub Actions et GitLab CI utilisent le même contrat CLI ;
- le profil OCI impose l'utilisateur non privilégié, les montages, limites,
  capacités et réseau attendus, sans socket de runtime ;
- l'adaptateur PostgreSQL stocke l'agrégat en JSONB, les appartenances à part et
  applique une révision atomique ;
- le cœur en ligne exige une identité, filtre par appartenance, applique les
  rôles et refuse une révision obsolète ;
- la rétention prévisualise avant toute suppression bornée.

## Vérifications

`tests/acceptance/test_lot4_bundle_runner.py` couvre la reproductibilité, le
contenu documentaire et CI, les empreintes, la séparation des écritures, la
concurrence optimiste, la rétention et les contraintes statiques OCI/CI.

La suite complète réussit avec **110 tests et 40 sous-tests**. Le lint critique,
le formatage et les liens réussissent. La stratégie Windows de contrôle
d'application bloque actuellement le module binaire de mypy ; cette réserve
d'outillage est indépendante des sources et reste visible.

## Parcours réel

La page **Refuser une connexion invalide** affiche **Exporter le bundle CI** sur
le candidat #1 approuvé, pas sur le candidat #2 à valider. La route réelle a
renvoyé HTTP 200, `application/zip` et l'empreinte
`b86d247505613c26101cb58cf9b3d654c4b3ab78672c039c0f3cdb69ca104bdf`.

Le ZIP extrait hors du service a réussi avec Chromium en **5,563 s**, code 0,
exécution `246cd07b87874c899c143f97e4fb0165`. JUnit, `execution.json` et les
journaux ont été écrits sous `.tmp/lot4-artifacts-final`, sans modifier le bundle.

## Réserve explicite

Docker, Podman et PostgreSQL ne sont pas installés sur l'hôte. Le profil OCI et
l'adaptateur PostgreSQL sont implémentés et couverts par contrats/statique, mais
leur exécution d'intégration externe reste à qualifier. La publication vers une
API Git distante et l'adaptateur HTTP OIDC restent hors de cet incrément ; aucun
faux succès n'est déclaré pour ces frontières.
