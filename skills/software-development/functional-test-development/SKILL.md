---
name: functional-test-development
description: "Use when implementing, testing, reviewing, and publishing the functional-test design and execution capabilities from numbered SentinelFonctionnelle specifications."
version: 1.0.0
author: SentinelFonctionnelle
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [functional-testing, software-development, tdd, runner, ci]
    related_skills: [functional-test-design, functional-test-generation, functional-load-test-design, test-driven-development]
---

# Développement des jeux de tests et de leur outillage

## Objectif

Faire développer les capacités de conception, génération, validation et exécution en tranches verticales vérifiables. Chaque modification doit relier une spécification stable (`EF-*`, `ENF-*`, `GEN-*`, `LOAD-*`) à un critère `ACC-*`, un test et une preuve d’exécution.

Référence normative : `docs/SPECIFICATIONS.md` dans le dépôt SentinelFonctionnelle.

## Déclencheurs

Utiliser ce skill pour :

- implémenter une exigence de SentinelFonctionnelle ;
- développer le domaine des jeux de tests ;
- développer le générateur ou le runner ;
- ajouter un profil de charge ;
- préparer une intégration GitHub Actions/GitLab CI ;
- vérifier qu’une fonctionnalité est réellement implémentée.

## Règles de périmètre

Avant toute modification :

1. vérifier le dépôt et la branche ;
2. confirmer le chemin `/opt/data/SentinelFonctionnelle` ;
3. inspecter `git status`, les tests et les fichiers concernés ;
4. sélectionner les identifiants de spécification et d’acceptation ;
5. vérifier que la fonction n’appartient pas à un autre projet.

Ne jamais déclarer une fonctionnalité terminée sur la seule base de code écrit ou de documentation.

## Cycle de développement obligatoire

### 1. Construire une tranche

Une tranche doit couvrir un chemin observable complet, par exemple :

```text
formulaire → définition structurée → validation → génération candidat → lancement contrôlé
```

ou :

```text
profil load → validation des limites → export du scénario → refus d’exécution sans adaptateur
```

Éviter de développer horizontalement toutes les couches sans un comportement utilisable.

### 2. RED — écrire le test d’abord

Pour chaque tranche :

1. choisir un `ACC-*` ;
2. écrire un test comportemental ciblé ;
3. exécuter le test ;
4. confirmer qu’il échoue pour la raison attendue ;
5. corriger les erreurs de test avant d’interpréter l’échec.

Aucun code de production ne doit être écrit avant l’échec observé, sauf configuration ou génération explicitement autorisée.

### 3. GREEN — implémenter le minimum

Implémenter uniquement ce qui rend le test vert. Respecter les frontières :

- domaine sans FastAPI, Playwright ou fournisseur LLM ;
- application pour orchestration et ports ;
- adaptateurs pour LLM, stockage, navigateur et configuration ;
- générateur pour les artefacts candidats ;
- runner isolé pour exécution ;
- historique minimal séparé des rapports détaillés.

### 4. Vérifier GREEN et refactoriser

1. relancer le test ciblé ;
2. relancer la suite complète ;
3. exercer le vrai point d’entrée : API, CLI, bundle ou formulaire ;
4. refactoriser uniquement avec les tests verts ;
5. conserver les preuves de commande et résultat.

### 5. Revue de sécurité

Toute fonction de navigation, secret, génération, exécution ou charge doit vérifier :

- destinations autorisées ;
- secrets non écrits ;
- runner non privilégié ;
- bundle en lecture seule ;
- artefacts séparés ;
- limites CPU, mémoire, PID et durée ;
- réseau explicitement autorisé ;
- absence de socket Docker/Podman ;
- échec bloquant des contrôles système ;
- charge interdite sur une cible non autorisée.

## Ordre recommandé des tranches

1. `EF-002`, `EF-007` : projets, jeux, hiérarchie et définition structurée.
2. `EF-004`, `EF-005`, `EF-017` : dialogue, description et catalogues configurables.
3. `EF-007.1`, `EF-007.2`, `ENF-012` : préconditions, données et contrôles système.
4. `EF-008`, `EF-009` : validation individuelle et empreinte.
5. `GEN-001` à `GEN-006` : modèle intermédiaire, mapping, localisateurs et assertions.
6. `GEN-007` à `GEN-014` : fixtures, personnalisation, manifeste, contrôles et LLM borné.
7. `EF-012` à `EF-015`, `ENF-005` : runner, sélection, rapports et isolation.
8. `LOAD-001` à `LOAD-006` : définition et paramétrage de charge.
9. `LOAD-007` à `LOAD-011` : export, sécurité, résultats et contrat de futur adaptateur.
10. `EF-016`, `ENF-011` : bundle, CI et publication.

Ne pas implémenter l’exécution réelle de charge dans le MVP sans nouvelle décision de périmètre et adaptateur vérifié.

## Contrat de preuve

Pour chaque exigence implémentée, enregistrer :

```text
Spécification : GEN-...
Acceptation : ACC-...
Fichiers modifiés : ...
Test RED : commande + sortie d’échec
Test GREEN : commande + sortie de réussite
Suite complète : commande + sortie
Point d’entrée réel : commande + sortie
Limites externes : ...
Revue sécurité : ...
```

Une exigence est `vérifiée` seulement lorsque le test ciblé, la suite et le point d’entrée réel ont été exercés. Une dépendance indisponible donne l’état `implémentée mais non vérifiée`.

## Développement délégué

Si une sous-tâche est déléguée, transmettre :

- chemin exact du dépôt ;
- identifiants de spécification et d’acceptation ;
- fichiers autorisés ;
- commande de test ;
- exigence TDD ;
- livrables vérifiables : chemins, diff, commandes, sorties.

Ne pas accepter « terminé » sans preuve lisible. Vérifier soi-même le diff et rejouer les commandes critiques.

## Vérification finale

- [ ] Aucun fichier hors périmètre modifié.
- [ ] Chaque modification référence `EF-*`, `ENF-*`, `GEN-*` ou `LOAD-*`.
- [ ] Chaque exigence possède un `ACC-*` vérifié ou un état explicitement bloqué.
- [ ] Test RED observé avant implémentation.
- [ ] Test ciblé et suite complète exécutés.
- [ ] Point d’entrée réel exercé.
- [ ] Artefact généré exact vérifié par empreinte.
- [ ] Personnalisation et régénération testées.
- [ ] Runner et CI respectent les limites de sécurité.
- [ ] Tests de charge limités à l’export MVP si aucun adaptateur vérifié n’existe.
- [ ] Revue indépendante du diff final effectuée.
- [ ] État Git et publication vérifiés avec les SHA local/distant.

## Pièges courants

- Marquer une exigence implémentée sans test RED observé.
- Tester uniquement une fonction interne sans exercer le point d’entrée réel.
- Mélanger le runner, l’application de conception et les adaptateurs.
- Déclarer une charge exécutée alors que seul son export MVP existe.
- Modifier un autre projet ou publier un diff non revu.
