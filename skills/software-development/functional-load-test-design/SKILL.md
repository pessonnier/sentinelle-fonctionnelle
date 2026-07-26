---
name: functional-load-test-design
description: "Use when an LLM must guide the definition and safe parameterization of a load test distinct from a single-user performance test."
version: 1.0.0
author: SentinelleFonctionnelle
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [load-testing, performance, workload, safety, guided-input]
    related_skills: [functional-test-design, functional-test-generation, functional-test-development]
---

# Conception guidée des tests de charge

## Objectif

Définir un test `load` paramétré, versionné et exportable sans le confondre avec un test `performance`. Le LLM peut guider et proposer ; il ne lance jamais une charge et ne dépasse jamais les limites administratives.

Référence normative : `docs/SPECIFICATIONS.md`, `EF-007`, `EF-012`, `ENF-003`, `ENF-005`, `LOAD-001` à `LOAD-011`, `ACC-044` à `ACC-046`.

## Règle de distinction

- `performance` : mesure d’un parcours fonctionnel, généralement sans concurrence, avec durées et seuils.
- `load` : simulation paramétrée d’une charge concurrente ou d’un débit appliqué à des opérations autorisées.

Le MVP définit, valide, versionne et exporte `load`. Il ne prétend pas exécuter une charge réelle sans adaptateur de charge vérifié.

## Déclencheurs

Utiliser ce skill lorsqu’un fonctionnel ou un LLM doit définir un test de charge, choisir un profil, paramétrer une charge ou préparer un export `load`. Ne pas l’utiliser pour lancer une charge réelle sans adaptateur autorisé.

## Procédure

### 1. Sécuriser la cible — `LOAD-008`

Avant de demander des paramètres :

1. sélectionner un environnement autorisé ;
2. vérifier les origines autorisées ;
3. vérifier que la cible n’est pas une production interdite ;
4. charger les plafonds utilisateurs, débit, durée, volume et réseau ;
5. afficher ces plafonds au fonctionnel ;
6. refuser tout profil dépassant un plafond.

**Terminé lorsque :** l’environnement, les limites et l’adaptateur autorisé sont connus.

### 2. Choisir le profil — `LOAD-001`, `LOAD-002`

Charger `config/load-profiles.yaml` et proposer un profil administré. Vérifier :

- identifiant et libellé ;
- adaptateur et version de protocole ;
- opérations autorisées ;
- environnements autorisés ;
- limites ;
- métriques ;
- seuils par défaut.

Ne pas demander au métier de choisir un moteur technique si le profil administrateur suffit.

### 3. Définir les opérations — `LOAD-005`

Faire choisir les opérations ou parcours ciblés dans une liste autorisée. Pour chaque opération, préciser :

- poids ou fréquence ;
- données utilisées ;
- préconditions ;
- résultat attendu ;
- nettoyage ;
- origine autorisée.

Une opération inconnue, ambiguë ou non autorisée bloque l’export.

### 4. Choisir le modèle de charge — `LOAD-004`

Proposer un seul modèle à la fois :

- constante ;
- progressive ;
- paliers ;
- pointe courte ;
- endurance ;
- mixte pondéré.

Décrire concrètement l’effet du modèle avant confirmation.

### 5. Saisir les paramètres — `LOAD-003`

Collecter dans un formulaire guidé :

- utilisateurs virtuels ;
- débit cible ou fréquence d’arrivée ;
- durée ;
- montée par paliers ;
- warmup/stabilisation ;
- jeux de données ;
- profil d’environnement ;
- opérations ciblées ;
- modèle de charge.

Afficher unité, valeur courante, limite minimale et limite maximale. Ne jamais accepter une valeur vide, négative, non bornée ou incohérente.

### 6. Définir les métriques et seuils — `LOAD-006`, `LOAD-009`

Proposer puis faire confirmer :

- débit atteint ;
- taux d’erreur maximal ;
- temps moyen ;
- P95/P99 ;
- nombre minimal d’opérations réussies ;
- durée minimale.

Distinguer :

- seuils de réussite du test ;
- métriques détaillées du rapport ;
- historique minimal : date, réussite, durée.

Un dépassement produit un échec explicite.

### 7. Contrôler le scénario

Avant export, vérifier :

- toutes les opérations sont autorisées ;
- les données et fixtures existent ;
- les dépendances sont résolues ;
- les paramètres respectent les limites ;
- les seuils utilisent des unités cohérentes ;
- le profil et l’environnement sont compatibles ;
- aucune valeur sensible n’est dans le profil.

### 8. Produire l’export MVP — `LOAD-007`, `LOAD-010`

Exporter un profil versionné et un scénario indépendant de l’interface. Ne pas produire un faux code Playwright concurrent. Le bundle doit indiquer :

- type `load` ;
- profil ;
- scénario ;
- paramètres ;
- seuils ;
- métriques ;
- limites ;
- adaptateur requis ;
- statut `exporté — exécution non disponible dans le MVP`.

### 9. Encadrer le LLM — `LOAD-011`

Le LLM peut :

- proposer un profil ;
- identifier les opérations ;
- poser les questions manquantes ;
- suggérer des valeurs initiales et seuils.

Le LLM ne peut pas :

- lancer une charge ;
- augmenter un plafond ;
- déclarer la cible sûre ;
- approuver les paramètres ;
- convertir un dépassement de seuil en réussite.

## Sortie attendue

```text
Type : load
Profil : ...
Environnement : ...
Opérations : ...
Modèle : ...
Utilisateurs virtuels : ...
Débit : ...
Warmup : ...
Durée : ...
Seuils : ...
Limites appliquées : ...
Statut : exportable / bloqué / exécution post-MVP
```

## Vérification

- [ ] Type `load` distinct de `performance`.
- [ ] Profil administré et adaptateur identifiés.
- [ ] Environnement autorisé et non production interdite.
- [ ] Tous les paramètres `LOAD-003` documentés et confirmés.
- [ ] Opérations et données autorisées.
- [ ] Limites administratives respectées.
- [ ] Métriques et seuils cohérents.
- [ ] Aucun secret exporté.
- [ ] Le MVP n’est pas présenté comme exécutant une charge réelle.

## Pièges courants

- Confondre une mesure `performance` avec une charge concurrente.
- Saisir un débit sans préciser son unité.
- Dépasser les plafonds du profil ou de l’environnement.
- Générer du Playwright concurrent au lieu d’un adaptateur de charge dédié.
- Conserver des métriques détaillées dans l’historique minimal.
