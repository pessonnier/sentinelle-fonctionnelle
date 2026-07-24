---
name: functional-test-generation
description: "Use when converting a confirmed functional-test definition into a deterministic Playwright candidate artifact, preserving customizations and requiring exact validation before approval."
version: 1.0.0
author: SentinelFonctionnelle
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [functional-testing, code-generation, playwright, artifacts, validation]
    related_skills: [functional-test-design, functional-test-development, test-driven-development]
---

# Génération du code de test fonctionnel

## Objectif

Convertir exclusivement une définition structurée confirmée en artefact candidat Playwright Python. Le code généré doit rester lisible, déterministe, autonome pendant l’exécution normale et vérifiable par empreinte.

Référence normative : `docs/SPECIFICATIONS.md`, `EF-008`, `EF-009`, `EF-012` à `EF-015`, `GEN-001` à `GEN-014`, `ENF-004` à `ENF-006`.

## Déclencheurs

Utiliser ce skill après `functional-test-design`, lorsque la définition est confirmée et versionnée. Ne jamais générer depuis un historique de conversation seul.

## Entrées obligatoires

Refuser de commencer si l’une de ces entrées manque :

- identifiant et version du test ;
- définition structurée confirmée ;
- modèle intermédiaire ou données permettant de le construire ;
- configuration effective et version de générateur ;
- environnement autorisé ;
- fixtures/profils référencés ;
- actions et assertions confirmées ;
- politique LLM d’exécution ;
- règle de personnalisation existante ;
- critère `ACC-*` à vérifier.

## Procédure

### 1. Construire le modèle intermédiaire — `GEN-001`, `GEN-002`

Normaliser :

```text
contexte + environnement
→ préconditions + dépendances
→ fixtures + données
→ actions ordonnées
→ assertions observables
→ postconditions
→ limites et preuves
→ politique LLM d’exécution
```

Valider le schéma avant toute écriture. Une ambiguïté ou un champ manquant laisse le test en conception et bloque l’artefact approuvable.

### 2. Générer de façon déterministe — `GEN-003`

Exécuter dans cet ordre :

1. résoudre composants et fixtures ;
2. générer les fichiers ;
3. formater et contrôler la syntaxe Python ;
4. analyser les secrets ;
5. générer le manifeste ;
6. calculer les empreintes ;
7. produire l’artefact candidat.

À entrées identiques, le comportement fonctionnel doit être identique. Conserver un diff entre l’ancienne et la nouvelle génération.

### 3. Traduire les actions — `GEN-004`

Utiliser uniquement le vocabulaire confirmé :

| Action | Code attendu |
|---|---|
| ouvrir | `page.goto()` avec contrôle d’origine |
| cliquer | localisateur stable puis `.click()` |
| saisir | localisateur puis `.fill()` |
| sélectionner | `.select_option()` |
| attendre | état observable, pas de `sleep` arbitraire |
| vérifier visibilité | assertion Playwright |
| vérifier texte | assertion sur contenu observable |
| vérifier URL | assertion sur URL autorisée |
| preuve | capture rattachée à l’étape |

Une action non supportée doit produire une erreur exploitable, jamais une approximation silencieuse.

### 4. Choisir les localisateurs — `GEN-005`

Ordre obligatoire : rôle/nom accessible, libellé, texte observable, attribut de test configuré, CSS stable. Refuser par défaut : coordonnées, position, identifiants générés et références temporaires d’exploration.

Enregistrer le localisateur et son niveau de fragilité dans la définition ou le manifeste.

### 5. Générer les assertions — `GEN-006`

Mapper chaque résultat attendu confirmé vers une assertion observable. Refuser un test sans assertion fonctionnelle ou de performance. Les messages du LLM ne constituent jamais une assertion.

### 6. Séparer données, fixtures et secrets — `GEN-007`

- écrire les fixtures non secrètes dans `fixtures/` ;
- écrire les paramètres non secrets dans `config/` ;
- référencer les secrets sans valeur ;
- injecter les secrets uniquement à l’exécution ;
- scanner le bundle, le manifeste, les captures et journaux avant validation.

### 7. Factoriser avec retenue — `GEN-008`, `GEN-009`

Utiliser un Page Object ou une fixture commune seulement si au moins deux tests le réutilisent ou si une frontière d’écran le justifie. Produire au minimum :

```text
tests/ pages/ fixtures/ config/ artifacts/
```

Chaque fichier porte l’identifiant du test et la version du générateur, sans prompt ni secret.

### 8. Préserver les personnalisations — `GEN-010`

Avant régénération :

1. lire le manifeste ;
2. identifier les zones personnalisées ;
3. comparer les contrats ;
4. préserver seulement les zones compatibles ;
5. produire un conflit visible sinon ;
6. créer un nouvel artefact candidat.

Ne jamais écraser une zone manuelle silencieusement.

### 9. Contrôler et empreinter — `GEN-011`, `GEN-012`, `GEN-013`

Pour `GEN-011`, produire un manifeste contenant au minimum les identifiants et versions, les fichiers et dépendances, le type, les tags, la déclaration CI, la version du générateur et les empreintes. Vérifier que le runner refuse un fichier absent, modifié, inconnu ou incompatible avec le manifeste.

Pour `GEN-012`, vérifier avant présentation : schéma, destinations, fixtures, dépendances, localisateurs, assertions, seuils et paramètres, secrets, analyse des secrets dans les fichiers générés, syntaxe et formatage. Un contrôle échoué bloque le lancement individuel et produit une action corrective explicite.

Pour `GEN-013`, l’empreinte doit inclure modèle intermédiaire, code, composants, fixtures non secrètes, configuration, générateur et format du bundle. Toute modification de l’un de ces éléments — y compris fixture, version du générateur ou format du bundle — invalide la validation précédente.

### 10. Présenter le candidat

Afficher :

- définition structurée ;
- code généré ;
- hypothèses ;
- localisateurs ;
- diff ;
- version générateur/LLM ;
- empreinte ;
- contrôles passés/échoués.

L’utilisateur doit ensuite lancer exactement cet artefact en validation individuelle. Une réussite ne vaut pas approbation automatique.

### 11. Limites de l’assistance LLM — `GEN-014`

Le LLM de conception peut proposer des actions, localisateurs, assertions, fixtures, composants et code initial, mais chaque proposition doit :

1. respecter le schéma du modèle intermédiaire ;
2. être présentée comme une proposition ;
3. être confirmée par l’utilisateur avant intégration ;
4. passer les contrôles déterministes avant génération du candidat.

Le LLM ne peut pas :

- approuver l’artefact ;
- confirmer une vérification système ;
- contourner un contrôle échoué ;
- modifier une version approuvée ;
- transformer une hypothèse en donnée confirmée.

Le LLM d’exécution est interdit dans la génération normale. Il ne peut intervenir que dans une étape adaptative explicitement autorisée par `EF-013`, avec décisions fermées, budget, délai et stratégie d’échec. Même dans ce cas, il ne peut pas :

- ajouter des étapes au test ;
- naviguer vers une origine non autorisée ;
- demander de nouveaux secrets ;
- modifier le code ou la version approuvée ;
- transformer un échec en réussite sans assertion observable ;
- rester non traçable : chaque invocation doit être identifiable dans le rapport.

## Contrat de validation

Le runner doit exécuter octet pour octet l’artefact présenté. Après modification du modèle, du code, d’un composant ou de la configuration effective :

```text
validation précédente = invalide
nouvel artefact candidat = obligatoire
nouvelle exécution individuelle = obligatoire
nouvelle approbation = obligatoire
```

## Vérification

- [ ] Entrée structurée confirmée et versionnée.
- [ ] Modèle intermédiaire validé.
- [ ] Actions supportées et assertions présentes.
- [ ] Localisateurs stables.
- [ ] Aucun secret dans le bundle.
- [ ] Personnalisations détectées et conflits visibles.
- [ ] `GEN-011` : manifeste complet et refus des bundles absents, modifiés, inconnus ou incompatibles.
- [ ] `GEN-012` : contrôles pré-approbation passés, y compris dépendances, paramètres et analyse des secrets générés.
- [ ] `GEN-013` : empreinte complète calculée et invalidation configurée.
- [ ] Artefact exact présenté puis exécuté.
- [ ] Validation invalidée après chaque modification.
- [ ] Approbation humaine explicite et liée à l’empreinte.
- [ ] `GEN-014` : assistance LLM limitée aux propositions validées et aux étapes adaptatives autorisées.

## Pièges courants

- Générer depuis la conversation brute plutôt que depuis la définition confirmée.
- Utiliser des sélecteurs temporaires ou des temporisations arbitraires.
- Écraser une personnalisation lors d’une régénération.
- Conserver un secret dans un fixture, un bundle ou un journal.
- Réutiliser une empreinte après modification du code.
