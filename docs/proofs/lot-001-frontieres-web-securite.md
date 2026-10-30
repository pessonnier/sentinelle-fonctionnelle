# Preuve — lot 1 : frontières web et sécurité locale

Date : **6 septembre 2026**

## Objectif

Réduire le coût des évolutions web et empêcher qu’une mutation cross-site ou une
destination réseau trompeuse contourne les frontières du mode local.

## Architecture obtenue

- `web/app.py` contient 83 lignes consacrées à la composition FastAPI ;
- `catalogue_routes.py`, `configuration_routes.py`, `cases_routes.py` et
  `generation_routes.py` construisent chacun un `APIRouter` indépendant ;
- `composition.py` instancie SQLite, les catalogues, le client LLM et le chargeur
  de pages en dehors des gestionnaires HTTP et des cas d’usage ;
- `route_support.py` centralise les conversions de formulaires, projections,
  redirections et validations communes ;
- les adaptateurs remplaçables par les tests restent résolus dynamiquement depuis
  l’état de l’application.

Chaque routeur peut être construit sans base ni réseau. Les tests contrôlent ses
tags, les chemins dont il est propriétaire et l’unicité des couples méthode/URL.

## Sécurité des mutations

Le middleware traite `POST`, `PUT`, `PATCH` et `DELETE`. Il refuse avec le statut
`403` :

- `Sec-Fetch-Site: cross-site` ;
- un en-tête `Origin` d’une autre origine ;
- un `Referer` d’une autre origine lorsque `Origin` est absent.

Une requête de même origine et les clients locaux non navigateurs restent admis.
Les tests vérifient également qu’un refus ne crée aucun projet.

## Sécurité de l’analyse HTML

Le chargeur applique successivement les contrôles suivants :

1. schéma HTTP(S), absence d’identifiants et origine identique à celle du projet ;
2. résolution de toutes les adresses de l’hôte ;
3. refus des adresses privées, de lien local, multicast, réservées ou non
   spécifiées ;
4. autorisation de la seule boucle locale lorsque la politique contient
   explicitement `local-loopback` ;
5. connexion à une adresse autorisée épinglée, avec le nom d’origine conservé pour
   l’en-tête HTTP et SNI/TLS ;
6. nouvelle validation à chaque redirection, limitée à cinq sauts ;
7. refus d’un changement de résolution DNS pour une même origine pendant le
   téléchargement ;
8. acceptation exclusive de HTML/XHTML dans une limite de 2 Mio.

Les tests couvrent les réseaux privés, l’adresse de métadonnées link-local, les
adresses réservées, la boucle locale, les changements DNS, les redirections vers
une autre origine et l’adresse effectivement transmise à la connexion.

## Vérification GREEN

Commande exécutée depuis l’environnement Python 3.12 contraint :

```powershell
python tools/check_quality.py
```

Résultat :

```text
versions contraintes : conformes
Ruff erreurs critiques : conforme
Ruff format : 18 fichiers conformes
Mypy : 15 modules conformes
liens documentaires locaux : conformes
pytest : 96 tests et 40 sous-tests réussis
```

Les nouveaux tests unitaires représentent 12 tests et 8 sous-tests. La suite
d’acceptation existante confirme la conservation des parcours projet, plan, cas,
configuration LLM et génération.

## Limites assumées

- le garde cross-site autorise volontairement les clients locaux dépourvus de
  métadonnées navigateur ; le mode en ligne devra utiliser un jeton CSRF lié à la
  session authentifiée ;
- les politiques de réseau privé autres que la boucle locale restent refusées ;
  une future liste d’autorisation devra être explicite, résolue et auditée ;
- la validation des formulaires reste portée par FastAPI et le domaine. Le support
  web centralise les conversions spécifiques sans dupliquer les invariants métier.
