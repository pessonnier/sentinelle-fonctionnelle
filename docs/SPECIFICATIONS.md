# Spécifications initiales de SentinelleFonctionnelle

- **Statut :** base de cadrage à valider et affiner
- **Projet :** SentinelleFonctionnelle
- **Dépôt :** `pessonnier/sentinelle-fonctionnelle`
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

Il constitue la référence initiale du produit. Chaque comportement devra néanmoins être confirmé progressivement par des critères d’acceptation et des cas de test automatisés.

### 1.1 Référentiel terminologique

Le vocabulaire de ce document est aligné sur l’**ISO/IEC/IEEE 29119-1:2022** pour les concepts généraux, l’**ISO/IEC/IEEE 29119-2:2021** pour les processus de test et l’**ISO/IEC/IEEE 29119-3:2021** pour la documentation de test, ainsi que sur le glossaire ISTQB et le syllabus **ISTQB Foundation Level v4.0.1**. Les versions, liens officiels, conditions d’accès et règles de maintenance sont recensés dans les [références normatives et terminologiques](REFERENCES.md).

Les termes suivants sont normatifs dans cette spécification :

- **plan de test** : document ou objet de gestion qui décrit les objectifs de test, le périmètre, les ressources, l’approche, les contraintes, les risques, les critères d’entrée et de sortie, ainsi que l’ordonnancement prévu ; un plan de test n’est pas lui-même une unité exécutable ;
- **base de test** : ensemble des connaissances et sources utilisées comme fondement de l’analyse et de la conception des tests ;
- **condition de test** : aspect testable d’un composant ou d’un système identifié comme fondement des tests ;
- **type de test** : groupe d’activités de test visant des caractéristiques de qualité ou des objectifs de test déterminés ;
- **suite de tests** : ensemble de cas de test ou de procédures de test assemblés en vue d’une exécution déterminée ; une suite peut contenir des sous-suites ;
- **cas de test** : ensemble de préconditions, de données d’entrée, d’actions, de résultats attendus et, le cas échéant, de postconditions, élaboré pour un objectif ou une condition de test déterminés ;
- **procédure de test** : séquence ordonnée de cas de test et des actions nécessaires à leur exécution ;
- **script de test** : suite d’instructions, manuelles ou automatisées, qui met en œuvre une procédure ou un cas de test ;
- **données de test** : données nécessaires à l’exécution des cas de test ;
- **exécution de test** : activité consistant à exécuter une suite, une procédure ou un cas de test sur une version déterminée de l’objet de test ;
- **résultat de test** : conséquence ou résultat observé d’une exécution, comparé au résultat attendu ;
- **objet de test** : composant ou système soumis aux activités de test.

Le mot **test**, employé seul, désigne l’activité générale de test ou qualifie un concept consacré, comme « type de test » ou « environnement de test ». Il ne désigne jamais l’unité élémentaire spécifiée par l’utilisateur, appelée exclusivement **cas de test**. Le terme ambigu **jeu de tests** n’est pas utilisé : il ne faut le confondre ni avec une suite de tests ni avec un jeu de données de test. Le terme **campagne de test**, non nécessaire au MVP et susceptible de recevoir des définitions différentes selon les organisations, n’est pas introduit.

Cet alignement terminologique ne constitue pas, à lui seul, une déclaration de conformité intégrale à l’ISO/IEC/IEEE 29119. Une telle déclaration exigerait une évaluation séparée des processus, des documents produits et des preuves d’application.

## 2. Vision du produit

SentinelleFonctionnelle est un outillage web qui aide un utilisateur à élaborer des plans, suites et cas de test fonctionnels à partir :

- d’indications exprimées en langage naturel ;
- de captures d’écran d’une application web ;
- de l’observation contrôlée de l’interface cible ;
- d’un dialogue avec un LLM de conception configurable.

Le résultat attendu est une bibliothèque hiérarchisée de cas de test fonctionnels décrits, versionnés et matérialisés par des scripts de test :

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

Le nom officiel du projet est **SentinelleFonctionnelle**.

Sa responsabilité est d’assister la conception, la génération, la validation et l’exécution de cas de test fonctionnels d’interfaces web.

### 3.1.1 Deux modes de déploiement, un seul produit

SentinelleFonctionnelle fournit les mêmes capacités fonctionnelles dans deux modes :

- **local** : application web exécutée sur le poste de l’utilisateur, avec une identité locale implicite et une persistance locale ;
- **online** : application web partagée, multi-utilisateur et multi-projet, avec authentification obligatoire et persistance partagée.

Le mode de déploiement ne doit pas créer deux variantes du domaine, des cas de test ou des bundles. Les mêmes cas d’usage, validations, formats d’export et règles de sécurité sont utilisés. Seuls les adaptateurs d’identité, de persistance, de stockage d’artefacts et la configuration de déploiement diffèrent.

Le mode local ne doit pas désactiver une fonctionnalité disponible en ligne. Une fonction nécessitant intrinsèquement un service partagé doit fournir un comportement local équivalent ou signaler explicitement la dépendance externe, sans altérer les données métier.

### 3.2 Deux phases explicitement séparées

Le produit sépare la **phase de conception** de la **phase d’exécution**. Elles n’ont ni les mêmes objectifs, ni les mêmes dépendances, ni les mêmes profils LLM.

#### Phase de conception

La conception est interactive. Elle sert à transformer une intention métier en un cas de test compréhensible et exécutable.

Pendant cette phase :

1. l’utilisateur dialogue avec un LLM de conception ;
2. il fournit des objectifs, contraintes, données et captures d’écran ;
3. le système maintient une représentation structurée du cas de test ;
4. la description du cas de test est remise à jour après chaque modification acceptée ;
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
5. il ne modifie jamais silencieusement le cas de test ou le script approuvé.

Le code exécuté peut être :

- entièrement généré par SentinelleFonctionnelle ;
- généré puis personnalisé par un développeur ;
- écrit manuellement mais enregistré et exécuté dans le même format de projet.

L’exécution normale ne dépend pas d’un LLM. Un LLM d’exécution peut intervenir uniquement dans un cas exceptionnel, explicitement déclaré par le cas de test, par exemple lorsqu’un élément ne peut pas être identifié de façon déterministe. Cette intervention doit être bornée, traçable et incapable d’élargir le périmètre du cas de test.

### 3.3 Profils LLM distincts

Le **LLM de conception** et le **LLM d’exécution** sont deux configurations indépendantes.

| Aspect | LLM de conception | LLM d’exécution |
|---|---|---|
| Finalité | Dialogue, clarification, synthèse, proposition d’étapes et génération de code | Résolution exceptionnelle d’une ambiguïté pendant un cas de test autorisé |
| Usage | Fréquent pendant l’édition | Désactivé par défaut |
| Interaction humaine | Oui | Non dans une CI |
| Tolérance à la latence | Interactive | Faible et bornée par un délai maximal |
| Permissions | Accès au contexte de conception nécessaire | Accès minimal à l’étape et à l’observation courantes |
| Sortie | Proposition soumise à validation | Réponse structurée limitée à une décision autorisée |
| Échec | La conception reste éditable | Le cas de test échoue ou suit une stratégie de repli explicite |
| Budget | Configurable par session ou projet | Configurable par cas de test et plafonné |

Les deux profils doivent pouvoir utiliser des fournisseurs, endpoints, modèles, paramètres et secrets différents. L’absence de profil d’exécution ne doit jamais empêcher l’exécution des cas de test déterministes.

### 3.4 Organisation hiérarchique

Les cas de test doivent pouvoir être rangés sous forme d’arbre afin de rester lisibles lorsque leur nombre augmente.

La hiérarchie minimale est :

```text
Projet
└── Plan de test
    ├── Suite de tests ou dossier
    │   ├── Cas de test
    │   │   ├── Étapes de test
    │   │   ├── Données de test
    │   │   └── Résultats attendus
    │   └── Cas de test
    └── Suite de tests ou dossier
```

Les étapes, données et résultats attendus sont des sections structurées du cas de test et non des nœuds déplaçables de l’arbre. Une suite, un dossier de classement ou un cas de test possède un nom, un ordre d’affichage et un parent compatible avec sa nature. Le déplacement d’un nœud ne doit pas changer l’identité ni l’historique du cas de test.

Les relations autorisées sont explicites :

| Parent | Enfants autorisés |
|---|---|
| Projet | plans de test |
| Plan de test | suites de tests et dossiers de classement |
| Suite de tests | cas de test, sous-suites et sous-dossiers |
| Dossier de classement | cas de test, suites de tests et sous-dossiers |
| Cas de test | aucun nœud hiérarchique |

Un cas de test ne peut jamais être créé directement sous un plan de test. Il doit appartenir à une suite de tests ou à un dossier de classement. Les sous-suites et sous-dossiers sont facultatifs ; le chemin minimal reste `Projet → Plan de test → Suite ou dossier → Cas de test`.

Un dossier de classement est uniquement une commodité de navigation de l’outil. Il ne constitue ni un plan de test, ni une suite de tests, ni une unité exécutable.

### 3.4.1 Plans de test, suites de tests et cas de test

Un **plan de test** formalise les objectifs, le périmètre, les risques, l’approche, les ressources, les contraintes, les critères d’entrée et de sortie, la cible, les environnements et l’ordonnancement prévisionnel des activités de test. Il référence une ou plusieurs suites de tests, mais n’est pas lui-même exécuté.

Une **suite de tests** regroupe des cas de test ou des sous-suites destinés à être exécutés ensemble. Elle est distincte d’un dossier de classement et possède une finalité, une sélection, un ordre d’exécution et, le cas échéant, des préconditions et postconditions communes. La résolution de son ordre et de ses dépendances produit la procédure de test utilisée pour une exécution donnée.

Un **cas de test** possède un objectif, des préconditions, des données d’entrée, des actions, des résultats attendus et, le cas échéant, des postconditions. Son script de test automatisé constitue un artefact dérivé et versionné ; il ne remplace pas la spécification structurée du cas de test.

Un plan de test doit pouvoir être versionné et exporté indépendamment des autres plans du projet. Une suite de tests ou un cas de test doit pouvoir être sélectionné, validé et exécuté indépendamment lorsque ses dépendances le permettent. L’historique porte sur les exécutions de suites et de cas de test, jamais sur une prétendue exécution du plan de test.

### 3.4.2 Types de test

Le type d’un cas de test est choisi dans une liste administrable. Une suite de tests peut définir un type de test par défaut pour ses cas descendants. Le MVP fournit au minimum :

- `smoke` : vérification rapide de disponibilité ;
- `sanity` : vérification ciblée après une modification ;
- `acceptance` : validation d’un comportement métier ;
- `regression` : vérification de comportements existants ;
- `e2e` : parcours complet de bout en bout ;
- `performance` : vérification de durées, seuils et budgets sur un parcours fonctionnel ;
- `load` : simulation paramétrée d’une charge sur une ou plusieurs opérations autorisées.

Le type `performance` ne désigne pas un test de charge ou de montée en charge. Le type `load` permet de paramétrer ces cas de test, mais leur exécution avec un moteur de charge dédié reste hors du périmètre d’exécution du MVP. Le MVP doit néanmoins pouvoir définir, valider la cohérence et exporter un profil de charge. Un cas de test `performance` doit déclarer les actions mesurées, les seuils attendus et les conditions de mesure.

Le type de la suite de tests sert de valeur par défaut pour ses cas de test descendants. Un cas de test peut déclarer un type différent lorsqu’il est compatible avec la suite ; ce type explicite prévaut alors. Une incompatibilité est signalée à la saisie et bloque l’export jusqu’à correction.

### 3.4.3 Cycle de vie

Un cas de test suit un cycle explicite :

```text
brouillon → en_conception → candidat → validé_individuellement → approuvé → actif → retiré → archivé
```

Les transitions autorisées sont : `brouillon → en_conception`, `en_conception → candidat`, `candidat → validé_individuellement`, `validé_individuellement → approuvé`, `approuvé → actif`, `actif → retiré` et `retiré → archivé`. Une modification d’un cas de test approuvé ou actif crée un nouveau brouillon. Les retours en arrière implicites et les transitions qui sautent une validation sont refusés.

Un cas de test en brouillon, en conception, candidat ou retiré n’est pas sélectionnable par une CI. Un cas de test candidat peut être lancé individuellement. Un cas de test actif est autorisé dans les suites de tests automatisées. Les transitions sont enregistrées dans un journal d’audit distinct de l’historique synthétique des résultats.

Les transitions et leurs conditions doivent être visibles dans l’interface. L’utilisateur ne doit pas avoir à connaître les valeurs internes pour comprendre ce qui lui reste à faire.

### 3.5 Description synthétique et factuelle

Chaque cas de test possède une description courte destinée à la navigation, à la revue et aux rapports.

Lorsqu’un cas de test est édité par la conversation ou par le formulaire structuré :

1. le système recalcule une proposition de description à partir de l’état courant validé du cas de test ;
2. la description exprime uniquement l’objectif, les préconditions déterminantes et le résultat vérifié ;
3. elle exclut les hésitations, justifications du LLM, détails d’implémentation et informations non confirmées ;
4. elle reste synthétique, factuelle et compréhensible hors du contexte de la conversation ;
5. l’utilisateur peut la corriger avant validation ;
6. sa version est enregistrée avec la version du cas de test.

La conversation n’est pas la source de vérité. La représentation structurée du cas de test et sa version approuvée le sont.

### 3.5.1 Saisie guidée et assistance

Les fonctionnels métier ne doivent pas avoir à écrire du YAML ou du code pour définir un cas de test. La saisie principale se fait par formulaire guidé, choix de listes, texte libre et conversation. Le YAML et les autres formats structurés sont des formats d’administration, d’export et d’intégration, pas des formats de saisie attendus des utilisateurs métier.

Tous les champs affichés doivent être documentés dans l’interface avec un libellé, une aide courte, un exemple, un indicateur obligatoire/facultatif, une règle de validation et l’origine de la valeur : utilisateur, configuration ou proposition du LLM.

| Champ métier | Obligatoire | Saisie et exemple | Validation | Assistance LLM |
|---|---:|---|---|---|
| Nom du projet | oui | texte court, ex. « Portail citoyen » | non vide, longueur limitée | aucune |
| Description du projet | non | texte libre | longueur limitée | reformulation facultative |
| Cible web du projet | oui | URL HTTPS | destination autorisée | aucune |
| Politique de sécurité du projet | oui | choix administré | politique existante | aucune |
| Nom du plan de test | oui | texte court, ex. « Validation de la commande » | non vide, longueur limitée | suggestion facultative |
| Objectifs et périmètre du plan | oui | texte libre décrivant ce qui est testé et ce qui est exclu | non vide | reformulation et questions de périmètre |
| Approche de test du plan | oui | niveaux, types, techniques et priorités | valeurs administrées ou description validée | proposition justifiée |
| Risques, critères d’entrée et critères de sortie | oui | listes structurées | au moins un critère de sortie mesurable | proposition soumise à confirmation |
| Ressources, contraintes et ordonnancement du plan | non | textes courts ou listes | valeurs cohérentes | proposition facultative |
| Nom de la suite de tests | oui | texte court, ex. « Parcours nominal de commande » | non vide, unique dans son parent | suggestion facultative |
| Objectif d’exécution de la suite | oui | texte décrivant la finalité de l’exécution groupée | non vide | reformulation facultative |
| Préconditions et postconditions communes de la suite | non | listes structurées | dépendances cohérentes | proposition facultative |
| Type et déclaration CI par défaut de la suite | non | listes administrées | valeurs autorisées | suggestion justifiée |
| Nom du dossier de classement | oui pour un dossier | texte court | non vide, unique dans son parent | suggestion facultative |
| Nom du cas de test | oui | texte court | non vide, unique dans son parent | suggestion à partir de l’objectif |
| Type de test | oui | liste administrable | valeur configurée | suggestion justifiée |
| Modèle de cas de test | non | liste administrable | modèle disponible | sélection selon l’objectif |
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

#### 3.5.1.1 Cheminement dans les formulaires

L’interface respecte le même ordre que le modèle métier :

1. la page d’accueil permet de créer ou ouvrir un **projet** ;
2. la page du projet liste ses **plans de test** et fournit un formulaire de plan distinct couvrant son objectif, son périmètre, son approche, sa cible, ses risques, ses critères, ses ressources, ses contraintes et son ordonnancement ;
3. la page du plan affiche l’arborescence et deux actions distinctes : créer une **suite ou un dossier**, puis créer un **cas de test** sous l’un de ces parents ;
4. la page du cas de test sépare visuellement le contexte, les **étapes de test**, les **données de test** et les **résultats attendus** ;
5. un fil d’Ariane rappelle en permanence `Projet / Plan / Suite ou dossier / Cas` et permet de revenir au niveau précédent sans perdre les données enregistrées.

Le formulaire de création d’un cas exige la sélection d’une suite ou d’un dossier parent. Tant qu’aucun parent compatible n’existe, l’action de création du cas est indisponible et l’interface indique l’étape préalable. Chaque formulaire conserve les valeurs invalides lors de l’affichage d’une erreur, associe le message au champ concerné et ne crée aucun objet partiel.

L’éditeur du cas de test présente les quatre sections dans un ordre stable. Les données de test restent facultatives, mais leur section est toujours visible. Pour le mode pas-à-pas, chaque étape possède exactement un résultat attendu placé au même rang ; un nombre différent d’étapes et de résultats bloque l’enregistrement.

### 3.5.2 Configuration administrable

Les administrateurs de l’outillage peuvent adapter le vocabulaire et les guides sans modifier le code de l’application. Les fichiers de configuration peuvent définir :

- les types de test disponibles ;
- les modèles de cas de test ;
- les phrases décrivant les intentions fonctionnelles ;
- les valeurs de tags autorisées ;
- les environnements et profils de données disponibles ;
- les profils LLM de conception et d’exécution ;
- les cibles GitLab d’entreprise autorisées pour la publication manuelle ;
- les aides, exemples et champs obligatoires par contexte.

Chaque entrée de configuration possède un identifiant stable, un libellé visible, une description destinée au métier et, lorsque nécessaire, une représentation technique non visible dans le formulaire.

Le MVP prévoit au minimum les fichiers administrables suivants :

```text
config/test-types.yaml          # types de test, libellés et aides
config/test-models.yaml         # modèles de cas de test et questions LLM
config/test-intents.yaml         # phrases d’intention fonctionnelle
config/tags.yaml                 # tags sélectionnables
config/environments.yaml         # environnements, URLs et origines autorisées
config/data-profiles.yaml        # profils de données et fixtures
config/load-profiles.yaml        # profils de charge paramétrés
config/llm-profiles.yaml         # fournisseurs, endpoints, modèles et paramètres LLM
config/git-targets.yaml          # instances et dépôts GitLab autorisés
```

Un modèle de cas de test peut par exemple déclarer :

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

Des profils LLM peuvent par exemple déclarer :

```yaml
profiles:
  - id: design-openai
    label: OpenAI - conception
    usage: design
    provider: openai
    protocol: responses
    endpoint: https://api.openai.com/v1
    model: configured-openai-model
    auth:
      strategy: api_key
      secret_ref: openai-design
    capabilities: [text, images, structured_output]
    parameters:
      max_output_tokens: 4096
    timeouts:
      connect_seconds: 10
      response_seconds: 120

  - id: design-ollama
    label: Ollama local - conception
    usage: design
    provider: ollama
    protocol: native
    endpoint: http://ollama:11434
    model: configured-ollama-model
    auth:
      strategy: none
    capabilities: [text, structured_output]
    parameters:
      max_output_tokens: 4096

  - id: design-mistral
    label: Mistral - conception
    usage: design
    provider: mistral
    protocol: chat_completions
    endpoint: https://api.mistral.ai/v1
    model: configured-mistral-model
    auth:
      strategy: api_key
      secret_ref: mistral-design
    capabilities: [text, structured_output]
    parameters:
      max_output_tokens: 4096
```

Les identifiants de modèles sont des exemples fictifs à remplacer par des modèles disponibles. Chaque entrée est validée par le schéma de son fournisseur avant activation.

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

Une cible GitLab d’entreprise peut par exemple déclarer :

```yaml
id: enterprise-quality
label: GitLab entreprise - Qualité
base_url: https://gitlab.example.internal
project: quality/web-functional-tests
default_branch: main
publication:
  mode: merge_request
  branch_prefix: sentinel/
  destination_path: sentinelle-bundle/
auth:
  secret_ref: gitlab-enterprise-publisher
tls:
  ca_bundle_ref: enterprise-ca
timeouts:
  connect_seconds: 10
  request_seconds: 30
```

Les valeurs `secret_ref` et `ca_bundle_ref` sont des références résolues par l’application et ne contiennent ni jeton ni certificat privé dans le fichier de configuration.

Le système doit vérifier la configuration au démarrage et signaler les identifiants en doublon, références inconnues ou champs incohérents.

### 3.6 Modèle d’exploration en conception

L’exploration d’une interface suit la boucle :

1. **Observer** : charger la page, collecter une représentation du DOM et une capture d’écran ;
2. **Raisonner** : interpréter l’état courant au regard du scénario en cours de conception ;
3. **Agir** : cliquer, saisir une valeur, naviguer ou attendre un changement autorisé ;
4. **Vérifier** : contrôler les résultats attendus et conserver les preuves utiles ;
5. **Itérer** jusqu’à la fin du scénario ou jusqu’à un blocage explicite.

Cette exploration aide à concevoir et valider le cas de test. Elle ne constitue pas à elle seule une preuve que le script final s’exécute correctement.

### 3.7 Méthode de développement

Le produit doit être développé en TDD :

1. écrire un cas de test automatisé en échec pour un comportement observable ;
2. vérifier que l’échec correspond au comportement manquant ;
3. ajouter l’implémentation minimale ;
4. exécuter le cas de test ciblé ;
5. exécuter toute la suite de tests ;
6. refactoriser uniquement lorsque tous les cas de test réussissent.

## 4. Utilisateurs visés

### 4.1 Testeur fonctionnel ou responsable QA

Il décrit les parcours métier, fournit des exemples visuels, organise les cas de test, examine les scénarios proposés et valide chaque cas de test sans devoir écrire l’intégralité du script.

### 4.2 Développeur

Il récupère du code versionnable et compréhensible. Il peut le personnaliser sans dépendre du LLM, l’exécuter localement et l’intégrer à la CI du dépôt cible.

### 4.3 Responsable produit

Il exprime un comportement attendu sous forme de parcours et de critères d’acceptation, puis vérifie que le cas de test approuvé correspond au besoin métier.

### 4.4 Responsable de plateforme ou DevOps

Il déploie l’outil, configure les secrets, fournit les runners et intègre les suites de tests à GitHub Actions, GitLab CI ou une autre chaîne d’intégration.

## 5. Parcours nominaux

### 5.1 Concevoir et valider un cas de test

1. L’utilisateur crée ou ouvre un projet.
2. Il crée ou ouvre un plan de test, puis une suite de tests dans l’arborescence.
3. Il crée un cas de test et renseigne l’URL ou l’environnement cible.
4. Il sélectionne un profil LLM de conception.
5. Il décrit l’objectif métier et ajoute éventuellement des captures d’écran.
6. Le LLM pose les questions nécessaires pour lever les ambiguïtés.
7. Le système met à jour la représentation structurée et la description synthétique.
8. L’utilisateur examine puis corrige les préconditions, étapes, données et résultats attendus.
9. Le générateur produit un artefact candidat Playwright et calcule son empreinte.
10. L’utilisateur lance individuellement cet artefact candidat en mode validation.
11. Le runner isolé exécute exactement le code candidat et conserve les preuves.
12. L’utilisateur corrige le cas de test ou personnalise le script si nécessaire, ce qui invalide la validation précédente, puis le relance.
13. Il approuve une version immuable liant le cas de test structuré, le script validé et son empreinte.

### 5.2 Exécuter une suite dans une CI

1. La CI récupère le dépôt ou le paquet de suites et cas de test approuvés.
2. Elle fournit la configuration de cible et les secrets par variables ou fichiers protégés.
3. Elle lance le runner par une commande ou une image conteneur versionnée.
4. Le runner sélectionne une suite de tests, un tag ou un cas de test ; un dossier de classement ne constitue pas une cible d’exécution.
5. Il exécute le code sans appeler le service web de conception.
6. Il utilise le profil LLM d’exécution uniquement si un cas de test l’autorise explicitement.
7. Il publie un code de sortie standard, un rapport JUnit et les artefacts configurés.
8. GitHub Actions, GitLab CI ou l’autre orchestrateur décide du succès du pipeline à partir du code de sortie.

## 6. Exigences fonctionnelles

### 6.1 Conception et organisation des plans, suites et cas de test

Cette partie décrit les fonctions utilisées par les fonctionnels métier pour définir, comprendre, organiser et valider des plans, suites et cas de test. Elle ne lance pas directement les scripts dans le processus de l’application de conception.

### EF-001 — Gestion des projets

Le système doit permettre de créer, consulter, modifier et archiver un projet contenant au minimum un nom, une description, une cible web et une politique de sécurité. Un projet peut contenir plusieurs plans de test indépendants.

Un plan de test doit contenir au minimum :

- un nom, des objectifs et un périmètre explicite ;
- une base de test et les éléments de l’objet de test concernés ;
- une approche de test comprenant les niveaux, types, techniques et priorités retenus ;
- les risques produit et projet pris en compte ;
- les rôles, responsabilités, ressources et contraintes ;
- les critères d’entrée et de sortie ;
- les exigences relatives aux données et environnements de test ;
- un calendrier ou un ordonnancement prévisionnel ;
- une ou plusieurs suites de tests.

Une suite de tests doit contenir au minimum un nom, un objectif d’exécution, une sélection ordonnée de cas de test ou de sous-suites et ses éventuelles préconditions communes. Cet ordre permet de produire une procédure de test exécutable. Le type de test et la déclaration d’exécution définis sur une suite servent de valeurs par défaut à ses cas de test descendants.

### EF-001.1 — Utilisateurs, appartenances et isolation des projets

Le système doit permettre à une même instance en ligne de servir plusieurs utilisateurs et plusieurs projets. Toute action sur un projet est évaluée avec une identité applicative et une appartenance explicite au projet.

Le socle minimal distingue les rôles :

- `owner` : administration du projet et de ses membres ;
- `editor` : conception et modification des plans, suites et cas de test ;
- `viewer` : consultation sans modification.

Un utilisateur ne doit ni voir, ni déduire, ni modifier un projet auquel il n’appartient pas. Les identifiants fournis par le client ne constituent jamais une autorisation. Les recherches, listes, journaux, captures, artefacts et exports doivent appliquer la même isolation.

En mode local, l’application crée ou résout une identité locale implicite possédant le rôle `owner` sur les projets qu’elle crée. Cette simplification d’authentification ne modifie pas les règles métier ni le format des projets.

### EF-001.2 — Interface web locale et configuration de démarrage

Le mode local expose les cas d’usage de projet et d’arborescence dans une interface
web servie par le même paquet applicatif. L’utilisateur doit pouvoir, sans écrire de
code ni de YAML :

- créer et retrouver plusieurs projets ;
- créer plusieurs plans de test dans un projet ;
- créer des suites de tests, sous-suites, dossiers de classement et cas de test ;
- renommer, déplacer, ordonner et archiver les nœuds ;
- redémarrer l’application sans perdre ces données.

Le point d’entrée local doit fournir une sonde de santé, lier l’interface à l’adresse
de boucle locale par défaut et permettre de choisir explicitement le fichier SQLite,
l’adresse et le port. Une demande de démarrage en mode `online` doit être refusée
tant que l’adaptateur d’authentification et la persistance partagée ne sont pas
composés ; le serveur ne doit jamais transformer silencieusement ce mode en accès
local implicite.

### EF-002 — Arborescence des suites et cas de test

Le système doit permettre de :

- créer, renommer, déplacer, ordonner et archiver des suites de tests, sous-suites, dossiers de classement et cas de test ;
- afficher l’arborescence sans charger toutes les preuves d’exécution ;
- conserver l’identité et l’historique d’un cas de test déplacé ;
- sélectionner une suite ou un cas de test pour exécuter le cas sélectionné ou tous les cas descendants ;
- filtrer les cas de test par nom, tag, état de validation ou résultat récent.

La suppression d’un nœud contenant des descendants doit exiger une confirmation et appliquer une politique explicite d’archivage ou de suppression.

L’organisation transversale complémentaire repose sur des **tags**. Aucun mécanisme parallèle de catégories libres ne doit être introduit pour remplacer les tags. Les types de test, `requirements`, `business_rules`, profils d’environnement et déclarations d’exécution restent des attributs dédiés parce qu’ils ont une signification opérationnelle.

Les tags doivent pouvoir être ajoutés, retirés et filtrés depuis l’interface par sélection dans une liste administrée. Un utilisateur métier ne doit pas avoir à connaître le fichier qui les définit.

### EF-002.1 — Navigation et formulaires hiérarchiques

L’interface web doit fournir des pages distinctes pour le catalogue des projets, le détail d’un projet, le détail d’un plan de test et l’éditeur d’un cas de test. Une URL stable identifie chaque projet, plan et cas ; un rechargement ou un redémarrage doit restaurer le même contexte.

La page d’un projet ne mélange pas l’édition détaillée des cas avec la création des plans. La page d’un plan affiche ses suites, dossiers et cas dans l’ordre hiérarchique, différencie visuellement leurs natures et interdit à l’interface de proposer un cas sans parent compatible. La page d’un cas affiche séparément :

- son contexte, son objectif, son acteur, ses préconditions et postconditions ;
- ses étapes ordonnées ;
- ses données référencées ou importées ;
- ses résultats attendus, alignés avec les étapes lorsque le mode le permet.

La navigation arrière, le fil d’Ariane et les liens de l’arbre doivent conserver les identifiants métier plutôt que reconstruire le contexte à partir des noms. Les commandes de renommage, déplacement et archivage restent disponibles au niveau du plan sans encombrer le formulaire principal du cas.

### EF-003 — Configuration des LLM

Le système doit proposer deux types de profils :

- **profil de conception** ;
- **profil d’exécution**.

Un administrateur doit pouvoir créer, consulter, dupliquer, modifier, désactiver et tester un profil LLM sans modifier le code de l’application. Les profils peuvent être chargés depuis la configuration administrable et, en mode en ligne, gérés depuis l’interface d’administration. Une modification crée une nouvelle version du profil ; elle ne modifie pas silencieusement la configuration référencée par une version de cas de test approuvée.

Chaque profil doit définir indépendamment :

- un identifiant stable, un libellé, un état actif ou désactivé et un type d’usage autorisé ;
- le fournisseur et la version du protocole utilisé ;
- l’URL de service et, si nécessaire, les paramètres de proxy et d’autorité de certification ;
- le modèle, sans imposer un modèle global à tous les profils ;
- les capacités nécessaires : texte, images, sortie structurée et outils autorisés ;
- les paramètres d’inférence pris en charge par le fournisseur, notamment la limite de sortie, la température ou l’effort de raisonnement lorsqu’ils existent ;
- les délais de connexion et de réponse, le nombre de tentatives, les limites de consommation et le budget ;
- la stratégie d’authentification et une référence vers un secret lorsqu’il est requis, sans exposer sa valeur dans l’interface, les prompts, les exports ou les journaux ;
- les en-têtes additionnels non secrets explicitement autorisés.

Le système doit appliquer un schéma propre au fournisseur : un paramètre non pris en charge est refusé avec un message explicite, et non ignoré silencieusement. La configuration effective, l’identifiant du profil et sa version doivent être traçables pour chaque appel sans journaliser de secret.

La connectivité de chaque profil doit être vérifiable séparément avant son activation. Le contrôle vérifie au minimum l’accès à l’endpoint, l’authentification lorsqu’elle est requise, la disponibilité du modèle et la compatibilité des capacités déclarées. Il retourne un résultat structuré et compréhensible sans envoyer de contenu métier ni persister de secret. Une configuration valide de conception n’implique pas une configuration valide d’exécution, et inversement.

### EF-003.1 — Fournisseurs LLM obligatoires

Le MVP doit fournir et maintenir trois adaptateurs configurables :

- **OpenAI** : endpoint API configurable, protocole OpenAI pris en charge, modèle configurable, référence de clé API et identifiants de projet ou d’organisation facultatifs ;
- **Ollama** : endpoint local ou distant configurable, modèle configurable, absence d’authentification autorisée sur un réseau explicitement approuvé et authentification facultative lorsqu’un proxy la fournit ;
- **Mistral** : endpoint API configurable, protocole Mistral pris en charge, modèle configurable et référence de clé API.

Aucun de ces fournisseurs ne doit être codé comme fournisseur unique ou implicite. Un projet peut sélectionner un profil OpenAI, Ollama ou Mistral pour la conception, et un autre profil compatible pour l’exécution exceptionnelle. L’ajout ultérieur d’un fournisseur doit se faire par un nouvel adaptateur respectant le même port applicatif, sans modifier le domaine métier.

Le système doit distinguer la disponibilité du fournisseur de la compatibilité du modèle choisi. Si un modèle ne prend pas en charge les images, les sorties structurées ou une autre capacité requise par le parcours, le profil ne peut pas être activé pour cet usage et l’interface indique la capacité manquante.

### EF-003.2 — Documentation des connexions LLM

Chaque adaptateur LLM déclaré comme pris en charge doit posséder une procédure de connexion versionnée avec l’application. Le MVP fournit au minimum :

```text
docs/llm/openai.md
docs/llm/ollama.md
docs/llm/mistral.md
```

Chaque procédure contient :

- les prérequis de compte, d’installation ou d’accès réseau ;
- la création et le stockage de l’éventuel secret sans afficher sa valeur ;
- les endpoints et protocoles pris en charge, avec un lien daté vers la documentation officielle du fournisseur ;
- un exemple de profil complet utilisant des valeurs fictives et une référence de secret ;
- les paramètres configurables et leurs valeurs par défaut dans SentinelleFonctionnelle ;
- la configuration TLS, proxy et réseau, y compris le cas local d’Ollama ;
- la sélection du modèle et la vérification des capacités nécessaires ;
- la procédure de test de connectivité depuis l’interface et, lorsqu’elle existe, depuis la CLI ;
- les erreurs courantes d’authentification, de modèle, de quota, de délai ou de réseau et leur diagnostic ;
- la rotation ou révocation des secrets et la désactivation du profil.

Une procédure ne doit contenir aucun secret réel. Un fournisseur ne peut pas être annoncé comme pris en charge si sa procédure est absente, si ses exemples ne respectent pas le schéma courant ou si le contrôle documentaire automatisé échoue.

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

Après chaque échange accepté ou modification structurée d’un cas de test, le système doit proposer une nouvelle description synthétique et factuelle.

La mise à jour doit :

- reposer sur la version structurée courante plutôt que sur le seul dernier message ;
- préserver les faits confirmés ;
- retirer les éléments devenus faux ou obsolètes ;
- éviter les formulations spéculatives ;
- être visible avant l’enregistrement de la nouvelle version ;
- rester modifiable par l’utilisateur.

### EF-006 — Gestion des captures d’écran

L’utilisateur doit pouvoir joindre des captures à un projet, un plan de test, une suite de tests, un cas de test ou une étape de test.

Chaque capture doit pouvoir recevoir :

- un libellé ;
- une description ;
- l’état du parcours auquel elle correspond ;
- des annotations ou zones d’intérêt ;
- une date et une provenance.

Le système doit conserver le lien entre une capture, l’étape dérivée et la version du cas de test.

Les captures d’écran restent facultatives. Leur absence ne doit pas empêcher la définition, la génération, la validation, l’approbation ou l’export d’un cas de test lorsque les informations textuelles et structurées sont suffisantes.

### EF-007 — Spécification structurée du cas de test

Le système doit transformer le dialogue en une représentation structurée contenant au minimum :

- un identifiant stable ;
- un titre et une description synthétique ;
- le plan de test, la suite de tests et le chemin hiérarchique ;
- le type de test ;
- les attributs `requirements` et `business_rules` ;
- les préconditions ;
- les données de test ;
- une séquence ordonnée d’actions ;
- un résultat attendu par étape lorsque pertinent ;
- les postconditions ;
- les tags ;
- les hypothèses et ambiguïtés restantes ;
- la déclaration d’exécution CI ;
- les seuils et mesures attendus pour un cas de test de type `performance` ;
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

Un cas de test peut référencer plusieurs jeux de données de test et profils d’environnement sans contenir de secret. L’utilisateur les sélectionne par des libellés métier et non par un chemin de fichier.

L’application doit permettre de :

- choisir un jeu de données de test existant ;
- demander au LLM de proposer les données manquantes ;
- déclarer une donnée comme sensible sans afficher sa valeur ;
- sélectionner un environnement autorisé ;
- vérifier que les préconditions et dépendances peuvent être satisfaites ;
- produire dans le bundle les fixtures non secrètes et leurs identifiants.

Les administrateurs définissent les profils techniques, les sources et les règles de substitution dans la configuration. Un environnement possède un identifiant, un libellé, une URL cible, des origines autorisées et des références de secrets. Un profil de données possède un identifiant, un libellé, une source de fixtures et des règles de préparation/nettoyage. L’utilisateur métier ne voit que les champs et libellés nécessaires à son choix.

### EF-007.3 — Modèles de cas de test

L’application doit proposer une liste de modèles de cas de test configurable par les administrateurs. Chaque modèle fournit un nom, une description métier, un type par défaut, des champs obligatoires et une liste de questions de clarification.

Le LLM de conception peut utiliser le modèle sélectionné pour poser les questions pertinentes et ne doit pas demander les informations déjà renseignées. L’utilisateur peut changer de modèle avant validation, avec affichage des champs qui seront ajoutés ou perdus.

### EF-007.4 — Modes de spécification et vues d’organisation

Un utilisateur métier peut choisir plusieurs modes de saisie sans écrire de
YAML. Le MVP propose au minimum :

- **pas-à-pas** : une action et son résultat observable par ligne ;
- **Given/When/Then** : préconditions, événement et résultat exprimés avec un
  vocabulaire BDD ;
- **tableau d’exemples** : colonnes de données et résultats séparées par des
  points-virgules, avec plusieurs cas ;
- **checklist** : liste de contrôles observables indépendants.

Ces modes sont des aides de rédaction et non quatre modèles métier concurrents.
Ils produisent une même définition canonique contenant l’objectif, l’acteur,
l’environnement, les préconditions, données, postconditions, exigences, règles
métier, déclaration d’exécution, clauses ordonnées et exemples. Le texte saisi
est conservé pour l’édition ; toute modification crée une nouvelle version de
la définition.

L’arbre reste l’organisation primaire. L’interface fournit en complément des
vues calculées par tag, exigence, règle métier et mode de spécification, ainsi
qu’une recherche textuelle. Ces vues ne déplacent pas les cas de test et ne créent
aucune seconde taxonomie persistante.

### EF-007.5 — Données tabulaires et stratégies d’itération

Un utilisateur peut associer à un cas de test un fichier de données de test au
format CSV UTF-8 ou Excel Open XML (`.xlsx`). La première ligne fournit les
noms de variables et chaque ligne suivante représente une itération de données. Les
deux formats produisent le même modèle canonique : nom du fichier, empreinte,
colonnes ordonnées et lignes de valeurs textuelles.

L’import doit être borné et déterministe. Il refuse au minimum un fichier vide,
une extension inconnue, des en-têtes vides ou dupliqués, un tableau sans itération,
une archive Excel invalide et toute cellule Excel contenant une formule. Le
MVP accepte au plus 2 Mio, 50 colonnes et 1 000 cas par fichier. Les macros,
connexions externes et calculs du classeur ne sont jamais exécutés ; seul le
premier onglet de données non vide est lu.

L’association choisit une stratégie d’itération :

- **série** : une itération après l’autre, dans l’ordre du fichier ;
- **parallèle** : itérations regroupées en lots dont la concurrence maximale est
  explicitement bornée ;
- **aléatoire** : ordre mélangé sans remise, avec une graine enregistrée et un
  nombre d’itérations inférieur ou égal au nombre de lignes.

L’application montre un aperçu de l’ordonnancement avant toute exécution. Chaque itération
contient l’index de la ligne source et le dictionnaire colonne/valeur. Une même
graine reproduit exactement le même ordre aléatoire. Modifier le fichier ou la
stratégie crée une nouvelle version de liaison et le redémarrage restaure le
fichier canonique, la configuration et le plan.

L’import de données prépare les futurs lancements du runner mais ne les
déclenche pas depuis le processus web de conception. Les cellules sont des
données, jamais des commandes, sélecteurs exécutables ou références de secrets.

### EF-008 — Validation humaine et versionnement

L’utilisateur doit pouvoir :

- éditer le cas de test proposé ;
- accepter ou refuser une étape ;
- demander une nouvelle proposition ;
- générer puis lancer individuellement l’artefact candidat du cas de test en cours de conception ;
- consulter les preuves du lancement ;
- approuver une version immuable après validation de l’artefact exact.

Toute modification du modèle structuré ou du code après validation invalide l’état `validé individuellement` et crée un nouvel artefact candidat. Toute modification après approbation doit créer une nouvelle version brouillon. La version approuvée précédente reste exécutable et traçable jusqu’à son remplacement explicite.

### EF-009 — Lancement individuel en conception

Depuis l’éditeur, l’utilisateur doit pouvoir générer puis lancer uniquement le cas de test courant avec la version brouillon sélectionnée. Le script lancé doit être octet pour octet celui de l’artefact candidat présenté à l’utilisateur.

Ce lancement doit :

- afficher clairement qu’il s’agit d’une validation de conception ;
- utiliser un environnement et des secrets explicitement sélectionnés ;
- montrer les étapes au fur et à mesure ;
- permettre l’arrêt ;
- produire journaux, captures, trace et résultat ;
- ne pas approuver automatiquement le cas de test en cas de réussite ;
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
- l’action proposée sort du périmètre du cas de test autorisé ;
- une politique de sécurité interdit la cible ou l’action ;
- le nombre maximal d’étapes ou la durée maximale est atteint ;
- un éventuel LLM d’exécution ne répond pas dans ses limites.

Le système doit expliquer le blocage plutôt que d’inventer une réussite.

### 6.2 Exécution des suites et cas de test, et historisation

Cette partie décrit les fonctions du runner et de la CI. Elle utilise uniquement un bundle de code généré ou personnalisé, versionné et approuvé. Elle ne dépend pas de l’interface de conception.

### EF-012 — Génération et personnalisation du code

Le MVP génère des **scripts de test Playwright en Python** à partir des cas de test approuvés.

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

Pour un cas de test `performance`, le script doit mesurer uniquement les actions et seuils déclarés. Le MVP ne génère pas de trafic concurrent ni de test de charge.

Une personnalisation produit un nouvel artefact candidat. Elle ne peut être exportée comme version approuvée ni exécutée en CI sous l’identité de la version précédente avant une nouvelle exécution individuelle réussie et une nouvelle approbation de son empreinte.

### EF-013 — Usage exceptionnel du LLM d’exécution

Un cas de test peut activer une étape adaptative uniquement si elle est explicitement marquée et approuvée.

Une telle étape doit définir :

- la raison pour laquelle une stratégie déterministe ne suffit pas ;
- les observations transmissibles au LLM ;
- les décisions autorisées sous forme d’un schéma fermé ;
- le profil LLM d’exécution ;
- un délai maximal ;
- un budget maximal ;
- une stratégie en cas d’indisponibilité ou de réponse invalide.

Le LLM d’exécution ne peut pas :

- ajouter des étapes au cas de test ;
- naviguer vers une autre origine non autorisée ;
- demander de nouveaux secrets ;
- modifier le code ou la version approuvée ;
- transformer un échec en réussite sans assertion observable.

Chaque invocation doit être identifiable dans le rapport. Un pipeline doit pouvoir interdire globalement toute utilisation du LLM d’exécution.

### EF-014 — Prévisualisation et traçabilité

Avant export, l’utilisateur doit pouvoir consulter :

- le cas de test structuré ;
- sa description ;
- le code généré ou personnalisé ;
- les hypothèses ;
- les localisateurs retenus ;
- les différences avec une version précédente ;
- la version du générateur et du LLM de conception ;
- les éventuelles étapes autorisant le LLM d’exécution.

### EF-015 — Exécution automatisée

Le runner doit pouvoir lancer :

- un cas de test ;
- une suite de tests et tous ses descendants ;
- une sélection par tags ;
- l’ensemble des suites référencées par un plan de test ou un projet.

Il doit accepter une déclaration de sélection (`--declaration`) et ne retenir que les cas de test actifs dont l’attribut correspond à cette déclaration. En l’absence de déclaration, la valeur `manual` est utilisée.

Il doit accepter sa configuration par arguments, variables d’environnement et fichier versionnable sans secrets. Il doit produire :

- un code de sortie nul en cas de réussite, non nul en cas d’échec ou d’erreur ;
- un statut par cas de test et par étape de test ;
- des journaux structurés ;
- un rapport JUnit XML ;
- des captures, vidéos ou traces selon la politique choisie ;
- la version exacte du cas de test et du script exécutés.

Après chaque exécution, le runner doit produire un rapport détaillé et transmettre au service d’historisation un enregistrement de résultat contenant uniquement :

- la date de l’exécution ;
- un indicateur de réussite ;
- la durée mesurée.

L’association technique entre cet enregistrement et le cas de test est portée par la relation de stockage et ne constitue pas un champ de l’historique métier. Le service de conception doit pouvoir importer ces enregistrements et afficher l’historique des réussites et des durées sans charger les fichiers lourds. Les journaux, traces et rapports détaillés restent des artefacts liés à l’exécution, mais ne font pas partie de l’historique synthétique. Une exécution de CI ne doit pas modifier la définition du cas de test.

Pour un cas de test de type `performance`, le rapport détaillé conserve les mesures et les seuils comparés. L’historique synthétique ne conserve que la réussite et la durée. Une mesure dépassant un seuil produit un échec explicite, sans être transformée en simple information.

### EF-015.1 — Déclaration d’exécution du cas de test

Chaque cas de test possède une déclaration simple indiquant quand il peut être sélectionné par une CI, par exemple `on_commit`, `on_merge_request`, `nightly`, `release` ou `manual`. Cette déclaration est un attribut du cas de test, est visible dans le formulaire et peut être utilisée avec les tags pour construire une suite de tests destinée à une exécution donnée.

### EF-016 — Export et intégration Git

L’export est une action manuelle et explicite. Le système doit guider l’utilisateur en lui faisant choisir un plan de test, une ou plusieurs suites de tests, un environnement, une sélection de tags et un format de sortie. Les commandes techniques sont affichées sous forme de commandes prêtes à copier, mais ne sont pas exigées pour définir un cas de test.

Le système doit permettre de produire un paquet versionnable contenant :

- les scripts de test Playwright ;
- les spécifications structurées des cas de test ;
- l’arborescence ;
- les données d’exemple non secrètes ;
- un manifeste de versions ;
- les commandes d’installation et d’exécution ;
- des modèles GitHub Actions et GitLab CI ;
- une documentation fonctionnelle lisible ;
- une documentation de déploiement pour GitHub Actions ;
- une documentation de déploiement pour GitLab CI.

L’écriture directe dans un dépôt Git exige une autorisation dédiée et limitée au dépôt concerné. L’export local et l’exécution CLI doivent rester disponibles sans accès Git distant.

### EF-016.1 — Documentation fonctionnelle exportée

Chaque export doit générer une documentation fonctionnelle en Markdown à partir du plan de test et des versions approuvées des cas de test effectivement inclus dans les suites sélectionnées. Elle doit être compréhensible par un responsable produit, un fonctionnel métier ou un responsable QA sans lecture des scripts ni de la conversation de conception.

Cette documentation contient au minimum :

- le nom, les objectifs, le périmètre, l’approche et la version du plan de test ;
- l’arborescence des suites, sous-suites et cas de test exportés ;
- pour chaque cas de test, son objectif, son type, sa description approuvée, ses préconditions, ses données non secrètes, ses étapes et ses résultats attendus ;
- les `requirements`, `business_rules`, tags et déclarations d’exécution associés ;
- l’environnement logique ciblé et les dépendances attendues, sans URL sensible ni valeur secrète ;
- l’état d’approbation, la version et l’empreinte de chaque cas de test ;
- les références aux captures ou preuves utiles lorsqu’elles existent, sans rendre les captures obligatoires.

Le LLM de conception peut produire la rédaction initiale, mais le contenu exporté doit être reconstruit à partir de la représentation structurée approuvée et contrôlé par schéma. Il ne doit contenir ni hypothèse non confirmée, ni historique de conversation, ni secret, ni résultat d’exécution présenté comme une exigence fonctionnelle. L’utilisateur doit pouvoir prévisualiser la documentation avant de confirmer l’export.

### EF-016.2 — Documentation de déploiement CI/CD exportée

Chaque export doit générer deux guides Markdown distincts, l’un pour GitLab CI et l’autre pour GitHub Actions. Chaque guide doit correspondre exactement au bundle, au runner et aux modèles de pipeline exportés.

Chaque guide contient au minimum :

- les versions minimales et prérequis du runner ;
- la commande d’installation ou l’image OCI à utiliser, épinglable par version ou digest ;
- l’emplacement du bundle et la commande d’exécution ;
- les variables d’environnement requises, avec distinction entre valeurs ordinaires et secrets ;
- la configuration des variables ou secrets protégés propre à la plateforme ;
- les déclarations d’exécution prises en charge et leur correspondance avec les événements de pipeline ;
- la publication des rapports JUnit, journaux, captures et traces ;
- les permissions, protections de branches ou d’environnements et restrictions réseau minimales ;
- une procédure de validation du pipeline et les principaux diagnostics d’échec ;
- la procédure de mise à jour ou de retour à une version antérieure du bundle.

Les guides ne doivent contenir aucune valeur secrète. Une incohérence entre un guide, le manifeste et le modèle de pipeline doit bloquer l’export.

### EF-016.3 — Publication manuelle vers un GitLab d’entreprise

Un administrateur doit pouvoir configurer une ou plusieurs cibles GitLab auto-hébergées ou d’entreprise. Une cible possède au minimum :

- un identifiant stable et un libellé ;
- l’URL de base HTTPS de l’instance GitLab ;
- un projet autorisé, identifié par son chemin ou son identifiant GitLab ;
- une branche par défaut, un préfixe de branche de publication et un chemin de destination dans le dépôt ;
- un mode de publication autorisé : commit sur une branche dédiée ou création/mise à jour d’une merge request ;
- une référence vers un secret d’authentification ;
- les autorités de certification, délais et paramètres de proxy nécessaires, sans désactiver silencieusement la vérification TLS.

La connectivité et les droits de lecture doivent pouvoir être vérifiés séparément sans effectuer d’écriture. Le secret doit être limité au projet et aux opérations nécessaires à la publication.

Depuis l’écran d’export, un utilisateur autorisé doit pouvoir sélectionner une cible configurée puis déclencher manuellement la publication du bundle. Avant confirmation, le système affiche l’instance, le projet, la branche, le chemin, la liste des fichiers et le diff prévu. La publication doit :

- utiliser exactement le bundle prévisualisé et son empreinte ;
- créer un commit traçable indiquant l’utilisateur, le plan de test, les suites exportées et leurs versions ;
- ne jamais effectuer de `force push` ni écraser silencieusement une modification distante ;
- refuser un projet, une branche ou un chemin hors des valeurs autorisées ;
- proposer une nouvelle branche ou signaler un conflit lorsque la branche distante a divergé ;
- retourner l’identifiant du commit et, le cas échéant, l’URL de la merge request ;
- enregistrer l’opération et son résultat dans le journal d’audit sans enregistrer le secret.

L’indisponibilité de GitLab ou un échec de publication ne doit pas invalider le bundle exporté localement. L’exécution du bundle reste indépendante de l’API GitLab.

### EF-017 — Catalogue de phrases d’intention fonctionnelle

La conception doit fournir un catalogue de phrases décrivant la diversité des cas de test fonctionnels. Le catalogue est chargé depuis un fichier de configuration administrable et peut être enrichi sans modification du code.

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
- vérifier un seuil de durée pour un cas de test `performance`.

Chaque phrase possède un identifiant, un libellé métier, des exemples, les précisions attendues et le type de test conseillé. Le LLM peut s’appuyer sur ce catalogue pour proposer les questions manquantes et les assertions adaptées. L’utilisateur confirme toujours la phrase retenue et ses paramètres.

## 7. Exigences de qualité des scripts de test

### 7.1 Déterminisme

Pour un cas de test, un état initial et une version de générateur identiques, le script de test doit conserver la même structure fonctionnelle. Les variations stylistiques du LLM de conception ne doivent pas modifier silencieusement le comportement approuvé.

### 7.2 Maintenabilité

Le script de test doit privilégier :

1. les rôles et noms accessibles ;
2. les libellés de formulaire ;
3. les attributs de test convenus avec l’équipe ;
4. les sélecteurs CSS stables en dernier recours.

Les sélecteurs dépendant d’une position, d’un identifiant généré ou d’une structure DOM profonde doivent être signalés comme fragiles.

### 7.3 Lisibilité

Chaque cas de test doit exprimer clairement :

- son intention ;
- sa préparation ;
- son action principale ;
- ses assertions ;
- son nettoyage éventuel.

La hiérarchie et la description doivent permettre de comprendre le rôle d’un cas de test sans ouvrir son historique de conversation.

### 7.4 Réutilisabilité

Les parcours partagés peuvent être extraits en fonctions, fixtures ou objets de page lorsqu’au moins deux cas de test justifient cette factorisation. Le MVP ne doit pas générer une hiérarchie abstraite de code par anticipation.

### 7.5 Reproductibilité

Un export doit déclarer ses versions minimales, sa commande d’installation, sa commande d’exécution et les variables d’environnement attendues.

### 7.6 Personnalisation sûre

Le code personnalisé doit être distingué du code régénérable. Une régénération doit soit préserver les zones personnalisées par un mécanisme explicite, soit produire un conflit visible ; elle ne doit jamais écraser silencieusement une modification humaine.

## 8. Exigences non fonctionnelles

### ENF-001 — Déploiement simple

Une instance locale ou en ligne doit pouvoir déployer la phase de conception avec :

- une image OCI versionnée ;
- une commande Docker ou Podman ;
- un volume persistant ;
- un fichier de configuration et des secrets externes.

Le mode local ne doit pas imposer PostgreSQL, Kubernetes, Redis, un bus de messages ou plusieurs bases de données. Le mode en ligne utilise une base partagée adaptée aux accès concurrents sans modifier le domaine.

### ENF-002 — Runner autonome

Le runner d’exécution doit être installable et lançable indépendamment du service web de conception. Il doit pouvoir fonctionner :

- depuis une image OCI versionnée ;
- depuis un environnement Python verrouillé ;
- sans accès à la base de données de conception ;
- sans LLM lorsque les cas de test sélectionnés sont déterministes.

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

Les jetons utilisés pour publier vers un GitLab d’entreprise sont référencés depuis le mécanisme de secrets de l’application. Ils doivent être limités au projet configuré et aux droits strictement nécessaires à la lecture du dépôt, à la création d’un commit et, si ce mode est autorisé, à la gestion d’une merge request. Leur rotation ou révocation ne doit pas nécessiter de modifier un bundle exporté.

### ENF-005 — Isolation d’exécution

Le navigateur et les scripts de test générés ou personnalisés sont considérés comme non fiables. Dans le MVP, ils doivent s’exécuter dans un conteneur runner distinct de l’application de conception avec les garanties minimales suivantes :

- utilisateur non privilégié ;
- système de fichiers racine en lecture seule ;
- bundle monté en lecture seule ;
- seul le répertoire d’artefacts est accessible en écriture ;
- répertoire temporaire dédié et supprimé après le job ;
- aucun montage du volume, de la base de conception ou de son stockage d’artefacts ;
- aucun accès au socket Docker, Podman ou au socket d’un autre orchestrateur ;
- capacités Linux supprimées et option `no-new-privileges` ;
- limites de CPU, mémoire, PID et durée ;
- secrets injectés uniquement pour le job et limités à la cible concernée ;
- réseau refusé par défaut hors origines explicitement autorisées, endpoint LLM d’exécution compris lorsqu’il est nécessaire.

Le conteneur de validation de conception et le conteneur utilisé en CI appliquent le même profil minimal d’isolation. Une impossibilité technique d’appliquer une limite exigée doit faire échouer le lancement plutôt que dégrader silencieusement l’isolation.

### ENF-006 — Auditabilité

Chaque décision automatisée importante doit être rattachée à :

- une demande utilisateur ou une étape approuvée ;
- une version de cas de test ;
- une version de script de test ;
- une version de modèle et de prompt lorsqu’un LLM intervient ;
- une observation ou preuve ;
- une action résultante.

### ENF-007 — Confidentialité

La politique de conservation des conversations, captures, traces et prompts doit être explicite. La suppression d’un projet doit pouvoir supprimer ses artefacts selon la politique définie.

### ENF-008 — Portabilité

Le domaine métier doit être indépendant des adaptateurs de LLM, de stockage, de navigateur et de CI. Un cas de test exporté ne doit pas dépendre d’un identifiant interne opaque pour être exécuté.

### ENF-009 — Résilience

Une indisponibilité du LLM de conception, du LLM d’exécution, du navigateur ou de la cible doit produire un état structuré et compréhensible. Aucun composant ne doit simuler un succès pour masquer une dépendance indisponible.

### ENF-010 — Observabilité

Les journaux doivent permettre de corréler un projet, un plan de test, une suite de tests, un cas de test, une génération et une exécution sans enregistrer de secrets. Des métriques minimales doivent couvrir les durées, échecs, usages des LLM et causes de blocage.

### ENF-011 — Compatibilité CI

L’intégration ne doit pas dépendre d’une API propriétaire de GitHub ou GitLab pour exécuter les suites et cas de test. Le contrat primaire est :

- une commande non interactive ;
- des codes de sortie standards ;
- des rapports JUnit XML ;
- des artefacts sur le système de fichiers ;
- une configuration par environnement ;
- une image OCI épinglable par version ou digest.

Les adaptateurs GitHub Actions et GitLab CI sont des modèles de commodité construits sur ce contrat portable.

L’adaptateur de publication manuelle peut utiliser l’API d’une instance GitLab configurée. Cette dépendance concerne uniquement le transfert du bundle vers le dépôt ; elle ne doit jamais être nécessaire à l’exécution locale ou en CI d’un bundle déjà exporté.

### ENF-012 — Vérifications système des préconditions

Avant toute exécution, le runner doit effectuer et journaliser un contrôle déterministe de la cible, de l’environnement, des données, des secrets référencés, du navigateur, des ressources et du réseau autorisé. Un contrôle impossible ou échoué doit empêcher l’exécution et produire un résultat explicite.

Ces vérifications système ne peuvent pas être remplacées par une réponse d’un LLM. Le LLM de conception peut seulement aider à formuler la demande, expliquer le résultat ou proposer une modification soumise à validation humaine.

### ENF-013 — Parité locale/en ligne et concurrence

Les modes `local` et `online` utilisent le même paquet applicatif et exposent les mêmes cas d’usage. Un test de contrat doit être exécutable contre chaque composition d’adaptateurs afin de vérifier cette parité.

Le mode local utilise par défaut SQLite et un stockage de fichiers sur le poste. Le mode en ligne utilise PostgreSQL et un stockage partagé configurable. Les migrations conservent un schéma logique commun.

En mode local, la fermeture puis le redémarrage du processus doit reconstruire les projets, appartenances, plans de test, suites de tests, cas de test, nœuds, ordres et historiques depuis SQLite. Les migrations sont versionnées, transactionnelles et idempotentes ; une version de schéma inconnue ou plus récente doit bloquer le démarrage en écriture.

Le mode en ligne doit :

- exiger une identité authentifiée fournie par un adaptateur remplaçable ;
- appliquer l’autorisation côté serveur à chaque cas d’usage ;
- supporter les accès concurrents sans partager d’état de requête en mémoire ;
- utiliser des transactions et un contrôle de concurrence explicite pour éviter les écrasements silencieux ;
- permettre plusieurs projets par utilisateur et plusieurs membres par projet.

Le mode local peut utiliser une identité implicite, mais ne peut pas contourner les contrôles d’appartenance du cœur applicatif.

## 9. Modèle conceptuel

### Projet

Regroupe des plans de test, une cible, des profils autorisés et une politique de sécurité.

### Plan de test

Décrit les objectifs, le périmètre, la base de test, l’approche de test, les risques, les ressources, les contraintes, les critères d’entrée et de sortie, les besoins d’environnement et de données, ainsi que l’ordonnancement prévisionnel. Il référence une ou plusieurs suites de tests et peut être versionné et exporté ; il n’est pas lui-même exécuté.

### Suite de tests

Assemble une sélection ordonnée de cas de test ou de sous-suites en vue d’une exécution déterminée. La résolution de cet ordre et des dépendances produit une procédure de test. La suite possède un identifiant stable, un objectif d’exécution, des préconditions et postconditions communes facultatives, ainsi que des valeurs par défaut de type de test et de déclaration d’exécution. Elle peut être sélectionnée et exécutée indépendamment lorsque ses dépendances sont satisfaites.

### Cible GitLab d’entreprise

Décrit une instance GitLab autorisée, un projet, une stratégie de branche, un chemin de destination, un mode de publication et une référence de secret. Elle ne contient jamais le jeton d’accès lui-même.

### Nœud hiérarchique

Représente une suite de tests, un dossier de classement ou un cas de test avec un identifiant stable, un parent, un ordre et des tags. Un dossier de classement n’est pas exécutable.

### Profil LLM de conception

Décrit l’identifiant, la version, le fournisseur, le protocole, l’endpoint, le modèle, les capacités, les paramètres, les limites et la référence de secret utilisés pendant l’édition.

### Profil LLM d’exécution

Décrit séparément l’identifiant, la version, le fournisseur, le protocole, l’endpoint, le modèle, les capacités, les paramètres, les limites et la référence de secret autorisés pour une étape adaptative.

### Conversation de conception

Conserve les échanges utiles à l’édition sans devenir la source de vérité du cas de test.

### Cas de test structuré

Versionne le titre, l’objectif, la description synthétique, le type de test, les attributs `requirements` et `business_rules`, les préconditions exprimées par le métier, leur traduction en dépendances exécutables, les données de test, le profil d’environnement, les actions, résultats attendus, postconditions, hypothèses, tags, déclaration d’exécution et politique d’usage du LLM d’exécution.

### Version de cas de test

Possède un état `brouillon`, `artefact candidat`, `validé individuellement`, `approuvé` ou `retiré`. Une validation individuelle référence l’empreinte exacte du script exécuté. Une version approuvée lie de façon immuable le cas de test structuré, le script validé et cette empreinte.

### Capture et observation

Conservent une preuve visuelle ou structurée et leur relation avec une étape et une version.

### Script de test

Associe une version de cas de test à des instructions Playwright générées ou personnalisées, à un manifeste, à la version du générateur et à une empreinte. Le script est candidat jusqu’à son exécution individuelle réussie et son approbation. Toute modification de fichier change l’empreinte et annule la validation précédente.

### Exécution de test

Associe une suite de tests ou un cas de test et son script immuable à une version de l’objet de test, un environnement, un déclencheur, un résultat de test, des journaux, des rapports et des preuves.

### Historique des résultats de test

Conserve uniquement, pour chaque résultat de test, la date, l’indicateur de réussite et la durée. L’association au cas de test est une relation technique de stockage ; elle n’est pas un champ de l’historique métier. Les rapports détaillés, journaux, captures et traces restent des artefacts séparés.

### Journal d’audit du cycle de vie

Conserve séparément les transitions d’état, l’utilisateur, la date et la version concernée. Ce journal ne doit pas être utilisé comme historique synthétique des résultats.

### Modèle de cas de test

Décrit un parcours de saisie guidée avec un type par défaut, des champs obligatoires, des aides, des exemples et des questions utilisées par le LLM de conception.

### Phrase d’intention

Décrit une famille de comportements fonctionnels et les précisions nécessaires à sa transformation en cas de test structuré.

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
│ Navigateur   │──────────▶│ Application Sentinelle Fonctionnelle │
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
- **Persistance locale :** SQLite sur le poste ou un volume persistant.
- **Persistance en ligne :** PostgreSQL partagé, avec transactions et migrations communes.
- **Artefacts :** système de fichiers local ou stockage partagé, derrière une même interface.
- **Migrations :** mécanisme versionné exécuté explicitement au démarrage ou par commande dédiée.
- **Validation navigateur :** runner conteneurisé distinct, sans montage du volume de conception et conforme au profil d’isolation défini par `ENF-005`.

SQLite, PostgreSQL et les stockages d’artefacts sont des adaptateurs et non des dépendances du domaine. Les cas d’usage reçoivent une identité applicative résolue soit par l’adaptateur local, soit par l’adaptateur d’authentification en ligne.

L’application de conception ne lance jamais de script de test dans son propre processus et ne reçoit jamais un socket Docker ou Podman. Pour le MVP complet, un second conteneur runner dédié à la validation est démarré par Docker Compose ou Podman Compose. Il reçoit les jobs et bundles minimaux par une API authentifiée interne, sans accès aux volumes de l’application.

#### Runner d’exécution

- **Langage :** Python.
- **Framework :** Playwright pour Python et pytest.
- **Interface :** CLI non interactive.
- **Distribution :** paquet Python verrouillé et image OCI incluant les navigateurs compatibles.
- **Entrées :** bundle de scripts de test, sélecteur de suite de tests, de cas de test ou de tags, URL cible, configuration et références de secrets.
- **Sorties :** code de sortie, JUnit XML, JSON structuré, journaux, captures et traces.
- **Dépendance au service web :** aucune pour exécuter un bundle déjà exporté.
- **Dépendance à un LLM :** aucune par défaut.
- **Isolation :** utilisateur non privilégié, racine en lecture seule, bundle en lecture seule, artefacts séparés, capacités supprimées, limites de ressources et réseau autorisé explicitement.

### 10.4 Modules de l’application de conception

```text
sentinelle_fonctionnelle/
├── domain/            # Entités, règles, états et événements métier
├── application/       # Cas d’utilisation et ports
├── adapters/
│   ├── llm/           # Port commun et adaptateurs OpenAI, Ollama et Mistral
│   ├── persistence/   # SQLite local et PostgreSQL en ligne
│   ├── artifacts/     # Volume local puis stockage objet
│   ├── configuration/ # Modèles, phrases, tags, environnements et cibles Git
│   ├── browser/       # Playwright pour la validation interactive
│   └── git/           # Export local et publication manuelle vers GitLab
├── web/               # API FastAPI, vues et ressources statiques
├── generation/        # Génération déterministe d’un candidat depuis le brouillon structuré
└── security/          # Politiques de destination, secrets et autorisations

runner/
├── cli/               # Commandes et configuration non interactive
├── selection/         # Résolution des suites de tests, cas de test et tags
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
11. Toute modification du cas de test ou du script annule cette validation.
12. L’approbation fige ensemble la version structurée, l’artefact validé et son empreinte.

### 10.6 Flux d’exécution

1. Le runner valide le manifeste, les versions et la sélection demandée.
2. Il charge la configuration de l’environnement sans écrire les secrets dans les journaux.
3. Il résout les suites sélectionnées en une liste ordonnée de cas de test.
4. Il lance pytest et Playwright avec les limites configurées.
5. Une étape déterministe utilise exclusivement le code approuvé.
6. Une étape adaptative vérifie d’abord qu’un LLM d’exécution est autorisé par le cas de test et la politique du pipeline.
7. La réponse du LLM est validée par un schéma fermé avant toute action.
8. Le runner agrège les résultats et écrit les rapports détaillés.
9. Il enregistre pour chaque cas de test la réussite, la durée et la date dans l’historique minimal.
10. Il termine avec un code de sortie standard sans dépendre du service de conception.

### 10.7 Contrats entre conception et exécution

La frontière est un bundle versionné contenant au minimum :

```text
sentinelle-bundle/
├── sentinelle-manifest.json
├── hierarchy.yaml
├── tests/
├── pages/
├── fixtures/
├── data/
├── load-profiles/     # Profils de charge versionnés, sans moteur embarqué dans le MVP
├── docs/
│   ├── functional.md
│   ├── deploy-gitlab-ci.md
│   └── deploy-github-actions.md
├── ci/
│   ├── gitlab-ci.yml
│   └── github-actions.yml
├── requirements.lock
├── pytest.ini
└── README.md
```

Le manifeste indique :

- la version du format ;
- l’identifiant et la version du plan de test ;
- l’identifiant et la version des suites de tests ;
- l’identifiant et la version des cas de test ;
- le type de chaque cas de test ;
- la version du générateur ;
- les versions Python, pytest et Playwright ;
- les profils logiques requis, sans secret ;
- les tags et chemins hiérarchiques ;
- la déclaration d’exécution de chaque cas de test ;
- les politiques d’artefacts et d’usage du LLM d’exécution ;
- les fichiers de documentation et modèles CI associés ;
- une empreinte de chaque fichier et une empreinte globale du bundle ;
- l’état d’approbation et l’empreinte validée individuellement.

Le runner doit refuser un format incompatible, un bundle incomplet ou une empreinte différente de celle approuvée avec un message explicite. Une CI ne peut exécuter un artefact modifié sous l’identité d’une version approuvée.

Un bundle contenant `load-profiles/` peut être validé et exporté par le MVP. Il ne peut être exécuté qu’après sélection d’un adaptateur de charge installé, vérifié et autorisé pour l’environnement ciblé.

### 10.8 Déploiement de la conception

Deux profils officiels utilisent la même image applicative et les mêmes migrations :

1. `local` : service web lié par défaut à l’interface de boucle locale, identité locale implicite, SQLite et artefacts sur le poste ;
2. `online` : service web exposé derrière HTTPS, identité authentifiée obligatoire, PostgreSQL et stockage d’artefacts partagé.

La configuration choisit les adaptateurs au démarrage. Elle ne peut pas masquer ou remplacer un cas d’usage métier. Les exports produits dans un mode doivent être importables et exécutables dans l’autre.

Le déploiement d’évaluation de l’interface, sans exécution de script de test, doit nécessiter :

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

1. installation ou conteneur local avec SQLite ;
2. Docker Compose ou Podman Compose local avec runner isolé ;
3. déploiement en ligne avec PostgreSQL, HTTPS et runner isolé ;
4. Kubernetes ou une plateforme équivalente uniquement comme option de montée en charge.

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
  TARGET_BASE_URL: http://sentinelle-target:8080
  SENTINELLE_FONCTIONNELLE_RUNNER_IMAGE: ghcr.io/pessonnier/sentinelle-fonctionnelle-runner:0.1.0
  SENTINELLE_FONCTIONNELLE_TARGET_IMAGE: ghcr.io/pessonnier/sentinelle-fonctionnelle-demo-target:0.1.0

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
          docker network create --internal sentinelle-ci
          trap 'docker rm -f sentinelle-target >/dev/null 2>&1 || true; docker network rm sentinelle-ci >/dev/null 2>&1 || true' EXIT
          docker run -d --rm \
            --name sentinelle-target \
            --network=sentinelle-ci \
            --user=10001:10001 \
            --read-only \
            --cap-drop=ALL \
            --security-opt=no-new-privileges \
            "$SENTINELLE_FONCTIONNELLE_TARGET_IMAGE"
          declaration=manual
          if [ "$GITHUB_EVENT_NAME" = pull_request ]; then declaration=on_merge_request; fi
          docker run --rm \
            --network=sentinelle-ci \
            --user=10001:10001 \
            --read-only \
            --cap-drop=ALL \
            --security-opt=no-new-privileges \
            --pids-limit=256 \
            --memory=2g \
            --cpus=2 \
            --tmpfs /tmp:rw,noexec,nosuid,size=512m \
            -v "$PWD/sentinelle-bundle:/bundle:ro" \
            -v "$PWD/artifacts:/artifacts:rw" \
            -e TARGET_BASE_URL \
            -e SENTINELLE_FONCTIONNELLE_DECLARATION="$declaration" \
            "$SENTINELLE_FONCTIONNELLE_RUNNER_IMAGE" \
            sentinelle-run --bundle /bundle --declaration "$declaration" --junit /artifacts/junit.xml
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: sentinelle-results
          path: artifacts/
```

Le workflow `pull_request` ci-dessus est destiné aux cas de test sans secret sur une cible de démonstration jetable. Le réseau Docker `--internal` relie uniquement le runner et cette cible, sans route de sortie générale. L’image du runner garantit que l’UID/GID `10001:10001` existe et peut écrire dans `/artifacts`. Le job impose une durée maximale. Il ne transmet aucun secret au code provenant de la PR.

Les cas de test authentifiés ou visant une cible externe doivent utiliser un workflow séparé, déclenché uniquement depuis une branche approuvée ou un `workflow_dispatch`, associé à un environnement GitHub protégé avec approbation. Ce workflow doit attacher le runner à un réseau dont la sortie est filtrée par un proxy ou une politique d’egress limitée aux origines approuvées. Les secrets sont alors fournis par `secrets`, limités au job et jamais inscrits dans le bundle. Un workflow ne doit jamais utiliser `pull_request_target` pour exécuter le code provenant de la PR. Les PR issues de forks ou de sources non approuvées ne reçoivent aucun secret ni accès à une cible sensible.

### 10.10 Intégration GitLab CI

Le dépôt doit fournir un modèle équivalent :

```yaml
sentinelle-functional-tests:
  image:
    name: ghcr.io/pessonnier/sentinelle-fonctionnelle-runner:0.1.0
    entrypoint: [""]
  variables:
    TARGET_BASE_URL: $SENTINELLE_FONCTIONNELLE_TARGET_BASE_URL
    SENTINELLE_FONCTIONNELLE_DECLARATION: on_merge_request
  before_script:
    - mkdir -p artifacts
  script:
    - sentinelle-run --bundle ./sentinelle-bundle --declaration "$SENTINELLE_FONCTIONNELLE_DECLARATION" --junit ./artifacts/junit.xml
  artifacts:
    when: always
    reports:
      junit: artifacts/junit.xml
    paths:
      - artifacts/
```

L’image garantit que `sentinelle-run` est disponible dans le `PATH`. L’`entrypoint` vide rend le contrat explicite pour les runners GitLab qui injectent leur propre script.

Le modèle utilise `on_merge_request` pour un pipeline de merge request. Les jobs `on_commit`, `nightly` et `release` doivent fournir la valeur correspondante dans `SENTINELLE_FONCTIONNELLE_DECLARATION`.

Les variables sensibles utilisent les variables CI/CD masquées et protégées de GitLab et ne sont disponibles que sur les branches ou environnements protégés. Les pipelines de merge requests externes ou non approuvées n’accèdent à aucune variable protégée ni cible sensible. L’exécuteur GitLab doit lui-même être non privilégié, sans montage de socket de runtime, et appliquer les limites de ressources et la politique réseau définies par `ENF-005`.

### 10.10.1 Publication vers un GitLab d’entreprise

La publication manuelle utilise un port applicatif indépendant du générateur et un adaptateur GitLab remplaçable. La configuration versionnable contient uniquement les cibles et règles non secrètes ; le jeton est résolu au moment de l’action depuis le mécanisme de secrets.

Le flux est le suivant :

1. l’utilisateur prépare et prévisualise un export local complet ;
2. il sélectionne une cible GitLab administrée ;
3. l’application vérifie la cible, les droits, la branche distante et le chemin autorisé ;
4. elle calcule le diff entre le bundle prévisualisé et le contenu distant ;
5. l’utilisateur confirme explicitement la publication ;
6. l’adaptateur crée ou met à jour une branche sans réécriture forcée de l’historique ;
7. il crée ou met à jour une merge request uniquement si le profil l’autorise ;
8. l’application conserve l’empreinte publiée, l’identifiant du commit, l’éventuelle merge request et le résultat dans le journal d’audit.

L’adaptateur doit accepter les URL d’instances auto-hébergées, les autorités de certification d’entreprise configurées et les proxys administrés. Il doit refuser les redirections vers une autre origine, les certificats invalides non approuvés et toute cible sortant du projet configuré.

### 10.11 Évolutivité après le MVP

Sans modifier les contrats du domaine et du bundle, une version ultérieure pourra :

- remplacer le volume local par un stockage objet ;
- exécuter les validations dans des workers distants ;
- ajouter une file de tâches ;
- ajouter d’autres adaptateurs d’authentification d’entreprise ;
- publier automatiquement des branches ou demandes de fusion ;
- prendre en charge d’autres langages ou frameworks de test.

Ces capacités ne doivent pas complexifier le déploiement minimal du MVP.

## 11. Définition du MVP

### 11.1 Objectif

Le MVP doit démontrer qu’un utilisateur peut élaborer un plan de test, organiser ses cas de test en suites, les valider individuellement, les exporter et exécuter leurs scripts Playwright en CI sans dépendre d’un LLM pendant l’exécution nominale.

### 11.2 Périmètre fonctionnel inclus

Le MVP est livré en deux tranches obligatoires. La première prouve la valeur fonctionnelle locale ; la seconde rend exactement les mêmes artefacts exploitables de façon sûre en CI. Le MVP n’est déclaré achevé que lorsque les deux tranches sont validées.

#### Tranche A — Conception et validation locale

1. une même application web déployable en mode local ou en ligne, avec parité fonctionnelle, plusieurs utilisateurs et plusieurs projets en ligne ;
2. un projet, plusieurs plans de test, suites de tests, sous-suites ou dossiers de classement ;
3. la création, le déplacement et l’ordonnancement de cas de test dans l’arborescence ;
4. les types `smoke`, `sanity`, `acceptance`, `regression`, `e2e`, `performance` et `load` ;
5. le cycle de vie brouillon, en conception, candidat, validé individuellement, approuvé, actif, retiré et archivé ;
6. un profil LLM de conception configurable par fournisseur, protocole, endpoint, modèle, capacités, paramètres, limites et référence de secret ;
7. un profil LLM d’exécution séparé, facultatif et désactivé par défaut ;
8. un éditeur conversationnel et structuré sans saisie YAML pour les métiers ;
9. la documentation de tous les champs du formulaire ;
10. l’ajout de captures d’écran ;
11. la mise à jour automatique d’une description synthétique et factuelle ;
12. les attributs `requirements` et `business_rules` ;
13. la saisie textuelle des préconditions et leur traduction confirmée en dépendances exécutables ;
14. les jeux de données de test et profils d’environnement sélectionnables par libellé ;
15. la liste administrable des modèles de cas de test et des phrases d’intention ;
16. la liste administrable des tags ;
17. la représentation versionnée des étapes, données et assertions ;
18. la génération d’un artefact candidat Playwright en Python ;
19. le lancement individuel de cet artefact exact dans le runner isolé ;
20. l’approbation explicite du cas de test structuré, du script validé et de leur empreinte ;
21. la possibilité de personnaliser le script, avec invalidation et nouvelle validation obligatoires ;
22. une démonstration E2E sur une application cible contrôlée ;
23. des adaptateurs OpenAI, Ollama et Mistral configurables et vérifiables indépendamment ;
24. une procédure de connexion complète, versionnée et validée pour chacun de ces trois fournisseurs ;
25. des écrans distincts pour le projet, le plan et le cas, avec création hiérarchique guidée et sections séparées pour les étapes, données et résultats attendus.

#### Tranche B — Exécution autonome et CI

1. un runner autonome capable de sélectionner un cas de test, une suite de tests ou des tags ;
2. des rapports console, JSON et JUnit XML ;
3. des captures et traces en cas d’échec ;
4. un bundle versionnable dont l’empreinte approuvée est vérifiée ;
5. une image OCI de conception et une image OCI de runner isolé ;
6. un fichier Compose appliquant les séparations de volumes et de secrets ;
7. des exemples Docker, Podman, GitHub Actions et GitLab CI ;
8. l’historisation minimale des réussites, durées et dates ;
9. l’évaluation des seuils des cas de test `performance` dans les rapports ;
10. la définition, la validation, le versionnement et l’export d’un cas de test `load` paramétré, sans exécution par un moteur de charge dans le MVP ;
11. la prise en compte de la déclaration d’exécution du cas de test ;
12. une démonstration CI sans secret sur une cible contrôlée ;
13. la génération et la prévisualisation d’une documentation fonctionnelle lisible pour le plan de test et les suites exportées ;
14. la génération de guides de déploiement cohérents avec les modèles GitLab CI et GitHub Actions exportés ;
15. la configuration d’une cible GitLab d’entreprise et la publication manuelle d’un bundle sur une branche dédiée, avec création optionnelle d’une merge request.

### 11.3 Usage du LLM dans le MVP

Le LLM de conception est utilisé pour :

- poser des questions de clarification ;
- proposer des modifications structurées ;
- synthétiser la description ;
- suggérer des localisateurs ;
- générer le code initial ;
- rédiger la proposition initiale de documentation fonctionnelle à partir des données approuvées ;
- proposer des questions à partir d’un modèle de cas de test ;
- traduire les préconditions textuelles en dépendances candidates ;
- proposer des données de test, types de test, tags, `requirements` et `business_rules` ;
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

- l’exploration autonome sans cas de test borné ;
- la résolution de CAPTCHA ;
- le contournement d’une authentification ou d’un MFA ;
- les applications mobiles ou desktop natives ;
- l’exécution réelle par un moteur de charge dédié ;
- plusieurs frameworks de génération ;
- l’exécution distribuée ;
- Kubernetes comme prérequis ;
- PostgreSQL comme prérequis du mode local ou un stockage objet comme prérequis des deux modes ;
- l’édition collaborative en temps réel ;
- la publication automatique dans un dépôt distant ;
- la correction automatique de l’application cible ;
- l’apprentissage ou le fine-tuning d’un modèle.

## 12. Critères d’acceptation du MVP

Le MVP est acceptable lorsque les critères suivants sont vérifiés par des cas de test automatisés et une démonstration réelle :

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
| 15 | `ACC-015` | 31 | `ACC-031` | 47 | `ACC-047` |
| 16 | `ACC-016` | 32 | `ACC-032` | 48 | `ACC-048` |
|  |  |  |  | 49 | `ACC-049` |
|  |  |  |  | 50 | `ACC-050` |
|  |  |  |  | 51 | `ACC-051` |
|  |  |  |  | 52 | `ACC-052` |
|  |  |  |  | 53 | `ACC-053` |
|  |  |  |  | 54 | `ACC-054` |
|  |  |  |  | 55 | `ACC-055` |
|  |  |  |  | 56 | `ACC-056` |
|  |  |  |  | 57 | `ACC-057` |
|  |  |  |  | 58 | `ACC-058` |
|  |  |  |  | 59 | `ACC-059` |
|  |  |  |  | 60 | `ACC-060` |
|  |  |  |  | 61 | `ACC-061` |
|  |  |  |  | 62 | `ACC-062` |
|  |  |  |  | 63 | `ACC-063` |
|  |  |  |  | 64 | `ACC-064` |
|  |  |  |  | 65 | `ACC-065` |
|  |  |  |  | 66 | `ACC-066` |
|  |  |  |  | 67 | `ACC-067` |
|  |  |  |  | 68 | `ACC-068` |
|  |  |  |  | 69 | `ACC-069` |
|  |  |  |  | 70 | `ACC-070` |
|  |  |  |  | 71 | `ACC-071` |
|  |  |  |  | 72 | `ACC-072` |

1. L’interface seule démarre avec une image OCI, un volume et une configuration documentée ; le MVP complet démarre avec le fichier Compose et son runner isolé.
2. Un utilisateur crée un plan de test et une arborescence contenant au moins une suite de tests, une sous-suite et deux cas de test.
3. Le déplacement d’un cas de test conserve son identifiant et son historique.
4. Un utilisateur configure et vérifie un profil LLM de conception.
5. Le profil LLM d’exécution est stocké séparément et peut rester absent.
6. Une capture valide est rattachée à un cas de test ; un format invalide est refusé explicitement.
7. Un échange accepté met à jour le cas de test structuré et propose une description synthétique cohérente.
8. La description ne contient ni hypothèse non confirmée ni verbatim inutile de la conversation.
9. Une réponse LLM invalide ne peut pas modifier ou approuver un cas de test.
10. L’utilisateur génère et lance individuellement un artefact candidat, puis consulte ses étapes, preuves et empreinte.
11. Une réussite de validation ne provoque pas une approbation automatique.
12. L’approbation lie la version structurée, le script réellement exécuté et son empreinte.
13. Toute personnalisation ou régénération invalide la validation et exige un nouveau lancement avant approbation.
14. Une version approuvée est immuable ; sa modification crée un nouveau brouillon et un nouvel artefact candidat.
15. Une destination interdite est bloquée avant le lancement du navigateur.
16. Le script généré ne contient ni référence éphémère de navigateur ni secret.
17. Le runner de validation ne voit ni volume de conception, ni socket de runtime, et n’écrit que dans son répertoire d’artefacts.
18. Le script Playwright du cas de test approuvé réussit sur l’application de démonstration sans LLM d’exécution.
19. Une régression volontaire de la cible fait échouer le cas de test avec une preuve exploitable.
20. Une étape adaptative ne peut utiliser que le profil LLM d’exécution et les décisions autorisées.
21. Le runner peut interdire tout LLM d’exécution et échoue explicitement si un cas de test en exige un.
22. Le bundle s’exécute sans connexion au service web de conception.
23. Le runner refuse un bundle dont l’empreinte diffère de l’empreinte approuvée.
24. La sélection d’une suite de tests exécute ses cas de test descendants dans un ordre déterministe.
25. Le runner produit un code de sortie non nul en cas d’échec et un rapport JUnit valide.
26. Le modèle GitHub Actions monte le bundle en lecture seule, sépare les artefacts et n’expose aucun secret aux PR non approuvées.
27. Le modèle GitLab CI publie les rapports sans exposer de variable protégée aux merge requests non approuvées.
28. Une modification manuelle protégée n’est jamais écrasée silencieusement par une régénération.
29. Le résultat distingue clairement validation de conception et exécution automatisée.
30. Les champs du formulaire affichent un libellé, une aide, un exemple et une règle de validation.
31. Un utilisateur métier peut définir un cas de test sans écrire de YAML.
32. Les modèles de cas de test, types de test, tags, phrases d’intention et environnements sont chargés depuis les fichiers de configuration administrables.
33. Une précondition saisie en texte est transformée en dépendances candidates puis confirmée avant génération du code.
34. Les vérifications système échouées bloquent l’exécution et ne peuvent pas être contournées par le LLM.
35. Les attributs `requirements` et `business_rules` sont conservés dans la définition et l’export du cas de test.
36. Un cas de test de type `performance` compare ses seuils, produit un rapport détaillé et historise sa réussite et sa durée.
37. L’historique persistant d’un cas de test contient uniquement sa date, sa réussite et sa durée.
38. La déclaration d’exécution d’un cas de test permet de le sélectionner pour `on_commit`, `on_merge_request`, `nightly`, `release` ou `manual`.
39. Les transitions de cycle de vie invalides sont refusées et les transitions valides sont inscrites dans le journal d’audit séparé.
40. Un cas de test retiré ou archivé n’est jamais sélectionné par une CI.
41. Une définition confirmée est transformée en modèle intermédiaire validé avant toute génération.
42. Une action non supportée, une assertion absente ou un localisateur interdit bloque la production de l’artefact approuvable.
43. Une régénération détecte les zones personnalisées, préserve les zones compatibles et expose les conflits sans écrasement silencieux.
44. Un cas de test `load` permet de saisir sans YAML son profil, ses opérations, ses utilisateurs virtuels, son débit, sa durée, sa montée en charge et ses seuils.
45. Les paramètres de charge dépassant les limites administratives ou de l’environnement sont refusés.
46. Le MVP valide, versionne et exporte un profil de charge, mais refuse de le présenter comme exécuté sans adaptateur de charge vérifié.
47. Un export manuel contient une documentation fonctionnelle Markdown correspondant au plan de test et aux seules versions approuvées des suites et cas de test sélectionnés, lisible sans consulter les scripts ou la conversation et dépourvue de secret.
48. Le bundle contient deux guides de déploiement distincts, GitLab CI et GitHub Actions, dont les commandes, variables, secrets référencés, rapports et versions correspondent au manifeste et aux modèles de pipeline exportés.
49. Un administrateur configure une instance GitLab d’entreprise, vérifie sa connectivité sans écriture et limite la cible à un projet, une stratégie de branche, un chemin et une référence de secret.
50. Un utilisateur autorisé prévisualise puis confirme manuellement la publication du bundle exact vers GitLab ; un commit traçable ou une merge request est créé sans `force push`, tandis qu’une divergence distante ou une cible hors périmètre bloque l’écriture et produit un résultat explicite.
51. En mode en ligne, deux utilisateurs possédant des appartenances différentes ne peuvent lister, consulter ou modifier que leurs projets autorisés ; la fourniture directe de l’identifiant d’un autre projet est refusée sans révéler son contenu.
52. Le même test de contrat crée plusieurs projets et une arborescence dans les compositions `local` et `online` ; les résultats métier et formats obtenus sont équivalents, tandis que le mode en ligne refuse toute requête sans identité authentifiée.
53. En mode local, un utilisateur crée deux projets, une arborescence et un historique de résultat dans SQLite ; après fermeture et nouvelle composition de l’application sur le même fichier, les identifiants, chemins, ordres et valeurs d’historique sont restaurés, et une nouvelle exécution des migrations ne modifie ni ne duplique les données.
54. Un tutoriel HTML autonome et accessible décrit le lancement local réellement disponible, ses prérequis, sa configuration, des scénarios couvrant uniquement les critères vérifiés et leurs résultats attendus ; il distingue explicitement les commandes de démonstration de l’interface web courante, référence les preuves et passe la validation documentaire ainsi qu’une inspection aux largeurs mobile et desktop.
55. Un administrateur crée puis modifie un profil LLM sans changement de code ; le profil expose le fournisseur, le protocole, l’endpoint, le modèle, les capacités, les paramètres, les limites et la référence de secret, et chaque modification produit une nouvelle version traçable sans altérer une version de cas de test approuvée.
56. Un profil OpenAI configuré avec un endpoint, un modèle et une référence de clé valides passe le contrôle de connexion et de capacités ; une clé absente, un modèle inconnu ou un paramètre non pris en charge produit un échec explicite sans exposer le secret.
57. Un profil Ollama configuré sur une origine autorisée passe le contrôle avec ou sans authentification selon sa configuration ; une origine interdite, un modèle absent ou une capacité manquante empêche son activation avec un diagnostic explicite.
58. Un profil Mistral configuré avec un endpoint, un modèle et une référence de clé valides passe le contrôle de connexion et de capacités ; une authentification refusée, un modèle indisponible ou un paramètre incompatible produit un échec explicite.
59. Les procédures OpenAI, Ollama et Mistral décrivent l’ensemble des étapes de connexion, utilisent uniquement des exemples fictifs, correspondent au schéma de configuration courant et passent le contrôle documentaire automatisé ; tout nouvel adaptateur sans procédure valide ne peut pas être déclaré pris en charge.
60. Démarrée par le point d’entrée réel en mode local, l’application répond à une sonde de santé et sert une interface web qui permet de créer deux projets, un plan de test, une suite de tests et une arborescence de cas de test ; une nouvelle composition sur le même fichier SQLite affiche les mêmes données et identifiants.
61. Le serveur local écoute par défaut uniquement sur l’adresse de boucle locale, accepte un fichier SQLite, une adresse et un port explicitement configurés, crée le répertoire de données nécessaire et refuse le mode `online` avec un diagnostic explicite tant que ses adaptateurs obligatoires ne sont pas disponibles.
62. Depuis l’interface web, un utilisateur renomme, déplace, ordonne puis archive un nœud ; son identifiant reste stable, l’archivage de ses descendants est explicite et l’état complet est restauré après redémarrage.
63. Sans écrire de YAML, un utilisateur définit quatre cas de test respectivement en pas-à-pas, Given/When/Then, tableau d’exemples et checklist ; chaque saisie valide produit une définition canonique consultable, tandis qu’une action sans résultat, un scénario BDD sans résultat, un tableau irrégulier ou une checklist vide est refusé explicitement.
64. Une définition fonctionnelle conserve l’objectif, l’acteur, l’environnement, les préconditions, données, postconditions, exigences, règles métier et déclaration d’exécution ; une modification incrémente sa version et un redémarrage sur le même fichier SQLite restaure exactement le mode, la version et le contenu.
65. Un projet peut afficher les mêmes cas de test dans l’arbre ou dans des vues calculées par tag, exigence, règle métier et mode de spécification, puis les rechercher par texte ; changer de vue ne modifie ni parent, ni ordre, ni identifiant.
66. Un même tableau valide importé en CSV UTF-8 puis en XLSX produit les mêmes colonnes et lignes canoniques ; un fichier trop volumineux, vide, sans itération, avec en-tête vide ou dupliqué, archive invalide, extension inconnue ou formule Excel est refusé avant persistance.
67. À partir de quatre lignes, la stratégie série produit quatre lots d’une itération dans l’ordre source, la stratégie parallèle produit des lots respectant la concurrence maximale et la stratégie aléatoire produit le nombre demandé d’itérations sans doublon ; une même graine reproduit le même ordre.
68. Depuis l’interface web, un utilisateur associe un CSV ou XLSX à un cas de test, choisit série, parallèle ou aléatoire et consulte les colonnes, lignes et lots prévus ; une modification incrémente la version et un redémarrage SQLite restaure exactement les données, l’empreinte et la stratégie sans conserver ni exécuter le fichier actif.
69. Depuis l’accueil, un utilisateur crée un projet, complète un plan de test dans un formulaire distinct puis atteint la page de ce plan ; le fil d’Ariane et les URL conservent les identifiants du projet et du plan après rechargement.
70. Depuis un plan, un utilisateur crée une suite de tests et un dossier, puis crée un cas directement sous chacun d’eux ; la création d’un cas à la racine du plan ou sous un autre cas est refusée explicitement.
71. L’éditeur d’un cas affiche dans cet ordre le contexte, les étapes de test, les données de test et les résultats attendus ; la section des données reste visible sans donnée et un mode pas-à-pas contenant un nombre différent d’étapes et de résultats est refusé.
72. L’utilisateur ouvre un cas depuis l’arbre, enregistre sa définition, revient au plan puis rouvre le même cas ; le projet, le plan, le parent, les sections et les valeurs enregistrées sont restaurés sans confusion avec une suite, un dossier ou un autre cas.

## 13. Stratégie de validation et de développement

Chaque exigence implémentée doit suivre une tranche verticale :

1. formaliser un critère d’acceptation observable ;
2. écrire le cas de test automatisé correspondant et constater son échec ;
3. implémenter le minimum nécessaire ;
4. faire réussir le cas de test ciblé ;
5. exécuter la suite de tests complète ;
6. exercer le véritable point d’entrée concerné ;
7. documenter séparément les dépendances externes indisponibles ;
8. effectuer une revue de sécurité pour toute fonction de navigation, de secret, de génération ou d’exécution.

Les cas de test automatisés doivent couvrir au minimum :

- le domaine sans LLM ni navigateur réels ;
- les états et versions du cycle de conception ;
- les transitions valides et invalides de tous les états, y compris retrait et archivage ;
- la hiérarchie et les déplacements ;
- la matrice des parents autorisés, notamment les cas sous suite ou dossier et l’interdiction des cas à la racine du plan ;
- le parcours des formulaires projet, plan et cas, leurs URL stables et leur fil d’Ariane ;
- les sections séparées des étapes, données et résultats attendus et leur validation croisée ;
- les sept types de test, leur héritage et les incompatibilités ;
- la synthèse factuelle des descriptions ;
- les champs obligatoires, aides, exemples, validations et assistance de la saisie guidée ;
- les attributs simples `requirements` et `business_rules` ;
- les modèles de cas de test et leurs questions de clarification ;
- le catalogue de phrases d’intention et sa configuration ;
- la validation des fichiers de configuration administrables ;
- les cibles GitLab d’entreprise, leurs restrictions de projet, branche, chemin, TLS et référence de secret ;
- les préconditions textuelles, leur confirmation et la résolution codée des dépendances ;
- le blocage des contrôles système échoués ;
- les données de test, profils d’environnement et leurs références ;
- les imports CSV/XLSX, leurs limites, empreintes, stratégies série,
  parallèle et aléatoire reproductible ;
- la déclaration de sélection CI et le filtrage par déclaration ;
- l’historique strictement limité à la date, la réussite et la durée ;
- les seuils de performance et le type `performance` ;
- la séparation des profils LLM ;
- le schéma, le versionnement et la validation des paramètres des profils LLM ;
- les adaptateurs OpenAI, Ollama et Mistral, y compris authentification, modèle absent, capacité manquante, délai et erreur réseau ;
- les contrôles de connexion sans contenu métier et sans exposition des secrets ;
- les contrats d’adaptateurs ;
- les réponses LLM invalides ;
- les politiques de destination ;
- la génération déterministe d’un artefact candidat à partir d’un brouillon structuré ;
- le modèle intermédiaire, la correspondance actions/code, les localisateurs et les assertions (`GEN-001` à `GEN-006`) ;
- les fixtures, Page Objects, personnalisations, conflits de régénération et empreintes (`GEN-007` à `GEN-013`) ;
- les contrôles et limites de l’assistance LLM à la génération (`GEN-014`) ;
- la définition et la validation de profils de charge paramétrés (`LOAD-001` à `LOAD-006`) ;
- l’export, les limites de sécurité, les résultats et l’assistance LLM des cas de test de charge (`LOAD-007` à `LOAD-011`) ;
- l’invalidation de la validation après toute modification du cas de test structuré ou du script ;
- le contrat du bundle ;
- la génération de la documentation fonctionnelle et son absence d’éléments non approuvés ou secrets ;
- la cohérence des guides de déploiement GitLab CI et GitHub Actions avec le manifeste et les modèles exportés ;
- la prévisualisation, la confirmation, l’audit et les conflits de publication manuelle vers GitLab ;
- les codes de sortie et rapports du runner ;
- l’exécution E2E sur une cible de démonstration contrôlée ;
- les modèles GitHub Actions et GitLab CI.
- l’isolation des projets entre utilisateurs et le refus des identifiants non autorisés ;
- la parité des cas d’usage entre les compositions locale et en ligne ;
- les conflits de modification concurrente en mode en ligne.
- la cohérence des tutoriels HTML avec les capacités réellement vérifiées, les commandes et les limites courantes.

## 14. Spécifications détaillées de génération et de charge

Cette section complète les exigences `EF-*` et `ENF-*`. Les identifiants `GEN-*` et `LOAD-*` sont obligatoires pour le suivi de conception, d’implémentation et de validation. Toute tâche de développement doit référencer au moins un identifiant de spécification et un critère d’acceptation associé.

### 14.0 Registre des identifiants

| Famille | Identifiants | Objet | Statut de référence |
|---|---|---|---|
| Exigences fonctionnelles | `EF-001` à `EF-017` | fonctions de conception, génération, validation et exécution | cadrées |
| Exigences non fonctionnelles | `ENF-001` à `ENF-013` | sécurité, isolation, portabilité, observabilité, déploiements et CI | cadrées |
| Génération | `GEN-001` à `GEN-014` | modèle intermédiaire, traduction, code, personnalisation et empreintes | cadrées ; implémentation à suivre |
| Charge | `LOAD-001` à `LOAD-011` | profils, paramètres, seuils, export et futur adaptateur de charge | définition/export MVP ; exécution post-MVP |
| Documentation | `DOC-001` à `DOC-007` | vérité d’implémentation, scénarios, configuration, lancement, connexions LLM et validation HTML | cadrée ; à maintenir avec chaque tranche |
| Acceptation | `ACC-001` à `ACC-072` | vérifications observables du MVP | à transformer en cas de test |

Une exigence ne peut être marquée comme implémentée que lorsqu’un cas de test ou une démonstration vérifie son comportement. Les statuts de développement (`à faire`, `en cours`, `implémentée`, `vérifiée`) doivent être suivis dans l’outil de gestion du projet, sans modifier l’identifiant stable de la spécification.

### 14.1 Génération des scripts de test

#### GEN-001 — Entrée de génération

Le générateur reçoit uniquement une version structurée confirmée du cas de test, le modèle de cas de test appliqué, les configurations administratives validées et les versions de générateur déclarées. Il ne reçoit pas directement l’historique brut de conversation.

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

Une action non supportée doit être signalée comme telle et empêcher l’approbation du script, plutôt que d’être remplacée par une approximation silencieuse.

#### GEN-005 — Choix et stabilité des localisateurs

Le générateur choisit les localisateurs dans l’ordre suivant : rôle et nom accessible, libellé, texte observable, attribut de test configuré, puis sélecteur CSS stable. Il doit conserver le localisateur retenu dans la représentation structurée et indiquer son niveau de fragilité.

Les localisateurs basés sur une position, un identifiant généré, une coordonnée ou une référence temporaire d’exploration sont interdits dans un artefact approuvable, sauf dérogation explicitement justifiée et visible.

#### GEN-006 — Génération des assertions

Chaque résultat attendu confirmé doit devenir au moins une assertion observable, sauf s’il est explicitement marqué comme information non vérifiable. Le générateur doit refuser un cas de test qui ne contient aucune assertion fonctionnelle ou de performance.

Les assertions doivent être indépendantes des messages du LLM. Elles portent sur l’interface, l’URL autorisée, une réponse observable, une donnée affichée, un état ou une mesure déclarée.

#### GEN-007 — Fixtures, données et secrets

Le générateur sépare :

- les fixtures reproductibles non secrètes ;
- les données paramétrables ;
- les références de secrets ;
- les valeurs fournies uniquement par l’environnement d’exécution.

Aucune valeur secrète ne doit être écrite dans le code, le bundle, le manifeste, le prompt, les captures ou les journaux. Une fixture manquante bloque la génération ou l’exécution selon le moment où elle est détectée.

#### GEN-008 — Composants et Page Objects

Un parcours commun peut être factorisé en fixture, fonction ou Page Object uniquement lorsqu’au moins deux cas de test le réutilisent ou lorsqu’une frontière d’écran claire le justifie. Chaque composant possède un identifiant et une version. Le générateur doit privilégier une structure simple et lisible plutôt qu’une abstraction anticipée.

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

Chaque fichier généré doit indiquer l’identifiant du cas de test et la version de génération, sans inclure le prompt complet ni de secret.

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

### 14.2 Paramétrage des cas de test de charge

#### LOAD-001 — Type de test de charge

`load` est un type de test distinct de `performance`. Il décrit une charge appliquée à une ou plusieurs opérations autorisées. Le type doit être sélectionnable dans l’interface et disponible dans `config/test-types.yaml`.

#### LOAD-002 — Profil de charge

Un cas de test de type `load` référence un profil de charge administrable dans `config/load-profiles.yaml`. Un profil possède au minimum :

- un identifiant et un libellé métier ;
- un moteur ou adaptateur de charge ;
- une version de protocole ;
- des opérations autorisées ;
- des limites maximales d’utilisateurs, de débit et de durée ;
- les métriques collectées ;
- les seuils par défaut ;
- les environnements autorisés.

#### LOAD-003 — Paramètres obligatoires

Un cas de test de charge doit pouvoir paramétrer sans YAML :

- le profil de charge ;
- les opérations ou parcours ciblés ;
- le nombre d’utilisateurs virtuels ;
- le débit cible ou la fréquence d’arrivée ;
- la durée de charge ;
- la montée en charge par paliers ;
- le temps de stabilisation ;
- les données de test et profils d’environnement ;
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

Un cas de test de charge doit pouvoir définir des seuils sur :

- débit atteint ;
- durée minimale d’exécution ;
- taux d’erreur maximal ;
- temps de réponse moyen ;
- percentile maximal, notamment P95 ou P99 ;
- nombre minimal d’opérations réussies.

Les seuils font partie de la version du cas de test. Un dépassement produit un échec explicite et ne peut pas être transformé en simple avertissement par le LLM.

#### LOAD-007 — Artefact et moteur d’exécution

La conception exporte un profil de charge versionné et un scénario indépendant de l’interface web. Le runner sélectionne un adaptateur compatible avec le profil. Le moteur exact peut être configuré par l’administrateur ; il ne doit pas être imposé aux fonctionnels métier.

Le script Playwright d’un cas de test fonctionnel ne doit pas être utilisé implicitement pour générer une charge concurrente. Un adaptateur de charge dédié est obligatoire pour l’exécution réelle.

#### LOAD-008 — Sécurité et limites

Un cas de test de charge doit être limité à un environnement explicitement autorisé. Le runner applique des plafonds sur utilisateurs virtuels, débit, durée, volume de données et origines. Les cas de test de charge sur une production ou une cible non autorisée sont refusés.

Le profil de charge ne contient pas de secret. Les secrets nécessaires sont référencés et injectés uniquement par l’environnement d’exécution.

#### LOAD-009 — Résultats

Le rapport détaillé d’un cas de test de charge contient les métriques et seuils comparés. L’historique synthétique conserve uniquement la date, la réussite et la durée, comme pour les autres cas de test. Les métriques détaillées sont conservées dans les artefacts de l’exécution selon la politique de conservation.

#### LOAD-010 — Périmètre MVP

Le MVP permet de définir, valider la cohérence, versionner et exporter un cas de test de charge paramétré. L’exécution par un moteur de charge dédié est une capacité activable après le MVP et ne doit pas être présentée comme disponible tant que l’adaptateur correspondant n’est pas installé et vérifié.

#### LOAD-011 — Assistance LLM

Le LLM de conception peut aider à choisir un profil, proposer une charge initiale, identifier les opérations, poser les questions manquantes et suggérer des seuils. Toute valeur proposée doit être confirmée par l’utilisateur. Le LLM ne peut ni lancer une charge ni augmenter les paramètres au-delà des limites administrées.

### 14.3 Documentation HTML de l’implémentation

#### DOC-001 — Source de vérité

Toute documentation d’utilisation doit être produite à partir des spécifications, du tableau d’avancement, des preuves d’exécution, des points d’entrée et de la configuration réellement présents. Une exigence cadrée mais non vérifiée ne doit jamais être présentée comme disponible.

#### DOC-002 — État et limites

Chaque guide indique sa date de vérification, la version ou l’état du produit, le mode concerné et les fonctions encore planifiées. Le tutoriel local doit distinguer les commandes de démonstration de l’interface FastAPI réellement disponible et signaler les capacités web ou de déploiement encore planifiées.

#### DOC-003 — Scénarios d’utilisation

Chaque scénario documenté précise un objectif utilisateur, les prérequis, les commandes ou actions exactes, le résultat observable et les identifiants `EF-*`, `ENF-*` et `ACC-*` vérifiés. Un scénario ne peut dépendre silencieusement d’une fonction planifiée.

#### DOC-004 — Configuration

La documentation inventorie les paramètres réellement lus par le produit, leur portée locale ou en ligne, leur valeur par défaut, leur caractère sensible et les erreurs associées. Elle ne doit contenir aucun secret réel ni laisser croire qu’un fichier de configuration futur est déjà pris en charge.

#### DOC-005 — Installation et lancement

Les commandes de prérequis, lancement, arrêt et nettoyage sont copiables et indiquent leur répertoire d’exécution. Les variantes Windows et POSIX sont séparées lorsqu’elles diffèrent. Chaque commande essentielle est exercée sur un environnement représentatif avant publication.

#### DOC-006 — HTML autonome et validation

Le guide HTML utilise une structure sémantique, une navigation, un lien d’évitement, des ancres stables, un contraste lisible, une mise en page responsive et une feuille d’impression. Il ne dépend d’aucune ressource réseau pour son contenu essentiel. Un validateur automatique contrôle sa structure, ses liens internes et ses marqueurs de traçabilité ; une inspection visuelle couvre au minimum 390 et 1440 pixels de largeur.

#### DOC-007 — Procédures de connexion aux LLM

La documentation doit couvrir chaque adaptateur LLM pris en charge et respecter `EF-003.2`. Le contrôle documentaire vérifie la présence d’une procédure par fournisseur, les champs obligatoires, la cohérence des exemples avec le schéma de profil courant, l’absence de secret réel, les liens vers les sources officielles et la présence d’un diagnostic pour chaque catégorie d’échec de connexion. Une modification du schéma d’un profil ou d’un adaptateur rend obligatoire la mise à jour et la revalidation de sa procédure dans la même livraison.

## 15. Questions ouvertes après le cadrage du MVP

Les points suivants restent à décider pendant les premières tranches TDD :

1. Quel protocole et quel fournisseur d’identité seront officiellement supportés en premier par l’adaptateur d’authentification en ligne ?
2. Quelle cible de démonstration contrôlée servira de référence E2E ?
3. Quel format précis décrira la hiérarchie et le cas de test structuré dans le bundle ?
4. Comment identifier les zones de code personnalisées à préserver lors d’une régénération ?
5. Quelle profondeur maximale l’interface autorisera-t-elle dans l’arborescence ?
6. Quelle politique de conservation s’appliquera aux captures, conversations et traces ?
7. Quelles versions minimales des protocoles OpenAI, Ollama et Mistral seront retenues pour les cas de test de compatibilité du MVP ?
8. Quelle implémentation de politique réseau appliquera l’autorisation explicite des origines dans les environnements Docker, Podman et CI ?

## 16. Traçabilité des besoins initiaux

Cette spécification repose sur les besoins explicitement exprimés :

- développer un outillage web ;
- fournir les mêmes fonctions en déploiement local monoposte et en déploiement web en ligne multi-utilisateur et multi-projet ;
- faire interagir l’utilisateur avec un LLM configurable pendant la conception ;
- configurer indépendamment des profils OpenAI, Ollama et Mistral sans modification du code ;
- documenter et valider toutes les procédures de connexion aux fournisseurs LLM pris en charge ;
- élaborer des plans de test et définir des suites et cas de test fonctionnels à partir des indications de l’utilisateur et de captures d’écran ;
- ranger les cas de test hiérarchiquement dans des suites de tests ;
- lancer les cas de test individuellement pendant leur conception ;
- mettre à jour automatiquement une description synthétique et factuelle ;
- générer du code réutilisable, maintenable et personnalisable ;
- générer une documentation fonctionnelle lisible et des guides de déploiement GitLab CI et GitHub Actions avec chaque export ;
- publier manuellement un plan de test, ses suites et leurs scripts vers une cible GitLab d’entreprise administrée ;
- exécuter ces scripts indépendamment de la conception ;
- réserver le LLM d’exécution à des cas exceptionnels ;
- configurer séparément les LLM de conception et d’exécution ;
- faciliter le déploiement et l’intégration à GitHub Actions et GitLab CI.

Les exigences de sécurité, de versionnement, de validation humaine, d’isolation, de portabilité et d’audit sont dérivées de ces besoins afin de rendre la capacité contrôlable et exploitable.
