# Audit et feuille de route de développement

Dernière mise à jour : **9 septembre 2026**.

Ce document mémorise les décisions prises à partir de l’audit du dépôt. Il sert
de feuille de route durable ; `IMPLEMENTATION_STATUS.md` reste la source des
preuves déjà acquises et `SPECIFICATIONS.md` reste le référentiel des exigences.

## Synthèse de l’audit

Le produit possède un socle métier sérieux : modèle canonique versionné,
frontières de sécurité explicites, profils YAML historisés, migrations SQLite,
artefacts déterministes avec empreintes et 80 tests produit/documentation
réussis. La séparation `domain` / `application` / `adapters` est pertinente pour
la cible locale actuelle et prépare les futurs adaptateurs en ligne.

La priorité n’est toutefois plus d’ajouter des capacités. Le périmètre du MVP a
atteint 90 critères d’acceptation alors que 35 sont déclarés vérifiés. La
spécification de 3 000 lignes mélange vision produit, exigences, décisions
d’architecture, exemples d’intégration et stratégie de preuve. Ce niveau de
détail est utile comme référence, mais rend la prochaine décision difficile et
ne correspond plus à un « minimum viable ».

| Axe | Appréciation | Faits observés |
|---|---|---|
| Choix métier | Bon | workflow canonique, validation humaine, séparation conception/exécution |
| Architecture | À consolider | `web/app.py` atteint 2 240 lignes et sa fabrique contient 1 630 lignes |
| Qualité | Bonne base, garde-fous incomplets | 80 tests passent ; aucun ciblage pytest par défaut, ni lint/type-check automatisé |
| Documentation | Très riche, peu synthétique | preuves nombreuses, mais duplication dans le README et états historiques contradictoires |
| Spécifications | Traçables, surdimensionnées | 90 critères et plusieurs tranches simultanément ouvertes |
| Simplicité d’usage | Correcte pour un expert QA | parcours métier concurrencé par trois entrées de configuration technique |
| Accessibilité | À corriger | l’aide imbriquée dans les libellés donne des noms accessibles tels que « Informations : Nom » |
| Reproductibilité | Fragile | environnement virtuel local lié à un Python supprimé ; dépendances non verrouillées |
| Sécurité locale | À renforcer avant diffusion | mutations sans défense CSRF dédiée et analyse HTTP fondée sur une cible saisie par l’utilisateur |

## Décisions de cadrage

1. **Stabiliser avant d’étendre.** Aucune nouvelle famille fonctionnelle n’est
   prioritaire tant que la suite par défaut, l’installation propre et les
   frontières web ne sont pas fiables.
2. **Conserver le mode local comme parcours de référence.** PostgreSQL,
   authentification partagée, publication Git et runner OCI restent prévus,
   mais ne doivent pas compliquer l’usage local avant que le cycle
   rédiger → confirmer → générer → valider soit fluide.
3. **Séparer le contrat produit de sa réalisation.** À terme,
   `SPECIFICATIONS.md` décrira le besoin et l’acceptation ; les choix techniques
   détaillés iront dans `docs/design/` et les résultats datés dans `docs/proofs/`.
4. **Privilégier la divulgation progressive.** Les réglages LLM, génération,
   JSON et politiques de sécurité restent disponibles, mais quittent le premier
   niveau du parcours d’un nouvel utilisateur.
5. **Une tranche active à la fois.** Chaque lot ci-dessous possède une sortie
   vérifiable avant l’ouverture du suivant.

## Plan priorisé

### Lot 0 — Stabilisation du socle — terminé

Objectif : obtenir un dépôt que l’on peut installer, tester et comprendre sans
connaître son historique.

- [x] isoler la suite produit/documentation des scénarios Playwright générés ;
- [x] documenter deux commandes distinctes : contrôle rapide et bout-en-bout ;
- [x] corriger les duplications et relier le README à cette feuille de route ;
- [x] corriger les irritants évidents du premier écran (espacement mobile et noms
  accessibles des champs) ;
- [x] supprimer les avertissements de collecte pytest et décider d’une stratégie de
  verrouillage des dépendances ;
- [x] ajouter un contrôle automatisé de syntaxe, format, types et liens
  documentaires.

Critères de sortie : `pytest` exécute uniquement la suite rapide et passe sur un
environnement propre ; les scénarios navigateur ont une commande explicite ; le
premier formulaire possède des noms accessibles non ambigus.

Sortie vérifiée : installation contrainte dans un environnement Python 3.12
neuf, commande qualité complète réussie, 84 tests et 32 sous-tests réussis. Le
formatage et le typage utilisent une base progressive clairement listée dans le
contrôleur. La preuve détaillée est
[`proofs/lot-000-stabilisation.md`](proofs/lot-000-stabilisation.md).

### Lot 1 — Frontières web et sécurité locale — terminé

Objectif : réduire le coût et le risque de chaque évolution d’interface.

- [x] extraire de `web/app.py` des routeurs `catalogue`, `configuration`, `cases` et
  `generation`, avec dépendances explicites ;
- [x] déplacer la composition web des adaptateurs hors des cas d’usage applicatifs ;
- [x] centraliser validation de formulaires, réponses d’erreur et redirections ;
- [x] protéger les mutations contre les requêtes cross-site ;
- [x] appliquer une politique de destination résolue (hôtes privés, redirections,
  changement DNS) à l’analyse de pages ;
- [x] ajouter des tests unitaires ciblés aux frontières, en complément des tests
  d’acceptation.

Critères de sortie : la fabrique web ne contient que la composition, chaque
routeur est testable isolément, et les requêtes cross-site ou destinations non
autorisées sont refusées par des tests dédiés.

Sortie vérifiée le 6 septembre 2026 : `web/app.py` est ramené à 83 lignes de
composition, les quatre routeurs physiques sont construits et testés séparément,
les mutations cross-site sont refusées, et le chargeur HTML épingle une adresse
publique résolue tout en contrôlant les redirections et changements DNS. La porte
qualité réussit avec 96 tests et 40 sous-tests. Voir la
[`preuve du lot 1`](proofs/lot-001-frontieres-web-securite.md).

### Lot 2 — Parcours guidé et accessibilité — terminé

Objectif : rendre le produit utilisable sans connaissance préalable du modèle.

- [x] afficher une action primaire « Créer mon premier projet » immédiatement ;
- [x] regrouper les réglages techniques sous une entrée « Administration » ;
- [x] proposer des valeurs par défaut métier pour la cible et la politique locale ;
- [x] présenter une progression courte : Projet → Plan → Cas → Validation ;
- [x] remplacer les aides imbriquées dans les `<label>` par de vrais libellés liés
  avec `for`, `id` et `aria-describedby` ;
- [x] valider clavier, lecteur d’écran, erreurs en ligne et affichages 390 px / bureau.

Critères de sortie : un nouvel utilisateur crée et confirme un premier cas sans
éditer de JSON ni ouvrir la documentation ; aucun champ n’a un nom accessible
pollué par le contrôle d’aide.

Sortie vérifiée le 7 septembre 2026 : le plan ouvre directement l’étape de
création du cas, une suite initiale est créée sans exposer l’organisation
technique, et le cas est confirmé en formulaire guidé avec le JSON masqué. La
porte qualité réussit avec 100 tests et 40 sous-tests. Les parcours bureau et
390 px, le clavier, les relations accessibles et les erreurs en ligne ont été
contrôlés dans le navigateur. Voir la
[`preuve du lot 2`](proofs/lot-002-parcours-guide-accessibilite.md).

### Lot 3 — Cycle de vie du candidat de test — terminé

Objectif : fermer la verticale de valeur déjà commencée avant les intégrations
de plateforme.

- persister le candidat LLM et son manifeste ;
- comparer deux générations et tracer leur origine ;
- exécuter le candidat depuis le cas, puis enregistrer preuves et résultat ;
- ajouter approbation, rejet et invalidation lors d’un changement du cas ;
- terminer les critères `ACC-010` à `ACC-016` et `GEN-007` à `GEN-013` réellement
  couverts par cette verticale.

Sortie vérifiée le 8 septembre 2026 : SQLite v8 conserve les fichiers, le
manifeste, l’origine et les empreintes de chaque candidat. L’écran du cas expose
l’historique, la comparaison, le téléchargement, l’exécution individuelle, ses
preuves et une décision humaine séparée. Une régénération invalide une validation
non approuvée ; une modification de définition invalide les brouillons liés à
l’ancienne version sans altérer une version déjà approuvée. La porte qualité et
le parcours réel Chromium sont consignés dans la
[`preuve du lot 3`](proofs/lot-003-cycle-candidat.md).

### Lot 4 — Exécution isolée et collaboration — implémenté, qualification externe requise

Objectif : rendre les mêmes artefacts exploitables en équipe et en CI.

- runner OCI non privilégié, racine en lecture seule et politique réseau ;
- export Git/CI reproductible ;
- PostgreSQL, authentification, rôles et concurrence optimiste ;
- observabilité, rétention et procédures opératoires ;
- seulement ensuite, profils de charge et fournisseurs supplémentaires.

Sortie du 9 septembre 2026 : export ZIP reproductible d'un candidat approuvé,
manifeste exhaustif, runner autonome à politique d'origine, JUnit/JSON et modèles
GitHub/GitLab. Le bundle réel a réussi hors du service avec Chromium. Le profil
OCI, l'adaptateur PostgreSQL JSONB, les rôles, les révisions optimistes et la
rétention sont livrés. Docker/Podman et PostgreSQL étant absents de l'hôte, leur
qualification d'intégration reste ouverte ; voir la
[`preuve du lot 4`](proofs/lot-004-execution-collaboration.md) et le
[`guide opératoire`](operations-lot4.md).

## Registre d’exécution

| Date | Lot | État | Résultat |
|---|---|---|---|
| 2026-09-06 | Lot 0 | Terminé | environnement Python 3.12 recréé et contraint ; contrôle qualité unifié réussi ; 84 tests et 32 sous-tests réussis ; [`preuve`](proofs/lot-000-stabilisation.md) |
| 2026-09-06 | Lot 1 | Terminé | quatre routeurs isolables ; composition web explicite ; protections cross-site et SSRF résolue ; 96 tests et 40 sous-tests réussis ; [`preuve`](proofs/lot-001-frontieres-web-securite.md) |
| 2026-09-07 | Lot 2 | Terminé | parcours Projet → Plan → Cas → Validation direct ; premier cas confirmé sans JSON ; navigation, libellés, erreurs et responsive vérifiés ; 100 tests et 40 sous-tests réussis ; [`preuve`](proofs/lot-002-parcours-guide-accessibilite.md) |
| 2026-09-08 | Lot 3 | Terminé | cycle candidat persistant, validation et décision humaine ; 104 tests et 40 sous-tests ; [`preuve`](proofs/lot-003-cycle-candidat.md) |
| 2026-09-09 | Lot 4 | Implémenté, qualification externe | export/runner réels ; profil OCI et PostgreSQL à qualifier ; 110 tests et 40 sous-tests ; [`preuve`](proofs/lot-004-execution-collaboration.md) |

Les changements futurs doivent mettre à jour ce registre, les critères de sortie
du lot concerné et, lorsqu’une exigence est réellement vérifiée,
`IMPLEMENTATION_STATUS.md` avec sa preuve.
