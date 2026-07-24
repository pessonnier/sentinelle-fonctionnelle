# Spécifications initiales de SentinelFonctionnelle

- **Statut :** base de cadrage à valider et affiner
- **Projet :** SentinelFonctionnelle
- **Dépôt :** `pessonnier/SentinelFonctionnelle`
- **Branche principale :** `main`
- **Licence :** MIT

## 1. Objet du document

Ce document définit :

1. la vision et le périmètre du produit ;
2. la séparation entre conception et exécution des tests ;
3. les exigences fonctionnelles et non fonctionnelles ;
4. le produit minimum viable, ou MVP ;
5. l’architecture logicielle cible ;
6. les contraintes de déploiement et d’intégration continue ;
7. les critères d’acceptation et la stratégie de développement.

Il constitue la référence initiale du produit. Chaque comportement devra néanmoins être confirmé progressivement par des critères d’acceptation et des tests automatisés.

## 2. Vision du produit

SentinelFonctionnelle est un outillage web qui aide un utilisateur à définir des jeux de tests fonctionnels à partir :

- d’indications exprimées en langage naturel ;
- de captures d’écran d’une application web ;
- de l’observation contrôlée de l’interface cible ;
- d’un dialogue avec un LLM de conception configurable.

Le résultat attendu est une bibliothèque hiérarchisée de tests fonctionnels décrits, versionnés et matérialisés par du code :

- exécutable ;
- déterministe autant que possible ;
- lisible par une équipe de développement ou de QA ;
- réutilisable ;
- personnalisable manuellement ;
- maintenable lorsque l’interface évolue ;
- intégrable dans une chaîne GitHub Actions, GitLab CI ou toute CI capable de lancer un conteneur ou une commande ;
- accompagné de ses données, versions et preuves d’exécution.

## 3. Principes structurants

### 3.1 Identité et responsabilité

Le nom officiel du projet est **SentinelFonctionnelle**.

Sa responsabilité est d’assister la conception, la génération, la validation et l’exécution de tests fonctionnels d’interfaces web.

### 3.2 Deux phases explicitement séparées

Le produit sépare la **phase de conception** de la **phase d’exécution**. Elles n’ont ni les mêmes objectifs, ni les mêmes dépendances, ni les mêmes profils LLM.

#### Phase de conception

La conception est interactive. Elle sert à transformer une intention métier en un test compréhensible et exécutable.

Pendant cette phase :

1. l’utilisateur dialogue avec un LLM de conception ;
2. il fournit des objectifs, contraintes, données et captures d’écran ;
3. le système maintient une représentation structurée du test ;
4. la description du test est remise à jour après chaque modification acceptée ;
5. l’utilisateur examine et corrige les étapes proposées ;
6. le système génère ou met à jour un artefact candidat Playwright ;
7. l’utilisateur lance individuellement cet artefact candidat exact dans un environnement isolé ;
8. il valide le comportement observé et approuve ensemble la version structurée, le code et leur empreinte ;
9. toute personnalisation ou régénération ultérieure produit un nouvel artefact candidat qui doit être relancé et approuvé.

Le LLM facilite l’analyse, le dialogue, la synthèse et la génération. Il ne remplace pas l’approbation de l’utilisateur.

#### Phase d’exécution

L’exécution est automatisable et doit fonctionner sans interaction humaine dans le cas nominal.

Pendant cette phase :

1. un runner charge une version approuvée du code généré ou personnalisé ;
2. il prépare les données et secrets fournis par l’environnement ;
3. il exécute Playwright ;
4. il produit un code de sortie, des journaux, un rapport JUnit et des preuves ;
5. il ne modifie jamais silencieusement le scénario ou le code approuvé.

Le code exécuté peut être :

- entièrement généré par SentinelFonctionnelle ;
- généré puis personnalisé par un développeur ;
- écrit manuellement mais enregistré et exécuté dans le même format de projet.

L’exécution normale ne dépend pas d’un LLM. Un LLM d’exécution peut intervenir uniquement dans un cas exceptionnel, explicitement déclaré par le test, par exemple lorsqu’un élément ne peut pas être identifié de façon déterministe. Cette intervention doit être bornée, traçable et incapable d’élargir le périmètre du test.

### 3.3 Profils LLM distincts

Le **LLM de conception** et le **LLM d’exécution** sont deux configurations indépendantes.

| Aspect | LLM de conception | LLM d’exécution |
|---|---|---|
| Finalité | Dialogue, clarification, synthèse, proposition d’étapes et génération de code | Résolution exceptionnelle d’une ambiguïté pendant un test autorisé |
| Usage | Fréquent pendant l’édition | Désactivé par défaut |
| Interaction humaine | Oui | Non dans une CI |
| Tolérance à la latence | Interactive | Faible et bornée par un délai maximal |
| Permissions | Accès au contexte de conception nécessaire | Accès minimal à l’étape et à l’observation courantes |
| Sortie | Proposition soumise à validation | Réponse structurée limitée à une décision autorisée |
| Échec | La conception reste éditable | Le test échoue ou suit une stratégie de repli explicite |
| Budget | Configurable par session ou projet | Configurable par test et plafonné |

Les deux profils doivent pouvoir utiliser des fournisseurs, endpoints, modèles, paramètres et secrets différents. L’absence de profil d’exécution ne doit jamais empêcher l’exécution des tests déterministes.

### 3.4 Organisation hiérarchique

Les tests doivent pouvoir être rangés sous forme d’arbre afin de rester lisibles lorsque leur nombre augmente.

La hiérarchie minimale est :

```text
Projet
└── Suite ou dossier
    ├── Sous-suite ou sous-dossier
    │   ├── Test
    │   └── Test
    └── Test
```

Une suite ou un test possède un nom, un ordre d’affichage et un parent facultatif. Le déplacement d’un nœud ne doit pas changer l’identité ni l’historique du test. Une profondeur maximale raisonnable pourra être imposée par l’interface sans modifier le modèle conceptuel.

### 3.4.1 Jeux de tests

Un **jeu de tests** est un regroupement fonctionnel exécutable, distinct d’un simple dossier. Il possède un objectif, un périmètre, un type, une cible, une politique d’exécution et une arborescence de tests.

La hiérarchie fonctionnelle est donc :

```text
Projet
└── Jeu de tests
    └── Suite ou dossier
        └── Test
```

Un jeu de tests doit pouvoir être exporté, validé, exécuté et historisé indépendamment des autres jeux du projet.

### 3.4.2 Types de tests

Le type d’un test ou d’un jeu de tests est choisi dans une liste administrable. Le MVP fournit au minimum :

- `smoke` : vérification rapide de disponibilité ;
- `sanity` : vérification ciblée après une modification ;
- `acceptance` : validation d’un comportement métier ;
- `regression` : vérification de comportements existants ;
- `e2e` : parcours complet de bout en bout ;
- `performance` : vérification de durées, seuils et budgets sur un parcours fonctionnel ;
- `load` : simulation paramétrée d’une charge sur une ou plusieurs opérations autorisées.

Le type `performance` ne désigne pas un test de charge ou de montée en charge. Le type `load` permet de paramétrer ces tests, mais leur exécution avec un moteur de charge dédié reste hors du périmètre d’exécution du MVP. Le MVP doit néanmoins pouvoir définir, valider la cohérence et exporter un profil de charge. Un test `performance` doit déclarer les actions mesurées, les seuils attendus et les conditions de mesure.

Le type du jeu de tests sert de valeur par défaut pour ses tests descendants. Un test peut déclarer un type différent lorsqu’il est compatible avec le jeu ; ce type explicite prévaut alors. Une incompatibilité est signalée à la saisie et bloque l’export jusqu’à correction.

### 3.4.3 Cycle de vie

Un test suit un cycle explicite :

```text
brouillon → en_conception → candidat → validé_individuellement → approuvé → actif → retiré → archivé
```

Les transitions autorisées sont : `brouillon → en_conception`, `en_conception → candidat`, `candidat → validé_individuellement`, `validé_individuellement → approuvé`, `approuvé → actif`, `actif → retiré` et `retiré → archivé`. Une modification d’un test approuvé ou actif crée un nouveau brouillon. Les retours en arrière implicites et les transitions qui sautent une validation sont refusés.

Un test en brouillon, en conception, candidat ou retiré n’est pas sélectionnable par une CI. Un test candidat peut être lancé individuellement. Un test actif est autorisé dans les jeux de tests automatisés. Les transitions sont enregistrées dans un journal d’audit distinct de l’historique synthétique des résultats.

Les transitions et leurs conditions doivent être visibles dans l’interface. L’utilisateur ne doit pas avoir à connaître les valeurs internes pour comprendre ce qui lui reste à faire.

### 3.5 Description synthétique et factuelle

Chaque test possède une description courte destinée à la navigation, à la revue et aux rapports.

Lorsqu’un test est édité par la conversation ou par le formulaire structuré :

1. le système recalcule une proposition de description à partir de l’état courant validé du test ;
2. la description exprime uniquement l’objectif, les préconditions déterminantes et le résultat vérifié ;
3. elle exclut les hésitations, justifications du LLM, détails d’implémentation et informations non confirmées ;
4. elle reste synthétique, factuelle et compréhensible hors du contexte de la conversation ;
5. l’utilisateur peut la corriger avant validation ;
6. sa version est enregistrée avec la version du test.

La conversation n’est pas la source de vérité. La représentation structurée du test et sa version approuvée le sont.

### 3.5.1 Saisie guidée et assistance

Les fonctionnels métier ne doivent pas avoir à écrire du YAML ou du code pour définir un test. La saisie principale se fait par formulaire guidé, choix de listes, texte libre et conversation. Le YAML et les autres formats structurés sont des formats d’administration, d’export et d’intégration, pas des formats de saisie attendus des utilisateurs métier.

Tous les champs affichés doivent être documentés dans l’interface avec un libellé, une aide courte, un exemple, un indicateur obligatoire/facultatif, une règle de validation et l’origine de la valeur : utilisateur, configuration ou proposition du LLM.

| Champ métier | Obligatoire | Saisie et exemple | Validation | Assistance LLM |
|---|---:|---|---|---|
| Nom du jeu de tests | oui | texte court, ex. « Parcours commande » | non vide, longueur limitée | suggestion facultative |
| Objectif du jeu | oui | texte libre décrivant le périmètre | non vide | reformulation et questions de périmètre |
| Nom du test | oui | texte court | non vide, unique dans son parent | suggestion à partir de l’objectif |
| Type de test | oui | liste administrable | valeur configurée | suggestion justifiée |
| Modèle de test | non | liste administrable | modèle disponible | sélection selon l’objectif |
| `requirements` | non | références ou libellés courts | valeurs non vides | proposition de références |
| `business_rules` | non | références ou libellés courts | valeurs non vides | proposition de règles |
| Préconditions | oui si nécessaire | texte métier libre | confirmation requise si ambigu | traduction en dépendances candidates |
| Données de test | non | tableau ou texte guidé | format du profil choisi | proposition de jeux de données |
| Environnement cible | oui | liste administrable | environnement autorisé | suggestion selon le projet |
| Profil de données | non | liste administrable | profil disponible | suggestion selon les préconditions |
| Étapes | oui | phrases décrivant les actions | au moins une étape | structuration et code candidat |
| Résultats attendus | oui | texte métier | au moins une assertion observable | reformulation en assertions |
| Postconditions | non | texte métier | dépendances nettoyables | proposition de nettoyage |
| Tags | non | choix dans une liste contrôlée | tag administré | suggestions |
| Déclaration d’exécution CI | oui | choix `on_commit`, `nightly`, etc. | valeur autorisée | proposition selon le type |
| Seuils de performance | obligatoire pour `performance` | durée ou budget | unité et seuil valides | proposition contextualisée |
| Profil de charge | obligatoire pour `load` | liste administrable | profil disponible | suggestion selon l’objectif |
| Opérations ou parcours ciblés | obligatoire pour `load` | choix guidé des opérations autorisées | opération disponible dans l’environnement | proposition selon le scénario |
| Modèle de charge | obligatoire pour `load` | constante, progressive, paliers, pointe, endurance ou mixte | modèle administré | suggestion selon l’objectif |
| Utilisateurs virtuels | obligatoire pour `load` | nombre entier | borné par l’environnement | proposition contrôlée |
| Débit cible | obligatoire pour `load` | requêtes ou parcours par seconde | unité et valeur positives | proposition contextualisée |
| Montée en charge | non pour `load` | durée et paliers | durée et paliers valides | proposition contextualisée |
| Stabilisation / warmup | non pour `load` | durée | durée positive et plafonnée | proposition contextualisée |
| Durée de charge | obligatoire pour `load` | durée | durée positive et plafonnée | proposition contextualisée |
| Données de charge | non pour `load` | jeu de données et profil d’environnement | références autorisées | proposition de profil |
| Seuils de charge | obligatoire pour `load` | taux d’erreur, débit, moyenne et percentiles | unités et limites valides | proposition contextualisée |
| Métriques collectées | obligatoire pour `load` | liste administrable | métrique compatible avec l’adaptateur | suggestion contrôlée |
| Usage exceptionnel du LLM d’exécution | non | case à cocher et justification | justification obligatoire si activé | aide à la justification |

Pour chaque champ, l’interface doit afficher le libellé, l’aide, l’exemple, le caractère obligatoire, la règle de validation et l’origine de la valeur. Ces informations sont elles-mêmes configurables par les administrateurs et sont testées avec le formulaire.

Le LLM ne peut pas approuver seul une proposition. Toute valeur proposée doit être distinguée visuellement d’une valeur confirmée.

### 3.5.2 Configuration administrable

Les administrateurs de l’outillage peuvent adapter le vocabulaire et les guides sans modifier le code de l’application. Les fichiers de configuration peuvent définir :

- les types de tests disponibles ;
- les modèles de tests ;
- les phrases décrivant les intentions fonctionnelles ;
- les valeurs de tags autorisées ;
- les environnements et profils de données disponibles ;
- les aides, exemples et champs obligatoires par contexte.

Chaque entrée de configuration possède un identifiant stable, un libellé visible, une description destinée au métier et, lorsque nécessaire, une représentation technique non visible dans le formulaire.

Le MVP prévoit au minimum les fichiers administrables suivants :

```text
config/test-types.yaml          # types, libellés et aides
config/test-models.yaml         # modèles de saisie et questions LLM
config/test-intents.yaml         # phrases d’intention fonctionnelle
config/tags.yaml                 # tags sélectionnables
config/environments.yaml         # environnements, URLs et origines autorisées
config/data-profiles.yaml        # profils de données et fixtures
config/load-profiles.yaml        # profils de charge paramétrés
```

Un modèle de test peut par exemple déclarer :

```yaml
id: create-record
label: Créer une donnée
help: Vérifie qu’un utilisateur peut créer une donnée et la retrouver.
default_type: acceptance
required_fields:
  - objective
  - preconditions_text
  - expected_results
llm_questions:
  - Quel utilisateur réalise l’action ?
  - Quelle donnée doit être créée ?
  - Comment vérifier que la création est effective ?
```

Le contenu technique des fichiers peut évoluer sans changer les libellés ni le parcours de saisie métier.

Un profil de charge peut par exemple déclarer :

```yaml
id: checkout-steady
label: Charge constante du parcours de commande
adapter: http-load
protocol_version: '1'
allowed_environments:
  - staging
allowed_operations:
  - login
  - create_order
metrics:
  - throughput
  - error_rate
  - mean_ms
  - p95_ms
default_thresholds:
  error_rate_max: 0.02
  p95_ms_max: 1000
limits:
  max_virtual_users: 50
  max_requests_per_second: 20
  max_duration_seconds: 900
workload:
  pattern: constant
  virtual_users: 10
  requests_per_second: 5
  duration_seconds: 300
  warmup_seconds: 30
thresholds:
  error_rate_max: 0.01
  p95_ms_max: 800
```

Les valeurs de `workload` ne peuvent pas dépasser les limites administratives du profil ou de l’environnement.

Le système doit vérifier la configuration au démarrage et signaler les identifiants en doublon, références inconnues ou champs incohérents.

### 3.6 Modèle d’exploration en conception

L’exploration d’une interface suit la boucle :

1. **Observer** : charger la page, collecter une représentation du DOM et une capture d’écran ;
2. **Raisonner** : interpréter l’état courant au regard du scénario en cours de conception ;
3. **Agir** : cliquer, saisir une valeur, naviguer ou attendre un changement autorisé ;
4. **Vérifier** : contrôler les résultats attendus et conserver les preuves utiles ;
5. **Itérer** jusqu’à la fin du scénario ou jusqu’à un blocage explicite.

Cette exploration aide à concevoir et valider le test. Elle ne constitue pas à elle seule une preuve que le code final s’exécute correctement.

### 3.7 Méthode de développement

Le produit doit être développé en TDD :

1. écrire un test en échec pour un comportement observable ;
2. vérifier que l’échec correspond au comportement manquant ;
3. ajouter l’implémentation minimale ;
4. exécuter le test ciblé ;
5. exécuter toute la suite ;
6. refactoriser uniquement lorsque les tests sont verts.

## 4. Utilisateurs visés

### 4.1 Testeur fonctionnel ou responsable QA

Il décrit les parcours métier, fournit des exemples visuels, organise les tests, examine les scénarios proposés et valide chaque test sans devoir écrire l’intégralité du code.

### 4.2 Développeur

Il récupère du code versionnable et compréhensible. Il peut le personnaliser sans dépendre du LLM, l’exécuter localement et l’intégrer à la CI du dépôt cible.

### 4.3 Responsable produit

Il exprime un comportement attendu sous forme de parcours et de critères d’acceptation, puis vérifie que le test approuvé correspond au besoin métier.

### 4.4 Responsable de plateforme ou DevOps

Il déploie l’outil, configure les secrets, fournit les runners et intègre les suites de tests à GitHub Actions, GitLab CI ou une autre chaîne d’intégration.

## 5. Parcours nominaux

### 5.1 Concevoir et valider un test

1. L’utilisateur crée ou ouvre un projet.
2. Il crée une suite dans l’arborescence.
3. Il crée un test et renseigne l’URL ou l’environnement cible.
4. Il sélectionne un profil LLM de conception.
5. Il décrit l’objectif métier et ajoute éventuellement des captures d’écran.
6. Le LLM pose les questions nécessaires pour lever les ambiguïtés.
7. Le système met à jour la représentation structurée et la description synthétique.
8. L’utilisateur examine puis corrige les préconditions, étapes, données et résultats attendus.
9. Le générateur produit un artefact candidat Playwright et calcule son empreinte.
10. L’utilisateur lance individuellement cet artefact candidat en mode validation.
11. Le runner isolé exécute exactement le code candidat et conserve les preuves.
12. L’utilisateur corrige le test ou personnalise le code si nécessaire, ce qui invalide la validation précédente, puis le relance.
13. Il approuve une version immuable liant le test structuré, le code validé et son empreinte.

### 5.2 Exécuter une suite dans une CI

1. La CI récupère le dépôt ou le paquet de tests approuvés.
2. Elle fournit la configuration de cible et les secrets par variables ou fichiers protégés.
3. Elle lance le runner par une commande ou une image conteneur versionnée.
4. Le runner sélectionne une suite, un dossier, un tag ou un test.
5. Il exécute le code sans appeler le service web de conception.
6. Il utilise le profil LLM d’exécution uniquement si un test l’autorise explicitement.
7. Il publie un code de sortie standard, un rapport JUnit et les artefacts configurés.
8. GitHub Actions, GitLab CI ou l’autre orchestrateur décide du succès du pipeline à partir du code de sortie.

## 6. Exigences fonctionnelles

### 6.1 Conception et organisation des tests

Cette partie décrit les fonctions utilisées par les fonctionnels métier pour définir, comprendre, organiser et valider un test. Elle ne lance pas directement le code dans le processus de l’application de conception.

### EF-001 — Gestion des projets

Le système doit permettre de créer, consulter, modifier et archiver un projet contenant au minimum un nom, une description, une cible web et une politique de sécurité. Un projet peut contenir plusieurs jeux de tests indépendants.

Un jeu de tests doit contenir au minimum :

- un nom et un objectif ;
- un type choisi dans la liste administrée ;
- une description lisible par les métiers ;
- une cible ou un profil d’environnement ;
- une arborescence de tests ;
- des tags ;
- une déclaration d’exécution.

### EF-002 — Arborescence des tests

Le système doit permettre de :

- créer, renommer, déplacer, ordonner et archiver des suites, sous-suites, dossiers et tests ;
- afficher l’arborescence sans charger toutes les preuves d’exécution ;
- conserver l’identité et l’historique d’un test déplacé ;
- sélectionner un nœud pour exécuter un test ou tous ses descendants ;
- filtrer les tests par nom, tag, état de validation ou résultat récent.

La suppression d’un nœud contenant des descendants doit exiger une confirmation et appliquer une politique explicite d’archivage ou de suppression.

L’organisation transversale complémentaire repose sur des **tags**. Aucun mécanisme parallèle de catégories libres ne doit être introduit pour remplacer les tags. Les types de tests, `requirements`, `business_rules`, profils d’environnement et déclarations d’exécution restent des attributs dédiés parce qu’ils ont une signification opérationnelle.

Les tags doivent pouvoir être ajoutés, retirés et filtrés depuis l’interface par sélection dans une liste administrée. Un utilisateur métier ne doit pas avoir à connaître le fichier qui les définit.

### EF-003 — Configuration des LLM

Le système doit proposer deux types de profils :

- **profil de conception** ;
- **profil d’exécution**.

Chaque profil doit définir indépendamment :

- le fournisseur ou protocole compatible ;
- l’URL de service ;
- le modèle ;
- les paramètres d’inférence autorisés ;
- les délais et limites de consommation ;
- une référence vers un secret, sans exposer sa valeur dans les exports ou journaux.

La connectivité de chaque profil doit être vérifiable séparément. Une configuration valide de conception n’implique pas une configuration valide d’exécution, et inversement.

### EF-004 — Dialogue de conception

Le système doit conserver un dialogue contextualisé permettant au LLM de demander des précisions sur :

- l’objectif métier ;
- les préconditions ;
- les rôles utilisateurs ;
- les données de test ;
- les résultats attendus ;
- les erreurs ou variantes à couvrir.

Une proposition du LLM ne doit jamais être présentée comme une exigence confirmée sans validation humaine.

### EF-005 — Mise à jour de la description

Après chaque échange accepté ou modification structurée d’un test, le système doit proposer une nouvelle description synthétique et factuelle.

La mise à jour doit :

- reposer sur la version structurée courante plutôt que sur le seul dernier message ;
- préserver les faits confirmés ;
- retirer les éléments devenus faux ou obsolètes ;
- éviter les formulations spéculatives ;
- être visible avant l’enregistrement de la nouvelle version ;
- rester modifiable par l’utilisateur.

### EF-006 — Gestion des captures d’écran

L’utilisateur doit pouvoir joindre des captures à un projet, une suite, un test ou une étape.

Chaque capture doit pouvoir recevoir :

- un libellé ;
- une description ;
- l’état du parcours auquel elle correspond ;
- des annotations ou zones d’intérêt ;
- une date et une provenance.

Le système doit conserver le lien entre une capture, l’étape dérivée et la version du test.

### EF-007 — Représentation structurée du test

Le système doit transformer le dialogue en une représentation structurée contenant au minimum :

- un identifiant stable ;
- un titre et une description synthétique ;
- le jeu de tests et le chemin hiérarchique ;
- le type de test ;
- les attributs `requirements` et `business_rules` ;
- les préconditions ;
- les données de test ;
- une suite ordonnée d’actions ;
- un résultat attendu par étape lorsque pertinent ;
- les postconditions ;
- les tags ;
- les hypothèses et ambiguïtés restantes ;
- la déclaration d’exécution CI ;
- les seuils et mesures attendus pour un test de type `performance` ;
- la politique d’usage exceptionnel du LLM d’exécution.

Cette représentation est la source de vérité de la génération. Le code ne doit pas être généré directement à partir d’un historique de conversation non validé.

Les attributs `requirements` et `business_rules` sont des listes simples de références ou de libellés courts, saisies comme des lignes ou des éléments sélectionnables. Ils sont facultatifs, ordonnés, sans structure imbriquée et sans secret. Une valeur vide est refusée ; une référence peut être contrôlée par une configuration administrateur, mais un texte métier court reste autorisé lorsque le référentiel externe n’est pas disponible.

### EF-007.1 — Préconditions exprimées en langage métier

L’utilisateur saisit les préconditions sous forme de texte métier, par exemple : « un client actif possède déjà un panier contenant un produit disponible ».

Le LLM de conception peut proposer une traduction structurée, mais l’utilisateur doit pouvoir la corriger et la confirmer. L’application transforme ensuite cette expression confirmée en :

- préconditions vérifiables ;
- fixtures ou jeux de données requis ;
- dépendances techniques traitées par du code ;
- actions de préparation et de nettoyage.

Le code généré doit porter la traduction confirmée. Il ne doit pas déduire silencieusement une dépendance à partir d’une phrase ambiguë.

Les vérifications système suivantes restent obligatoires avant l’exécution :

- existence et validité du profil d’environnement ;
- accessibilité de la cible autorisée ;
- disponibilité des données et fixtures requises ;
- présence des secrets référencés, sans en afficher la valeur ;
- disponibilité du navigateur et des dépendances du runner ;
- respect des limites de durée, ressources et réseau.

Le LLM peut expliquer une erreur, proposer une formulation ou suggérer une correction de la définition. Il ne peut pas déclarer une vérification système réussie et ne peut pas contourner un contrôle échoué.

### EF-007.2 — Jeux de données et profils d’environnement

Un test peut référencer plusieurs jeux de données et profils d’environnement sans contenir de secret. L’utilisateur les sélectionne par des libellés métier et non par un chemin de fichier.

L’application doit permettre de :

- choisir un jeu de données existant ;
- demander au LLM de proposer les données manquantes ;
- déclarer une donnée comme sensible sans afficher sa valeur ;
- sélectionner un environnement autorisé ;
- vérifier que les préconditions et dépendances peuvent être satisfaites ;
- produire dans le bundle les fixtures non secrètes et leurs identifiants.

Les administrateurs définissent les profils techniques, les sources et les règles de substitution dans la configuration. Un environnement possède un identifiant, un libellé, une URL cible, des origines autorisées et des références de secrets. Un profil de données possède un identifiant, un libellé, une source de fixtures et des règles de préparation/nettoyage. L’utilisateur métier ne voit que les champs et libellés nécessaires à son choix.

### EF-007.3 — Modèles de tests

L’application doit proposer une liste de modèles de tests configurable par les administrateurs. Chaque modèle fournit un nom, une description métier, un type par défaut, des champs obligatoires et une liste de questions de clarification.

Le LLM de conception peut utiliser le modèle sélectionné pour poser les questions pertinentes et ne doit pas demander les informations déjà renseignées. L’utilisateur peut changer de modèle avant validation, avec affichage des champs qui seront ajoutés ou perdus.

### EF-008 — Validation humaine et versionnement

L’utilisateur doit pouvoir :

- éditer le test proposé ;
- accepter ou refuser une étape ;
- demander une nouvelle proposition ;
- générer puis lancer individuellement l’artefact candidat du test en cours de conception ;
- consulter les preuves du lancement ;
- approuver une version immuable après validation de l’artefact exact.

Toute modification du modèle structuré ou du code après validation invalide l’état `validé individuellement` et crée un nouvel artefact candidat. Toute modification après approbation doit créer une nouvelle version brouillon. La version approuvée précédente reste exécutable et traçable jusqu’à son remplacement explicite.

### EF-009 — Lancement individuel en conception

Depuis l’éditeur, l’utilisateur doit pouvoir générer puis lancer uniquement le test courant avec la version brouillon sélectionnée. Le code lancé doit être octet pour octet celui de l’artefact candidat présenté à l’utilisateur.

Ce lancement doit :

- afficher clairement qu’il s’agit d’une validation de conception ;
- utiliser un environnement et des secrets explicitement sélectionnés ;
- montrer les étapes au fur et à mesure ;
- permettre l’arrêt ;
- produire journaux, captures, trace et résultat ;
- ne pas approuver automatiquement le test en cas de réussite ;
- enregistrer l’empreinte de l’artefact effectivement exécuté ;
- invalider le résultat dès que le modèle structuré ou le code change ;
- ne pas remplacer les résultats officiels d’une exécution de CI.

### EF-010 — Exploration contrôlée du navigateur

Le système doit pouvoir naviguer vers la cible et réaliser les actions autorisées :

- navigation ;
- clic ;
- saisie ;
- sélection ;
- attente d’un état observable ;
- lecture d’un contenu ;
- capture d’une preuve.

Les références temporaires issues d’un instantané de navigateur ou les coordonnées visuelles ne doivent pas être copiées telles quelles dans le code final. Elles servent à l’exploration, puis doivent être converties en localisateurs stables.

### EF-011 — Gestion des blocages

L’exploration ou l’exécution doit s’arrêter proprement lorsque :

- la cible n’est pas accessible ;
- un élément est introuvable ou ambigu ;
- une authentification ou une donnée manque ;
- l’action proposée sort du test autorisé ;
- une politique de sécurité interdit la cible ou l’action ;
- le nombre maximal d’étapes ou la durée maximale est atteint ;
- un éventuel LLM d’exécution ne répond pas dans ses limites.

Le système doit expliquer le blocage plutôt que d’inventer une réussite.

### 6.2 Exécution des tests et historisation

Cette partie décrit les fonctions du runner et de la CI. Elle utilise uniquement un bundle de code généré ou personnalisé, versionné et approuvé. Elle ne dépend pas de l’interface de conception.

### EF-012 — Génération et personnalisation du code

Le MVP génère des tests **Playwright en Python**.

Le code généré doit :

- être autonome vis-à-vis du LLM pendant son exécution normale ;
- utiliser des localisateurs stables, prioritairement rôle, libellé, texte ou attribut de test ;
- éviter les temporisations arbitraires lorsque Playwright peut attendre un état ;
- isoler les données variables ;
- produire des assertions explicites ;
- nettoyer l’état qu’il crée lorsque nécessaire ;
- ne contenir aucun secret en clair ;
- factoriser les comportements réellement partagés sans surarchitecture ;
- rester lisible et modifiable manuellement ;
- conserver les personnalisations identifiées lors d’une régénération ou signaler explicitement les conflits.

Pour un test `performance`, le code doit mesurer uniquement les actions et seuils déclarés. Le MVP ne génère pas de trafic concurrent ni de test de charge.

Une personnalisation produit un nouvel artefact candidat. Elle ne peut être exportée comme version approuvée ni exécutée en CI sous l’identité de la version précédente avant une nouvelle exécution individuelle réussie et une nouvelle approbation de son empreinte.

### EF-013 — Usage exceptionnel du LLM d’exécution

Un test peut activer une étape adaptative uniquement si elle est explicitement marquée et approuvée.

Une telle étape doit définir :

- la raison pour laquelle une stratégie déterministe ne suffit pas ;
- les observations transmissibles au LLM ;
- les décisions autorisées sous forme d’un schéma fermé ;
- le profil LLM d’exécution ;
- un délai maximal ;
- un budget maximal ;
- une stratégie en cas d’indisponibilité ou de réponse invalide.

Le LLM d’exécution ne peut pas :

- ajouter des étapes au test ;
- naviguer vers une autre origine non autorisée ;
- demander de nouveaux secrets ;
- modifier le code ou la version approuvée ;
- transformer un échec en réussite sans assertion observable.

Chaque invocation doit être identifiable dans le rapport. Un pipeline doit pouvoir interdire globalement toute utilisation du LLM d’exécution.

### EF-014 — Prévisualisation et traçabilité

Avant export, l’utilisateur doit pouvoir consulter :

- le test structuré ;
- sa description ;
- le code généré ou personnalisé ;
- les hypothèses ;
- les localisateurs retenus ;
- les différences avec une version précédente ;
- la version du générateur et du LLM de conception ;
- les éventuelles étapes autorisant le LLM d’exécution.

### EF-015 — Exécution automatisée

Le runner doit pouvoir lancer :

- un test ;
- une suite ou un dossier et tous ses descendants ;
- une sélection par tags ;
- l’ensemble du projet.

Il doit accepter une déclaration de sélection (`--declaration`) et ne retenir que les tests actifs dont l’attribut correspond à cette déclaration. En l’absence de déclaration, la valeur `manual` est utilisée.

Il doit accepter sa configuration par arguments, variables d’environnement et fichier versionnable sans secrets. Il doit produire :

- un code de sortie nul en cas de réussite, non nul en cas d’échec ou d’erreur ;
- un statut par test et par étape ;
- des journaux structurés ;
- un rapport JUnit XML ;
- des captures, vidéos ou traces selon la politique choisie ;
- la version exacte du test et du code exécutés.

Après chaque exécution, le runner doit produire un rapport détaillé et transmettre au service d’historisation un enregistrement de résultat contenant uniquement :

- la date de l’exécution ;
- un indicateur de réussite ;
- la durée mesurée.

L’association technique entre cet enregistrement et le test est portée par la relation de stockage et ne constitue pas un champ de l’historique métier. Le service de conception doit pouvoir importer ces enregistrements et afficher l’historique des réussites et des durées sans charger les fichiers lourds. Les journaux, traces et rapports détaillés restent des artefacts liés à l’exécution, mais ne font pas partie de l’historique synthétique. Une exécution de CI ne doit pas modifier la définition du test.

Pour un test de type `performance`, le rapport détaillé conserve les mesures et les seuils comparés. L’historique synthétique ne conserve que la réussite et la durée. Une mesure dépassant un seuil produit un échec explicite, sans être transformée en simple information.

### EF-015.1 — Déclaration d’exécution du test

Chaque test possède une déclaration simple indiquant quand il peut être sélectionné par une CI, par exemple `on_commit`, `on_merge_request`, `nightly`, `release` ou `manual`. Cette déclaration est un attribut du test, est visible dans le formulaire et peut être utilisée avec les tags pour construire une sélection.

### EF-016 — Export et intégration Git

Le système doit guider l’utilisateur lors de l’export en lui faisant choisir un jeu de tests, un environnement, une sélection de tags et un format de sortie. Les commandes techniques sont affichées sous forme de commandes prêtes à copier, mais ne sont pas exigées pour définir le test.

Le système doit permettre de produire un paquet versionnable contenant :

- le code Playwright ;
- la représentation structurée des tests ;
- l’arborescence ;
- les données d’exemple non secrètes ;
- un manifeste de versions ;
- les commandes d’installation et d’exécution ;
- des modèles GitHub Actions et GitLab CI.

L’écriture directe dans un dépôt Git exige une autorisation dédiée et limitée au dépôt concerné. L’export local et l’exécution CLI doivent rester disponibles sans accès Git distant.

### EF-017 — Catalogue de phrases d’intention fonctionnelle

La conception doit fournir un catalogue de phrases décrivant la diversité des tests fonctionnels. Le catalogue est chargé depuis un fichier de configuration administrable et peut être enrichi sans modification du code.

Le catalogue couvre au minimum :

- accéder à une fonctionnalité ;
- se connecter, se déconnecter ou expirer une session ;
- créer, consulter, modifier ou supprimer une donnée ;
- rechercher, filtrer, trier ou paginer ;
- saisir, valider, réinitialiser ou abandonner un formulaire ;
- accepter, refuser ou modifier une opération ;
- vérifier un message, une notification ou un état ;
- vérifier une permission ou un rôle ;
- gérer une erreur, une donnée invalide ou une absence de résultat ;
- importer, exporter ou télécharger ;
- effectuer un parcours de commande, paiement ou remboursement ;
- vérifier une transition d’état métier ;
- vérifier un seuil de durée pour un test `performance`.

Chaque phrase possède un identifiant, un libellé métier, des exemples, les précisions attendues et le type de test conseillé. Le LLM peut s’appuyer sur ce catalogue pour proposer les questions manquantes et les assertions adaptées. L’utilisateur confirme toujours la phrase retenue et ses paramètres.

## 7. Exigences de qualité du code de test

### 7.1 Déterminisme

À test, état initial et version de générateur identiques, le code doit conserver la même structure fonctionnelle. Les variations stylistiques du LLM de conception ne doivent pas modifier silencieusement le comportement approuvé.

### 7.2 Maintenabilité

Le test doit privilégier :

1. les rôles et noms accessibles ;
2. les libellés de formulaire ;
3. les attributs de test convenus avec l’équipe ;
4. les sélecteurs CSS stables en dernier recours.

Les sélecteurs dépendant d’une position, d’un identifiant généré ou d’une structure DOM profonde doivent être signalés comme fragiles.

### 7.3 Lisibilité

Chaque test doit exprimer clairement :

- son intention ;
- sa préparation ;
- son action principale ;
- ses assertions ;
- son nettoyage éventuel.

La hiérarchie et la description doivent permettre de comprendre le rôle d’un test sans ouvrir son historique de conversation.

### 7.4 Réutilisabilité

Les parcours partagés peuvent être extraits en fonctions, fixtures ou objets de page lorsqu’au moins deux tests justifient cette factorisation. Le MVP ne doit pas générer une hiérarchie abstraite de code par anticipation.

### 7.5 Reproductibilité

Un export doit déclarer ses versions minimales, sa commande d’installation, sa commande d’exécution et les variables d’environnement attendues.

### 7.6 Personnalisation sûre

Le code personnalisé doit être distingué du code régénérable. Une régénération doit soit préserver les zones personnalisées par un mécanisme explicite, soit produire un conflit visible ; elle ne doit jamais écraser silencieusement une modification humaine.

## 8. Exigences non fonctionnelles

### ENF-001 — Déploiement simple

Une instance monoposte ou une petite équipe doit pouvoir déployer la phase de conception avec :

- une image OCI versionnée ;
- une commande Docker ou Podman ;
- un volume persistant ;
- un fichier de configuration et des secrets externes.

Le MVP ne doit pas imposer Kubernetes, Redis, un bus de messages ou plusieurs bases de données.

### ENF-002 — Runner autonome

Le runner d’exécution doit être installable et lançable indépendamment du service web de conception. Il doit pouvoir fonctionner :

- depuis une image OCI versionnée ;
- depuis un environnement Python verrouillé ;
- sans accès à la base de données de conception ;
- sans LLM lorsque les tests sélectionnés sont déterministes.

### ENF-003 — Sécurité des destinations

Les URL fournies par l’utilisateur doivent être validées avant tout accès. Par défaut, le moteur doit refuser ou encadrer strictement :

- les schémas non HTTP(S) ;
- les métadonnées cloud ;
- les adresses internes ou de boucle locale lorsqu’elles ne sont pas explicitement autorisées ;
- les redirections vers une destination interdite.

Cette politique doit être configurable par un administrateur, pas contournable par un LLM.

### ENF-004 — Protection des secrets

Les mots de passe, jetons et clés doivent être stockés dans un mécanisme de secrets. Ils doivent être masqués dans l’interface, les prompts, les journaux, les captures et les exports.

En CI, les secrets proviennent des mécanismes protégés de GitHub, GitLab ou de l’orchestrateur choisi. Aucun secret ne doit être requis dans un fichier suivi par Git.

### ENF-005 — Isolation d’exécution

Le navigateur et le code de test généré ou personnalisé sont considérés comme non fiables. Dans le MVP, ils doivent s’exécuter dans un conteneur runner distinct de l’application de conception avec les garanties minimales suivantes :

- utilisateur non privilégié ;
- système de fichiers racine en lecture seule ;
- bundle monté en lecture seule ;
- seul le répertoire d’artefacts est accessible en écriture ;
- répertoire temporaire dédié et supprimé après le job ;
- aucun montage du volume de conception, de sa base SQLite ou de son stockage d’artefacts ;
- aucun accès au socket Docker, Podman ou au socket d’un autre orchestrateur ;
- capacités Linux supprimées et option `no-new-privileges` ;
- limites de CPU, mémoire, PID et durée ;
- secrets injectés uniquement pour le job et limités à la cible concernée ;
- réseau refusé par défaut hors origines explicitement autorisées, endpoint LLM d’exécution compris lorsqu’il est nécessaire.

Le conteneur de validation de conception et le conteneur utilisé en CI appliquent le même profil minimal d’isolation. Une impossibilité technique d’appliquer une limite exigée doit faire échouer le lancement plutôt que dégrader silencieusement l’isolation.

### ENF-006 — Auditabilité

Chaque décision automatisée importante doit être rattachée à :

- une demande utilisateur ou une étape approuvée ;
- une version de test ;
- une version de code ;
- une version de modèle et de prompt lorsqu’un LLM intervient ;
- une observation ou preuve ;
- une action résultante.

### ENF-007 — Confidentialité

La politique de conservation des conversations, captures, traces et prompts doit être explicite. La suppression d’un projet doit pouvoir supprimer ses artefacts selon la politique définie.

### ENF-008 — Portabilité

Le domaine métier doit être indépendant des adaptateurs de LLM, de stockage, de navigateur et de CI. Un test exporté ne doit pas dépendre d’un identifiant interne opaque pour être exécuté.

### ENF-009 — Résilience

Une indisponibilité du LLM de conception, du LLM d’exécution, du navigateur ou de la cible doit produire un état structuré et compréhensible. Aucun composant ne doit simuler un succès pour masquer une dépendance indisponible.

### ENF-010 — Observabilité

Les journaux doivent permettre de corréler un projet, un test, une génération et une exécution sans enregistrer de secrets. Des métriques minimales doivent couvrir les durées, échecs, usages des LLM et causes de blocage.

### ENF-011 — Compatibilité CI

L’intégration ne doit pas dépendre d’une API propriétaire de GitHub ou GitLab pour exécuter les tests. Le contrat primaire est :

- une commande non interactive ;
- des codes de sortie standards ;
- des rapports JUnit XML ;
- des artefacts sur le système de fichiers ;
- une configuration par environnement ;
- une image OCI épinglable par version ou digest.

Les adaptateurs GitHub Actions et GitLab CI sont des modèles de commodité construits sur ce contrat portable.

### ENF-012 — Vérifications système des préconditions

Avant toute exécution, le runner doit effectuer et journaliser un contrôle déterministe de la cible, de l’environnement, des données, des secrets référencés, du navigateur, des ressources et du réseau autorisé. Un contrôle impossible ou échoué doit empêcher l’exécution et produire un résultat explicite.

Ces vérifications système ne peuvent pas être remplacées par une réponse d’un LLM. Le LLM de conception peut seulement aider à formuler la demande, expliquer le résultat ou proposer une modification soumise à validation humaine.

## 9. Modèle conceptuel

### Projet

Regroupe des jeux de tests, une cible, des profils autorisés et une politique de sécurité.

### Jeu de tests

Regroupe un objectif, un type, une cible, une déclaration d’exécution, des tags et une arborescence de tests. Il peut être exporté et exécuté indépendamment.

### Nœud hiérarchique

Représente une suite, un dossier ou un test avec un identifiant stable, un parent, un ordre et des tags.

### Profil LLM de conception

Décrit l’adaptateur, l’endpoint, le modèle, les paramètres, limites et référence de secret utilisés pendant l’édition.

### Profil LLM d’exécution

Décrit séparément l’adaptateur, l’endpoint, le modèle, les paramètres, limites et référence de secret autorisés pour une étape adaptative.

### Conversation de conception

Conserve les échanges utiles à l’édition sans devenir la source de vérité du test.

### Test structuré

Versionne le titre, la description synthétique, le type, les attributs `requirements` et `business_rules`, les préconditions exprimées par le métier, leur traduction en dépendances exécutables, les jeux de données, le profil d’environnement, les étapes, assertions, hypothèses, tags, déclaration d’exécution et politique d’usage du LLM d’exécution.

### Version de test

Possède un état `brouillon`, `artefact candidat`, `validé individuellement`, `approuvé` ou `retiré`. Une validation individuelle référence l’empreinte exacte du code exécuté. Une version approuvée lie de façon immuable le test structuré, l’artefact validé et cette empreinte.

### Capture et observation

Conservent une preuve visuelle ou structurée et leur relation avec une étape et une version.

### Artefact de code

Associe une version de test à du code Playwright généré ou personnalisé, à un manifeste, à la version du générateur et à une empreinte. Un artefact est candidat jusqu’à son exécution individuelle réussie et son approbation. Toute modification de fichier change l’empreinte et annule la validation précédente.

### Exécution

Associe un artefact immuable à un environnement, un déclencheur, un résultat, des journaux, des rapports et des preuves.

### Historique de résultat

Conserve uniquement, pour chaque résultat, la date, l’indicateur de réussite et la durée. L’association au test est une relation technique de stockage ; elle n’est pas un champ de l’historique métier. Les rapports détaillés, journaux, captures et traces restent des artefacts séparés.

### Journal d’audit du cycle de vie

Conserve séparément les transitions d’état, l’utilisateur, la date et la version concernée. Ce journal ne doit pas être utilisé comme historique synthétique des résultats.

### Modèle de test

Décrit un parcours de saisie guidée avec un type par défaut, des champs obligatoires, des aides, des exemples et des questions utilisées par le LLM de conception.

### Phrase d’intention

Décrit une famille de comportements fonctionnels et les précisions nécessaires à sa transformation en test structuré.

## 10. Architecture logicielle

### 10.1 Objectifs d’architecture

L’architecture doit optimiser en priorité :

1. la simplicité de déploiement pour une petite équipe ;
2. l’autonomie du runner dans une CI ;
3. la séparation forte entre conception et exécution ;
4. la portabilité entre GitHub Actions, GitLab CI et d’autres orchestrateurs ;
5. la capacité à remplacer un fournisseur LLM ;
6. la sécurité des secrets et des navigations ;
7. l’évolution progressive vers plusieurs workers sans imposer cette complexité au MVP.

### 10.2 Vue d’ensemble

```text
                         PHASE DE CONCEPTION
┌──────────────┐   HTTPS   ┌────────────────────────────────────┐
│ Navigateur   │──────────▶│ Application SentinelFonctionnelle  │
│ utilisateur  │◀──────────│                                    │
└──────────────┘            │  UI + API applicative              │
                            │  Domaine et versionnement          │
                            │  Orchestrateur de conception       │
                            │  Générateur Playwright             │
                            └──────┬───────────┬───────────┬─────┘
                                   │           │           │
                                   ▼           ▼           ▼
                              Stockage    LLM de       Worker local
                              persistant  conception   de validation
                                                           │
                                                           ▼
                                                     Application cible

                         ARTEFACT VERSIONNÉ
                            Tests Playwright
                            + manifeste
                            + arborescence
                            + configuration

                         PHASE D’EXÉCUTION
┌─────────────────┐       ┌──────────────────────┐       ┌───────────────┐
│ GitHub Actions, │──────▶│ Runner autonome OCI │──────▶│ Application   │
│ GitLab CI, CLI  │       │ ou paquet Python    │       │ cible         │
└─────────────────┘       └──────┬───────────────┘       └───────────────┘
                                 │
                                 ├── JUnit XML, traces, captures, code de sortie
                                 └── LLM d’exécution optionnel et borné
```

### 10.3 Choix structurants du MVP

Le MVP adopte un **monolithe modulaire** pour la conception et un **runner séparé** pour l’exécution.

Ce choix évite de déployer prématurément plusieurs services tout en maintenant une frontière logicielle claire.

#### Application de conception

- **Langage :** Python.
- **API et serveur web :** FastAPI.
- **Interface :** pages web servies par l’application, enrichies progressivement ; aucun second backend n’est requis.
- **Domaine :** modules Python sans dépendance directe à FastAPI, Playwright ou à un fournisseur LLM.
- **Persistance MVP :** SQLite sur volume persistant pour un déploiement simple.
- **Artefacts MVP :** système de fichiers sur volume persistant, derrière une interface de stockage.
- **Migrations :** mécanisme versionné exécuté explicitement au démarrage ou par commande dédiée.
- **Validation navigateur :** runner conteneurisé distinct, sans montage du volume de conception et conforme au profil d’isolation défini par `ENF-005`.

SQLite et le stockage local sont des valeurs par défaut de déploiement, pas des dépendances du domaine. Les interfaces doivent permettre l’ajout ultérieur de PostgreSQL et d’un stockage objet.

L’application de conception ne lance jamais du code de test dans son propre processus et ne reçoit jamais un socket Docker ou Podman. Pour le MVP complet, un second conteneur runner dédié à la validation est démarré par Docker Compose ou Podman Compose. Il reçoit les jobs et bundles minimaux par une API authentifiée interne, sans accès aux volumes de l’application.

#### Runner d’exécution

- **Langage :** Python.
- **Framework :** Playwright pour Python et pytest.
- **Interface :** CLI non interactive.
- **Distribution :** paquet Python verrouillé et image OCI incluant les navigateurs compatibles.
- **Entrées :** bundle de tests, sélecteur de suite/test/tag, URL cible, configuration et références de secrets.
- **Sorties :** code de sortie, JUnit XML, JSON structuré, journaux, captures et traces.
- **Dépendance au service web :** aucune pour exécuter un bundle déjà exporté.
- **Dépendance à un LLM :** aucune par défaut.
- **Isolation :** utilisateur non privilégié, racine en lecture seule, bundle en lecture seule, artefacts séparés, capacités supprimées, limites de ressources et réseau autorisé explicitement.

### 10.4 Modules de l’application de conception

```text
sentinelfonctionnelle/
├── domain/            # Entités, règles, états et événements métier
├── application/       # Cas d’utilisation et ports
├── adapters/
│   ├── llm/           # Adaptateurs LLM de conception et d’exécution
│   ├── persistence/   # SQLite puis autres implémentations
│   ├── artifacts/     # Volume local puis stockage objet
│   ├── configuration/ # Modèles, phrases, tags et environnements
│   ├── browser/       # Playwright pour la validation interactive
│   └── git/           # Export et intégrations Git optionnelles
├── web/               # API FastAPI, vues et ressources statiques
├── generation/        # Génération déterministe d’un candidat depuis le brouillon structuré
└── security/          # Politiques de destination, secrets et autorisations

runner/
├── cli/               # Commandes et configuration non interactive
├── selection/         # Résolution suite, dossier, test et tags
├── execution/         # Orchestration pytest/Playwright
├── load/              # Adaptateurs de charge dédiés, activables post-MVP
├── adaptive/          # Appel exceptionnel du LLM d’exécution
├── reporting/         # JUnit, JSON, traces et artefacts
└── history/           # Historique minimal : réussite, durée, date
```

Les dépendances pointent vers le domaine et les ports applicatifs. Le domaine ne dépend d’aucun adaptateur.

### 10.5 Flux de conception

1. L’interface envoie un message ou une modification structurée à l’API.
2. Le cas d’utilisation charge le brouillon courant.
3. L’orchestrateur construit un contexte minimisé pour le LLM de conception.
4. L’adaptateur exige une réponse structurée et validée par schéma.
5. Le domaine applique uniquement les changements autorisés.
6. Le service de synthèse recalcule la description factuelle.
7. Une nouvelle version brouillon est enregistrée.
8. Le générateur produit un artefact candidat et calcule l’empreinte de son bundle.
9. À la demande de l’utilisateur, le runner isolé exécute exactement cet artefact candidat.
10. Les preuves et l’empreinte exécutée sont rattachées à cette version.
11. Toute modification du test ou du code annule cette validation.
12. L’approbation fige ensemble la version structurée, l’artefact validé et son empreinte.

### 10.6 Flux d’exécution

1. Le runner valide le manifeste, les versions et la sélection demandée.
2. Il charge la configuration de l’environnement sans écrire les secrets dans les journaux.
3. Il résout l’arborescence en une liste ordonnée de tests.
4. Il lance pytest et Playwright avec les limites configurées.
5. Une étape déterministe utilise exclusivement le code approuvé.
6. Une étape adaptative vérifie d’abord qu’un LLM d’exécution est autorisé par le test et la politique du pipeline.
7. La réponse du LLM est validée par un schéma fermé avant toute action.
8. Le runner agrège les résultats et écrit les rapports détaillés.
9. Il enregistre pour chaque test la réussite, la durée et la date dans l’historique minimal.
10. Il termine avec un code de sortie standard sans dépendre du service de conception.

### 10.7 Contrats entre conception et exécution

La frontière est un bundle versionné contenant au minimum :

```text
sentinel-bundle/
├── sentinel-manifest.json
├── hierarchy.yaml
├── tests/
├── pages/
├── fixtures/
├── data/
├── load-profiles/     # Profils de charge versionnés, sans moteur embarqué dans le MVP
├── requirements.lock
├── pytest.ini
└── README.md
```

Le manifeste indique :

- la version du format ;
- l’identifiant et la version des tests ;
- l’identifiant et la version du jeu de tests ;
- le type de chaque test ;
- la version du générateur ;
- les versions Python, pytest et Playwright ;
- les profils logiques requis, sans secret ;
- les tags et chemins hiérarchiques ;
- la déclaration d’exécution de chaque test ;
- les politiques d’artefacts et d’usage du LLM d’exécution ;
- une empreinte de chaque fichier et une empreinte globale du bundle ;
- l’état d’approbation et l’empreinte validée individuellement.

Le runner doit refuser un format incompatible, un bundle incomplet ou une empreinte différente de celle approuvée avec un message explicite. Une CI ne peut exécuter un artefact modifié sous l’identité d’une version approuvée.

Un bundle contenant `load-profiles/` peut être validé et exporté par le MVP. Il ne peut être exécuté qu’après sélection d’un adaptateur de charge installé, vérifié et autorisé pour l’environnement ciblé.

### 10.8 Déploiement de la conception

Le déploiement d’évaluation de l’interface, sans exécution de code de test, doit nécessiter :

```text
1 image OCI + 1 volume + 1 fichier de configuration + des secrets
```

Le déploiement complet du MVP, qui inclut la validation individuelle, doit utiliser :

```text
1 conteneur de conception + 1 conteneur runner isolé
+ 1 volume de conception inaccessible au runner
+ 1 espace d’échange de jobs minimal et authentifié
+ des répertoires d’artefacts dédiés
```

Un fichier Compose versionné doit rendre ce déploiement reproductible. Aucun des deux conteneurs ne reçoit le socket Docker ou Podman. Le runner ne monte jamais le volume de conception.

Les modes supportés doivent être documentés dans cet ordre :

1. `docker run` et `podman run` pour évaluer l’interface sans lancer de code non fiable ;
2. Docker Compose ou Podman Compose pour le MVP complet avec runner isolé ;
3. Kubernetes ou une plateforme équivalente uniquement comme option de montée en charge.

L’image doit :

- être versionnée et publiable par digest ;
- exécuter un utilisateur non privilégié ;
- fournir une vérification de santé ;
- séparer configuration et secrets ;
- permettre la sauvegarde du volume ;
- documenter les migrations et la restauration ;
- éviter toute dépendance implicite à un service SaaS.

### 10.9 Intégration GitHub Actions

Le dépôt doit fournir un modèle basé sur le contrat CLI portable, par exemple :

```yaml
name: functional-tests
on:
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

env:
  TARGET_BASE_URL: http://sentinel-target:8080
  SENTINEL_RUNNER_IMAGE: ghcr.io/pessonnier/sentinelfonctionnelle-runner:0.1.0
  SENTINEL_TARGET_IMAGE: ghcr.io/pessonnier/sentinelfonctionnelle-demo-target:0.1.0

jobs:
  sentinel:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - name: Prepare artifact directory
        run: |
          mkdir -p artifacts
          sudo chown 10001:10001 artifacts
      - name: Run functional tests
        run: |
          docker network create --internal sentinel-ci
          trap 'docker rm -f sentinel-target >/dev/null 2>&1 || true; docker network rm sentinel-ci >/dev/null 2>&1 || true' EXIT
          docker run -d --rm \
            --name sentinel-target \
            --network=sentinel-ci \
            --user=10001:10001 \
            --read-only \
            --cap-drop=ALL \
            --security-opt=no-new-privileges \
            "$SENTINEL_TARGET_IMAGE"
          declaration=manual
          if [ "$GITHUB_EVENT_NAME" = pull_request ]; then declaration=on_merge_request; fi
          docker run --rm \
            --network=sentinel-ci \
            --user=10001:10001 \
            --read-only \
            --cap-drop=ALL \
            --security-opt=no-new-privileges \
            --pids-limit=256 \
            --memory=2g \
            --cpus=2 \
            --tmpfs /tmp:rw,noexec,nosuid,size=512m \
            -v "$PWD/sentinel-bundle:/bundle:ro" \
            -v "$PWD/artifacts:/artifacts:rw" \
            -e TARGET_BASE_URL \
            -e SENTINEL_DECLARATION="$declaration" \
            "$SENTINEL_RUNNER_IMAGE" \
            sentinel-run --bundle /bundle --declaration "$declaration" --junit /artifacts/junit.xml
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: sentinel-results
          path: artifacts/
```

Le workflow `pull_request` ci-dessus est destiné aux tests sans secret sur une cible de démonstration jetable. Le réseau Docker `--internal` relie uniquement le runner et cette cible, sans route de sortie générale. L’image du runner garantit que l’UID/GID `10001:10001` existe et peut écrire dans `/artifacts`. Le job impose une durée maximale. Il ne transmet aucun secret au code provenant de la PR.

Les tests authentifiés ou visant une cible externe doivent utiliser un workflow séparé, déclenché uniquement depuis une branche approuvée ou un `workflow_dispatch`, associé à un environnement GitHub protégé avec approbation. Ce workflow doit attacher le runner à un réseau dont la sortie est filtrée par un proxy ou une politique d’egress limitée aux origines approuvées. Les secrets sont alors fournis par `secrets`, limités au job et jamais inscrits dans le bundle. Un workflow ne doit jamais utiliser `pull_request_target` pour exécuter le code provenant de la PR. Les PR issues de forks ou de sources non approuvées ne reçoivent aucun secret ni accès à une cible sensible.

### 10.10 Intégration GitLab CI

Le dépôt doit fournir un modèle équivalent :

```yaml
sentinel-functional-tests:
  image:
    name: ghcr.io/pessonnier/sentinelfonctionnelle-runner:0.1.0
    entrypoint: [""]
  variables:
    TARGET_BASE_URL: $SENTINEL_TARGET_BASE_URL
    SENTINEL_DECLARATION: on_merge_request
  before_script:
    - mkdir -p artifacts
  script:
    - sentinel-run --bundle ./sentinel-bundle --declaration "$SENTINEL_DECLARATION" --junit ./artifacts/junit.xml
  artifacts:
    when: always
    reports:
      junit: artifacts/junit.xml
    paths:
      - artifacts/
```

L’image garantit que `sentinel-run` est disponible dans le `PATH`. L’`entrypoint` vide rend le contrat explicite pour les runners GitLab qui injectent leur propre script.

Le modèle utilise `on_merge_request` pour un pipeline de merge request. Les jobs `on_commit`, `nightly` et `release` doivent fournir la valeur correspondante dans `SENTINEL_DECLARATION`.

Les variables sensibles utilisent les variables CI/CD masquées et protégées de GitLab et ne sont disponibles que sur les branches ou environnements protégés. Les pipelines de merge requests externes ou non approuvées n’accèdent à aucune variable protégée ni cible sensible. L’exécuteur GitLab doit lui-même être non privilégié, sans montage de socket de runtime, et appliquer les limites de ressources et la politique réseau définies par `ENF-005`.

### 10.11 Évolutivité après le MVP

Sans modifier les contrats du domaine et du bundle, une version ultérieure pourra :

- remplacer SQLite par PostgreSQL ;
- remplacer le volume local par un stockage objet ;
- exécuter les validations dans des workers distants ;
- ajouter une file de tâches ;
- proposer une authentification d’entreprise ;
- publier automatiquement des branches ou demandes de fusion ;
- prendre en charge d’autres langages ou frameworks de test.

Ces capacités ne doivent pas complexifier le déploiement minimal du MVP.

## 11. Définition du MVP

### 11.1 Objectif

Le MVP doit démontrer qu’un utilisateur peut concevoir, organiser, valider individuellement, exporter et exécuter en CI un petit ensemble de tests fonctionnels Playwright sans dépendre d’un LLM pendant l’exécution nominale.

### 11.2 Périmètre fonctionnel inclus

Le MVP est livré en deux tranches obligatoires. La première prouve la valeur fonctionnelle locale ; la seconde rend exactement les mêmes artefacts exploitables de façon sûre en CI. Le MVP n’est déclaré achevé que lorsque les deux tranches sont validées.

#### Tranche A — Conception et validation locale

1. une application web mono-instance ;
2. un projet et plusieurs jeux de tests, suites, sous-suites ou dossiers ;
3. la création, le déplacement et l’ordonnancement de tests dans l’arborescence ;
4. les types `smoke`, `sanity`, `acceptance`, `regression`, `e2e`, `performance` et `load` ;
5. le cycle de vie brouillon, en conception, candidat, validé individuellement, approuvé, actif, retiré et archivé ;
6. un profil LLM de conception configurable par endpoint, modèle et secret ;
7. un profil LLM d’exécution séparé, facultatif et désactivé par défaut ;
8. un éditeur conversationnel et structuré sans saisie YAML pour les métiers ;
9. la documentation de tous les champs du formulaire ;
10. l’ajout de captures d’écran ;
11. la mise à jour automatique d’une description synthétique et factuelle ;
12. les attributs `requirements` et `business_rules` ;
13. la saisie textuelle des préconditions et leur traduction confirmée en dépendances exécutables ;
14. les jeux de données et profils d’environnement sélectionnables par libellé ;
15. la liste administrable des modèles de tests et des phrases d’intention ;
16. la liste administrable des tags ;
17. la représentation versionnée des étapes, données et assertions ;
18. la génération d’un artefact candidat Playwright en Python ;
19. le lancement individuel de cet artefact exact dans le runner isolé ;
20. l’approbation explicite du modèle structuré, du code validé et de leur empreinte ;
21. la possibilité de personnaliser le code, avec invalidation et nouvelle validation obligatoires ;
22. une démonstration E2E sur une application cible contrôlée.

#### Tranche B — Exécution autonome et CI

1. un runner autonome capable de sélectionner un test, une suite ou des tags ;
2. des rapports console, JSON et JUnit XML ;
3. des captures et traces en cas d’échec ;
4. un bundle versionnable dont l’empreinte approuvée est vérifiée ;
5. une image OCI de conception et une image OCI de runner isolé ;
6. un fichier Compose appliquant les séparations de volumes et de secrets ;
7. des exemples Docker, Podman, GitHub Actions et GitLab CI ;
8. l’historisation minimale des réussites, durées et dates ;
9. l’évaluation des seuils de tests `performance` dans les rapports ;
10. la définition, la validation, le versionnement et l’export d’un test `load` paramétré, sans exécution par un moteur de charge dans le MVP ;
11. la prise en compte de la déclaration d’exécution du test ;
12. une démonstration CI sans secret sur une cible contrôlée.

### 11.3 Usage du LLM dans le MVP

Le LLM de conception est utilisé pour :

- poser des questions de clarification ;
- proposer des modifications structurées ;
- synthétiser la description ;
- suggérer des localisateurs ;
- générer le code initial ;
- proposer des questions à partir d’un modèle de test ;
- traduire les préconditions textuelles en dépendances candidates ;
- proposer des jeux de données, types, tags, `requirements` et `business_rules` ;
- sélectionner des phrases d’intention pertinentes.

Ces propositions restent soumises à la validation du fonctionnel métier. Les vérifications système et l’exécution du code ne sont pas déléguées au LLM de conception.

Le LLM d’exécution :

- possède une configuration indépendante ;
- est désactivé par défaut ;
- n’est utilisé que par une étape adaptative explicitement approuvée ;
- peut être interdit par un paramètre du runner ;
- ne doit pas être nécessaire à la démonstration nominale du MVP.

### 11.4 Périmètre exclu du MVP

Le MVP n’inclut pas :

- l’exploration autonome sans test borné ;
- la résolution de CAPTCHA ;
- le contournement d’une authentification ou d’un MFA ;
- les applications mobiles ou desktop natives ;
- l’exécution réelle par un moteur de charge dédié ;
- plusieurs frameworks de génération ;
- l’exécution distribuée ;
- Kubernetes comme prérequis ;
- PostgreSQL ou un stockage objet comme prérequis ;
- l’édition collaborative en temps réel ;
- la publication automatique dans un dépôt distant ;
- la correction automatique de l’application cible ;
- l’apprentissage ou le fine-tuning d’un modèle.

## 12. Critères d’acceptation du MVP

Le MVP est acceptable lorsque les critères suivants sont vérifiés par des tests automatisés et une démonstration réelle :

Chaque critère possède un identifiant stable. Le tableau suivant établit le mapping individuel entre la liste lisible et l’identifiant de suivi :

| Numéro | Identifiant | Numéro | Identifiant | Numéro | Identifiant |
|---:|---|---:|---|---:|---|
| 1 | `ACC-001` | 17 | `ACC-017` | 33 | `ACC-033` |
| 2 | `ACC-002` | 18 | `ACC-018` | 34 | `ACC-034` |
| 3 | `ACC-003` | 19 | `ACC-019` | 35 | `ACC-035` |
| 4 | `ACC-004` | 20 | `ACC-020` | 36 | `ACC-036` |
| 5 | `ACC-005` | 21 | `ACC-021` | 37 | `ACC-037` |
| 6 | `ACC-006` | 22 | `ACC-022` | 38 | `ACC-038` |
| 7 | `ACC-007` | 23 | `ACC-023` | 39 | `ACC-039` |
| 8 | `ACC-008` | 24 | `ACC-024` | 40 | `ACC-040` |
| 9 | `ACC-009` | 25 | `ACC-025` | 41 | `ACC-041` |
| 10 | `ACC-010` | 26 | `ACC-026` | 42 | `ACC-042` |
| 11 | `ACC-011` | 27 | `ACC-027` | 43 | `ACC-043` |
| 12 | `ACC-012` | 28 | `ACC-028` | 44 | `ACC-044` |
| 13 | `ACC-013` | 29 | `ACC-029` | 45 | `ACC-045` |
| 14 | `ACC-014` | 30 | `ACC-030` | 46 | `ACC-046` |
| 15 | `ACC-015` | 31 | `ACC-031` |  |  |
| 16 | `ACC-016` | 32 | `ACC-032` |  |  |

1. L’interface seule démarre avec une image OCI, un volume et une configuration documentée ; le MVP complet démarre avec le fichier Compose et son runner isolé.
2. Un utilisateur crée une arborescence contenant au moins une suite, une sous-suite et deux tests.
3. Le déplacement d’un test conserve son identifiant et son historique.
4. Un utilisateur configure et vérifie un profil LLM de conception.
5. Le profil LLM d’exécution est stocké séparément et peut rester absent.
6. Une capture valide est rattachée à un test ; un format invalide est refusé explicitement.
7. Un échange accepté met à jour le test structuré et propose une description synthétique cohérente.
8. La description ne contient ni hypothèse non confirmée ni verbatim inutile de la conversation.
9. Une réponse LLM invalide ne peut pas modifier ou approuver un test.
10. L’utilisateur génère et lance individuellement un artefact candidat, puis consulte ses étapes, preuves et empreinte.
11. Une réussite de validation ne provoque pas une approbation automatique.
12. L’approbation lie la version structurée, le code réellement exécuté et son empreinte.
13. Toute personnalisation ou régénération invalide la validation et exige un nouveau lancement avant approbation.
14. Une version approuvée est immuable ; sa modification crée un nouveau brouillon et un nouvel artefact candidat.
15. Une destination interdite est bloquée avant le lancement du navigateur.
16. Le code généré ne contient ni référence éphémère de navigateur ni secret.
17. Le runner de validation ne voit ni volume de conception, ni socket de runtime, et n’écrit que dans son répertoire d’artefacts.
18. Le test Playwright approuvé réussit sur l’application de démonstration sans LLM d’exécution.
19. Une régression volontaire de la cible fait échouer le test avec une preuve exploitable.
20. Une étape adaptative ne peut utiliser que le profil LLM d’exécution et les décisions autorisées.
21. Le runner peut interdire tout LLM d’exécution et échoue explicitement si un test en exige un.
22. Le bundle s’exécute sans connexion au service web de conception.
23. Le runner refuse un bundle dont l’empreinte diffère de l’empreinte approuvée.
24. La sélection d’une suite exécute ses descendants dans un ordre déterministe.
25. Le runner produit un code de sortie non nul en cas d’échec et un rapport JUnit valide.
26. Le modèle GitHub Actions monte le bundle en lecture seule, sépare les artefacts et n’expose aucun secret aux PR non approuvées.
27. Le modèle GitLab CI publie les rapports sans exposer de variable protégée aux merge requests non approuvées.
28. Une modification manuelle protégée n’est jamais écrasée silencieusement par une régénération.
29. Le résultat distingue clairement validation de conception et exécution automatisée.
30. Les champs du formulaire affichent un libellé, une aide, un exemple et une règle de validation.
31. Un utilisateur métier peut définir un test sans écrire de YAML.
32. Les modèles de tests, types, tags, phrases d’intention et environnements sont chargés depuis les fichiers de configuration administrables.
33. Une précondition saisie en texte est transformée en dépendances candidates puis confirmée avant génération du code.
34. Les vérifications système échouées bloquent l’exécution et ne peuvent pas être contournées par le LLM.
35. Les attributs `requirements` et `business_rules` sont conservés dans la définition et l’export du test.
36. Un test de type `performance` compare ses seuils, produit un rapport détaillé et historise sa réussite et sa durée.
37. L’historique persistant d’un test contient uniquement sa date, sa réussite et sa durée.
38. La déclaration d’exécution d’un test permet de le sélectionner pour `on_commit`, `on_merge_request`, `nightly`, `release` ou `manual`.
39. Les transitions de cycle de vie invalides sont refusées et les transitions valides sont inscrites dans le journal d’audit séparé.
40. Un test retiré ou archivé n’est jamais sélectionné par une CI.
41. Une définition confirmée est transformée en modèle intermédiaire validé avant toute génération.
42. Une action non supportée, une assertion absente ou un localisateur interdit bloque la production de l’artefact approuvable.
43. Une régénération détecte les zones personnalisées, préserve les zones compatibles et expose les conflits sans écrasement silencieux.
44. Un test `load` permet de saisir sans YAML son profil, ses opérations, ses utilisateurs virtuels, son débit, sa durée, sa montée en charge et ses seuils.
45. Les paramètres de charge dépassant les limites administratives ou de l’environnement sont refusés.
46. Le MVP valide, versionne et exporte un profil de charge, mais refuse de le présenter comme exécuté sans adaptateur de charge vérifié.

## 13. Stratégie de validation et de développement

Chaque exigence implémentée doit suivre une tranche verticale :

1. formaliser un critère d’acceptation observable ;
2. écrire le test automatisé correspondant et constater son échec ;
3. implémenter le minimum nécessaire ;
4. faire passer le test ciblé ;
5. exécuter la suite complète ;
6. exercer le véritable point d’entrée concerné ;
7. documenter séparément les dépendances externes indisponibles ;
8. effectuer une revue de sécurité pour toute fonction de navigation, de secret, de génération ou d’exécution.

Les tests doivent couvrir au minimum :

- le domaine sans LLM ni navigateur réels ;
- les états et versions du cycle de conception ;
- les transitions valides et invalides de tous les états, y compris retrait et archivage ;
- la hiérarchie et les déplacements ;
- les sept types de tests, leur héritage et les incompatibilités ;
- la synthèse factuelle des descriptions ;
- les champs obligatoires, aides, exemples, validations et assistance de la saisie guidée ;
- les attributs simples `requirements` et `business_rules` ;
- les modèles de tests et leurs questions de clarification ;
- le catalogue de phrases d’intention et sa configuration ;
- la validation des fichiers de configuration administrables ;
- les préconditions textuelles, leur confirmation et la résolution codée des dépendances ;
- le blocage des contrôles système échoués ;
- les jeux de données, profils d’environnement et leurs références ;
- la déclaration de sélection CI et le filtrage par déclaration ;
- l’historique strictement limité à la date, la réussite et la durée ;
- les seuils de performance et le type `performance` ;
- la séparation des profils LLM ;
- les contrats d’adaptateurs ;
- les réponses LLM invalides ;
- les politiques de destination ;
- la génération déterministe d’un artefact candidat à partir d’un brouillon structuré ;
- le modèle intermédiaire, la correspondance actions/code, les localisateurs et les assertions (`GEN-001` à `GEN-006`) ;
- les fixtures, Page Objects, personnalisations, conflits de régénération et empreintes (`GEN-007` à `GEN-013`) ;
- les contrôles et limites de l’assistance LLM à la génération (`GEN-014`) ;
- la définition et la validation de profils de charge paramétrés (`LOAD-001` à `LOAD-006`) ;
- l’export, les limites de sécurité, les résultats et l’assistance LLM des tests de charge (`LOAD-007` à `LOAD-011`) ;
- l’invalidation de la validation après toute modification du modèle ou du code ;
- le contrat du bundle ;
- les codes de sortie et rapports du runner ;
- l’exécution E2E sur une cible de démonstration contrôlée ;
- les modèles GitHub Actions et GitLab CI.

## 14. Spécifications détaillées de génération et de charge

Cette section complète les exigences `EF-*` et `ENF-*`. Les identifiants `GEN-*` et `LOAD-*` sont obligatoires pour le suivi de conception, d’implémentation et de validation. Toute tâche de développement doit référencer au moins un identifiant de spécification et un critère d’acceptation associé.

### 14.0 Registre des identifiants

| Famille | Identifiants | Objet | Statut de référence |
|---|---|---|---|
| Exigences fonctionnelles | `EF-001` à `EF-017` | fonctions de conception, génération, validation et exécution | cadrées |
| Exigences non fonctionnelles | `ENF-001` à `ENF-012` | sécurité, isolation, portabilité, observabilité et CI | cadrées |
| Génération | `GEN-001` à `GEN-014` | modèle intermédiaire, traduction, code, personnalisation et empreintes | cadrées ; implémentation à suivre |
| Charge | `LOAD-001` à `LOAD-011` | profils, paramètres, seuils, export et futur adaptateur de charge | définition/export MVP ; exécution post-MVP |
| Acceptation | `ACC-001` à `ACC-046` | vérifications observables du MVP | à transformer en tests |

Une exigence ne peut être marquée comme implémentée que lorsqu’un test ou une démonstration vérifie son comportement. Les statuts de développement (`à faire`, `en cours`, `implémentée`, `vérifiée`) doivent être suivis dans l’outil de gestion du projet, sans modifier l’identifiant stable de la spécification.

### 14.1 Génération du code de test

#### GEN-001 — Entrée de génération

Le générateur reçoit uniquement une version structurée confirmée du test, le modèle de test appliqué, les configurations administratives validées et les versions de générateur déclarées. Il ne reçoit pas directement l’historique brut de conversation.

#### GEN-002 — Modèle intermédiaire normalisé

Avant d’émettre du code, le système transforme la définition métier en un modèle intermédiaire normalisé contenant :

- le contexte et l’environnement ;
- les préconditions et dépendances résolues ;
- les fixtures et données référencées ;
- les actions ordonnées ;
- les assertions observables ;
- les postconditions ;
- les limites de durée et de ressources ;
- les preuves attendues ;
- la politique d’usage du LLM d’exécution.

Le modèle intermédiaire est validé par schéma. Une définition incomplète ou ambiguë reste en conception et ne produit pas d’artefact approuvable.

#### GEN-003 — Pipeline déterministe

La génération suit le pipeline :

```text
définition confirmée
→ modèle intermédiaire validé
→ résolution des composants et fixtures
→ génération des fichiers
→ formatage et contrôles statiques
→ manifeste et empreintes
→ artefact candidat
```

À définition, configuration, version de générateur et données identiques, la génération doit produire le même comportement fonctionnel. Les différences non fonctionnelles doivent être signalées dans le diff de génération.

#### GEN-004 — Correspondance des actions

Le MVP définit un vocabulaire d’actions indépendant de Playwright. Le générateur le traduit notamment en :

| Action métier | Représentation générée attendue |
|---|---|
| ouvrir une page | `page.goto(...)` avec contrôle de destination |
| cliquer sur un élément | localisateur stable puis `.click()` |
| saisir une valeur | localisateur de champ puis `.fill()` |
| sélectionner une option | localisateur puis `.select_option()` |
| attendre un état | attente d’une condition observable, jamais une temporisation arbitraire par défaut |
| vérifier une visibilité | assertion `expect(...).to_be_visible()` |
| vérifier un texte | assertion sur le contenu observable |
| vérifier une URL | assertion sur l’URL autorisée |
| capturer une preuve | capture rattachée à l’étape et à l’exécution |

Une action non supportée doit être signalée comme telle et empêcher l’approbation du code, plutôt que d’être remplacée par une approximation silencieuse.

#### GEN-005 — Choix et stabilité des localisateurs

Le générateur choisit les localisateurs dans l’ordre suivant : rôle et nom accessible, libellé, texte observable, attribut de test configuré, puis sélecteur CSS stable. Il doit conserver le localisateur retenu dans la représentation structurée et indiquer son niveau de fragilité.

Les localisateurs basés sur une position, un identifiant généré, une coordonnée ou une référence temporaire d’exploration sont interdits dans un artefact approuvable, sauf dérogation explicitement justifiée et visible.

#### GEN-006 — Génération des assertions

Chaque résultat attendu confirmé doit devenir au moins une assertion observable, sauf s’il est explicitement marqué comme information non vérifiable. Le générateur doit refuser un test qui ne contient aucune assertion fonctionnelle ou de performance.

Les assertions doivent être indépendantes des messages du LLM. Elles portent sur l’interface, l’URL autorisée, une réponse observable, une donnée affichée, un état ou une mesure déclarée.

#### GEN-007 — Fixtures, données et secrets

Le générateur sépare :

- les fixtures reproductibles non secrètes ;
- les données paramétrables ;
- les références de secrets ;
- les valeurs fournies uniquement par l’environnement d’exécution.

Aucune valeur secrète ne doit être écrite dans le code, le bundle, le manifeste, le prompt, les captures ou les journaux. Une fixture manquante bloque la génération ou l’exécution selon le moment où elle est détectée.

#### GEN-008 — Composants et Page Objects

Un parcours commun peut être factorisé en fixture, fonction ou Page Object uniquement lorsqu’au moins deux tests le réutilisent ou lorsqu’une frontière d’écran claire le justifie. Chaque composant possède un identifiant et une version. Le générateur doit privilégier une structure simple et lisible plutôt qu’une abstraction anticipée.

La modification d’un composant identifie les artefacts candidats et versions approuvées qui doivent être revalidés.

#### GEN-009 — Structure du code généré

Le bundle Playwright Python doit séparer au minimum :

```text
tests/       # scénarios et assertions
pages/       # Page Objects réellement réutilisés
fixtures/    # préparation et nettoyage
config/      # paramètres sans secrets
artifacts/   # sortie d’exécution, jamais source de génération
```

Chaque fichier généré doit indiquer l’identifiant du test et la version de génération, sans inclure le prompt complet ni de secret.

#### GEN-010 — Personnalisation et zones protégées

Le code personnalisé doit être identifiable par des marqueurs ou fichiers explicitement déclarés dans le manifeste. Une régénération doit :

1. détecter les zones personnalisées ;
2. calculer les différences ;
3. préserver automatiquement uniquement les zones dont le contrat n’a pas changé ;
4. produire un conflit visible dans les autres cas ;
5. créer un nouvel artefact candidat.

Aucune personnalisation ne doit être écrasée silencieusement.

#### GEN-011 — Validation de l’artefact

Le générateur produit un manifeste contenant les identifiants, versions, fichiers, dépendances, type de test, tags, déclaration CI, version du générateur et empreintes. Le runner refuse l’artefact si un fichier est absent, modifié, inconnu ou incompatible avec le manifeste.

#### GEN-012 — Contrôles avant approbation

Avant de présenter l’artefact comme candidat, le système exécute :

- validation du schéma intermédiaire ;
- validation des destinations ;
- vérification des secrets référencés sans lecture de leur valeur ;
- contrôle des localisateurs ;
- contrôle des assertions ;
- contrôle des dépendances et fixtures ;
- contrôle des seuils et paramètres ;
- analyse de secrets dans les fichiers générés ;
- formatage et contrôle syntaxique Python.

Un contrôle échoué empêche le lancement individuel et explique l’action corrective attendue.

#### GEN-013 — Versionnement de la génération

L’empreinte d’un artefact inclut le modèle intermédiaire, le code, les composants, les fixtures non secrètes, la configuration effective, la version du générateur et le format du bundle. Toute modification de l’un de ces éléments invalide la validation précédente.

#### GEN-014 — Assistance LLM de génération

Le LLM de conception peut proposer des actions, localisateurs, assertions, fixtures, composants et code initial. Il doit produire des structures soumises au schéma et à la validation humaine. Il ne peut pas approuver un artefact, confirmer un contrôle système ou modifier une version approuvée.

Le LLM d’exécution n’intervient jamais dans la génération normale. Il ne peut être utilisé que pendant une étape adaptative explicitement autorisée par `EF-013`.

### 14.2 Paramétrage des tests de charge

#### LOAD-001 — Type de test de charge

`load` est un type de test distinct de `performance`. Il décrit une charge appliquée à une ou plusieurs opérations autorisées. Le type doit être sélectionnable dans l’interface et disponible dans `config/test-types.yaml`.

#### LOAD-002 — Profil de charge

Un test `load` référence un profil de charge administrable dans `config/load-profiles.yaml`. Un profil possède au minimum :

- un identifiant et un libellé métier ;
- un moteur ou adaptateur de charge ;
- une version de protocole ;
- des opérations autorisées ;
- des limites maximales d’utilisateurs, de débit et de durée ;
- les métriques collectées ;
- les seuils par défaut ;
- les environnements autorisés.

#### LOAD-003 — Paramètres obligatoires

Un test de charge doit pouvoir paramétrer sans YAML :

- le profil de charge ;
- les opérations ou parcours ciblés ;
- le nombre d’utilisateurs virtuels ;
- le débit cible ou la fréquence d’arrivée ;
- la durée de charge ;
- la montée en charge par paliers ;
- le temps de stabilisation ;
- les jeux de données et profils d’environnement ;
- les seuils de réussite.

Les champs affichent leurs unités, limites et exemples. Les valeurs sont contrôlées avant export.

#### LOAD-004 — Modèles de charge

L’administrateur peut configurer les profils suivants ou des profils équivalents :

- charge constante ;
- montée progressive ;
- paliers successifs ;
- pointe courte ;
- endurance ;
- scénario mixte pondéré.

Le modèle sélectionné fournit au LLM de conception les questions nécessaires, mais les paramètres définitifs sont confirmés par l’utilisateur.

#### LOAD-005 — Scénario de charge

Un scénario de charge est une séquence d’opérations autorisées avec une pondération ou une fréquence. Il réutilise les intentions, préconditions, fixtures et profils d’environnement du modèle fonctionnel lorsque cela est possible.

Une opération non autorisée, une destination inconnue ou une dépendance non résolue bloque l’export du profil.

#### LOAD-006 — Seuils et critères de réussite

Un test de charge doit pouvoir définir des seuils sur :

- débit atteint ;
- durée minimale d’exécution ;
- taux d’erreur maximal ;
- temps de réponse moyen ;
- percentile maximal, notamment P95 ou P99 ;
- nombre minimal d’opérations réussies.

Les seuils font partie de la version du test. Un dépassement produit un échec explicite et ne peut pas être transformé en simple avertissement par le LLM.

#### LOAD-007 — Artefact et moteur d’exécution

La conception exporte un profil de charge versionné et un scénario indépendant de l’interface web. Le runner sélectionne un adaptateur compatible avec le profil. Le moteur exact peut être configuré par l’administrateur ; il ne doit pas être imposé aux fonctionnels métier.

Le code Playwright de test fonctionnel ne doit pas être utilisé implicitement pour générer une charge concurrente. Un adaptateur de charge dédié est obligatoire pour l’exécution réelle.

#### LOAD-008 — Sécurité et limites

Un test de charge doit être limité à un environnement explicitement autorisé. Le runner applique des plafonds sur utilisateurs virtuels, débit, durée, volume de données et origines. Les tests de charge sur une production ou une cible non autorisée sont refusés.

Le profil de charge ne contient pas de secret. Les secrets nécessaires sont référencés et injectés uniquement par l’environnement d’exécution.

#### LOAD-009 — Résultats

Le rapport détaillé d’un test de charge contient les métriques et seuils comparés. L’historique synthétique conserve uniquement la date, la réussite et la durée, comme pour les autres tests. Les métriques détaillées sont conservées dans les artefacts de l’exécution selon la politique de conservation.

#### LOAD-010 — Périmètre MVP

Le MVP permet de définir, valider la cohérence, versionner et exporter un test de charge paramétré. L’exécution par un moteur de charge dédié est une capacité activable après le MVP et ne doit pas être présentée comme disponible tant que l’adaptateur correspondant n’est pas installé et vérifié.

#### LOAD-011 — Assistance LLM

Le LLM de conception peut aider à choisir un profil, proposer une charge initiale, identifier les opérations, poser les questions manquantes et suggérer des seuils. Toute valeur proposée doit être confirmée par l’utilisateur. Le LLM ne peut ni lancer une charge ni augmenter les paramètres au-delà des limites administrées.

## 15. Questions ouvertes après le cadrage du MVP

Les points suivants restent à décider pendant les premières tranches TDD :

1. Quel mécanisme d’authentification minimal utilisera l’application web ?
2. Quelle cible de démonstration contrôlée servira de référence E2E ?
3. Quel format précis décrira la hiérarchie et le test structuré dans le bundle ?
4. Comment identifier les zones de code personnalisées à préserver lors d’une régénération ?
5. Quelle profondeur maximale l’interface autorisera-t-elle dans l’arborescence ?
6. Quelle politique de conservation s’appliquera aux captures, conversations et traces ?
7. Quels endpoints LLM seront testés officiellement au MVP ?
8. Quelle implémentation de politique réseau appliquera l’autorisation explicite des origines dans les environnements Docker, Podman et CI ?

## 16. Traçabilité des besoins initiaux

Cette spécification repose sur les besoins explicitement exprimés :

- développer un outillage web ;
- faire interagir l’utilisateur avec un LLM configurable pendant la conception ;
- définir des jeux de tests fonctionnels à partir des indications de l’utilisateur et de captures d’écran ;
- ranger les tests hiérarchiquement ;
- lancer les tests individuellement pendant leur conception ;
- mettre à jour automatiquement une description synthétique et factuelle ;
- générer du code réutilisable, maintenable et personnalisable ;
- exécuter ce code indépendamment de la conception ;
- réserver le LLM d’exécution à des cas exceptionnels ;
- configurer séparément les LLM de conception et d’exécution ;
- faciliter le déploiement et l’intégration à GitHub Actions et GitLab CI.

Les exigences de sécurité, de versionnement, de validation humaine, d’isolation, de portabilité et d’audit sont dérivées de ces besoins afin de rendre la capacité contrôlable et exploitable.
