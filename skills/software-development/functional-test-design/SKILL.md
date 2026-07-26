---
name: functional-test-design
description: "Use when an LLM must guide a business user to specify a functional test set without YAML, clarify the test, and produce a validated structured definition."
version: 1.0.0
author: SentinelleFonctionnelle
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [functional-testing, test-design, business-user, llm, guided-input]
    related_skills: [functional-test-generation, functional-load-test-design, functional-test-development]
---

# Conception guidée des jeux de tests fonctionnels

## Objectif

Transformer une intention métier, des captures et des réponses utilisateur en une définition structurée, versionnée et validable. Le LLM aide à clarifier et proposer ; il ne confirme jamais seul une information et ne génère pas directement un code approuvable depuis la conversation.

Référence normative : `docs/SPECIFICATIONS.md`, notamment `EF-002`, `EF-004` à `EF-009`, `EF-017`, `GEN-001` à `GEN-002` et `ACC-001` à `ACC-046`.

## Déclencheurs

Utiliser ce skill lorsqu’il faut :

- créer un projet, un jeu de tests, une suite ou un test ;
- guider un fonctionnel métier qui ne doit pas écrire de YAML ;
- transformer un objectif métier en test structuré ;
- demander les précisions manquantes ;
- préparer un test pour génération et validation individuelle.

Ne pas l’utiliser pour exécuter un bundle approuvé en CI ; utiliser alors `functional-test-development` ou le runner.

## Contrat de sortie

Ne terminer la conception que lorsque les artefacts suivants existent :

1. définition structurée versionnée ;
2. description courte et factuelle ;
3. modèle de test choisi ou explicitement absent ;
4. attributs renseignés : type, tags, `requirements`, `business_rules`, environnement, données ;
5. préconditions confirmées et dépendances candidates identifiées ;
6. étapes ordonnées et résultats attendus observables ;
7. déclaration CI ;
8. critères d’approbation et questions encore bloquantes listés.

## Procédure obligatoire

### 1. Installer le contexte

1. Identifier le projet et ne jamais mélanger un autre projet.
2. Charger le vocabulaire administrateur : types, modèles, intentions, tags, environnements et profils de données.
3. Créer ou retrouver l’identifiant stable du jeu de tests.
4. Demander le périmètre : objectif, population concernée, parcours inclus et exclusions.

**Terminé lorsque :** le parent hiérarchique, l’objectif et l’environnement autorisé sont connus.

### 2. Choisir la structure

1. Proposer le niveau adapté : jeu de tests, suite, sous-suite ou test.
2. Choisir un modèle de test selon l’objectif.
3. Appliquer le type du jeu comme valeur par défaut.
4. Demander explicitement une exception si le test descendant utilise un autre type.
5. Refuser une incompatibilité de type au lieu de la corriger silencieusement.
6. Proposer des tags contrôlés, sans créer une seconde taxonomie.

**Terminé lorsque :** hiérarchie, type, modèle et tags sont confirmés.

### 3. Remplir le formulaire guidé

Pour chaque champ, afficher libellé, aide, exemple, obligatoire/facultatif, validation et origine de valeur. Ne jamais demander au métier d’écrire du YAML.

Collecter au minimum :

- nom et objectif ;
- type et modèle ;
- `requirements` comme liste plate de références/libellés courts ;
- `business_rules` comme liste plate de références/libellés courts ;
- préconditions en texte métier ;
- environnement et profil de données ;
- étapes ;
- résultats attendus ;
- postconditions ;
- tags ;
- déclaration `on_commit`, `on_merge_request`, `nightly`, `release` ou `manual` ;
- seuils si le type est `performance` ;
- paramètres de charge si le type est `load`.

**Terminé lorsque :** chaque champ obligatoire est confirmé et chaque proposition LLM est visuellement distinguée d’une valeur utilisateur.

### 4. Clarifier l’intention

Pour chaque ambiguïté, poser une question courte et une seule décision à la fois. Utiliser le modèle de test pour éviter les questions déjà résolues.

Priorité des questions :

1. acteur et droits ;
2. préconditions et état initial ;
3. données exactes ;
4. action observable ;
5. résultat attendu ;
6. nettoyage ;
7. environnement et déclaration d’exécution.

Ne pas inventer une donnée, un seuil, un localisateur ou une règle métier. Marquer `à confirmer` toute hypothèse.

### 5. Traduire les préconditions

1. Conserver la phrase originale dans la définition.
2. Proposer une traduction en préconditions exécutables, dépendances, fixtures et nettoyage.
3. Indiquer les hypothèses et les données nécessaires.
4. Faire confirmer la traduction.
5. Bloquer la génération si la phrase reste ambiguë.
6. Vérifier séparément les contrôles système : environnement, cible, fixtures, secrets référencés, navigateur, ressources et réseau.

Le LLM ne peut jamais déclarer un contrôle système réussi ni contourner un échec.

### 6. Définir les étapes et assertions

1. Décomposer le parcours en actions métier ordonnées.
2. Exiger au moins un résultat observable.
3. Reformuler les résultats en assertions vérifiables.
4. Signaler les résultats purement subjectifs ou non observables.
5. Décrire les preuves attendues.
6. Déclarer les postconditions et le nettoyage.

**Terminé lorsque :** aucune étape ne dépend d’une intention implicite et chaque résultat attendu est testable ou explicitement marqué non vérifiable.

### 7. Produire la description et soumettre à validation

Générer une description courte contenant uniquement objectif, préconditions déterminantes et résultat vérifié. Exclure les hésitations, le prompt, les justifications du LLM et les détails d’implémentation.

Présenter un récapitulatif avant validation :

```text
Objectif : ...
Type : ...
Environnement : ...
Données : ...
Préconditions confirmées : ...
Étapes : ...
Assertions : ...
Déclaration CI : ...
Hypothèses restantes : ...
```

Demander une validation explicite du test structuré. La validation ne vaut pas approbation du code.

### 8. Passer au générateur

Transmettre uniquement la version structurée confirmée, jamais la conversation brute. Appeler ensuite `functional-test-generation` avec :

- identifiant/version du test ;
- modèle et configuration effective ;
- préconditions confirmées ;
- actions et assertions ;
- jeux de données/profils ;
- politique LLM d’exécution ;
- critère `ACC-*` concerné.

## Interdictions

- Ne pas approuver seul.
- Ne pas inventer les résultats attendus.
- Ne pas enregistrer de secret.
- Ne pas transformer une phrase ambiguë en dépendance silencieuse.
- Ne pas confondre `performance` et `load`.
- Ne pas utiliser les tags pour remplacer les attributs métier.
- Ne pas appeler l’exécution CI avec un brouillon.

## Vérification

- [ ] Tous les champs visibles sont documentés.
- [ ] Les valeurs LLM sont distinguées des valeurs confirmées.
- [ ] `requirements` et `business_rules` sont plats et sans secret.
- [ ] Préconditions, fixtures et nettoyage sont confirmés.
- [ ] Les contrôles système restent déterministes.
- [ ] Au moins une assertion observable existe.
- [ ] La version structurée est enregistrée.
- [ ] Le prochain artefact est explicitement un candidat, pas une version approuvée.

## Pièges courants

- Demander au métier de modifier directement le YAML.
- Transformer une hypothèse LLM en fait confirmé.
- Oublier l’environnement, les données ou le nettoyage.
- Décrire un résultat non observable.
- Confondre validation de la définition et approbation du code.
