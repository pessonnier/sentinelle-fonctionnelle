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
- **profil d’approche de test** : configuration versionnée qui précise les niveaux et types de test, les techniques de conception de tests, l’usage de l’analyse des risques, la stratégie d’automatisation, les éléments de preuve attendus et les instructions applicables à la génération ; un plan de test référence exactement un profil et une version ;
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
- **trace d’exécution** : artefact technique horodaté qui permet de reconstituer le déroulement d’une exécution ; dans ce document, une trace désigne soit une trace Playwright contenant les actions, états du navigateur, journaux et échanges réseau, soit une archive HAR décrivant les échanges HTTP ;
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
4. il produit un code de sortie, des journaux, un rapport JUnit, des preuves et, lorsque la politique de capture l’exige, des traces Playwright et HAR ;
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

Un cas de test en brouillon, en conception, candidat ou retiré n’est pas
sélectionnable par une CI. Un cas de test candidat peut être lancé
individuellement. Un cas approuvé peut être inclus dans une vérification locale
et une sélection de publication ; un cas actif est en plus autorisé dans les
suites automatisées de la CI. Les transitions sont enregistrées dans un journal
d’audit distinct de l’historique synthétique des résultats.

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
| Profil d’approche de test du plan | oui | choix dans la liste des profils YAML actifs, ex. « Tests fonctionnels orientés risques » | identifiant et version existants ; aucune saisie libre | recommandation justifiée parmi les profils actifs |
| Risques, critères d’entrée et critères de sortie | oui | listes structurées | au moins un critère de sortie mesurable | proposition soumise à confirmation |
| Ressources, contraintes et ordonnancement du plan | non | textes courts ou listes | valeurs cohérentes | proposition facultative |
| Politique de traces par défaut du plan | non | formats `playwright` et/ou `har`, avec `off`, `on`, `on-failure` ou `on-first-retry` | formats et politique autorisés | aucune |
| Cible de développement par défaut du plan | non | liste des cibles GitLab ou GitHub administrées | cible active et autorisée pour le projet | aucune |
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
| Politique de traces du cas | non | héritage du plan ou sélection des formats et du mode de capture | formats et politique autorisés | aucune |
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
2. la page du projet liste ses **plans de test** et fournit un formulaire de plan distinct couvrant son objectif, son périmètre, le choix d’un profil d’approche de test, sa cible, ses risques, ses critères, ses ressources, ses contraintes et son ordonnancement ;
3. la page du plan affiche l’arborescence et deux actions distinctes : créer une **suite ou un dossier**, puis créer un **cas de test** sous l’un de ces parents ;
4. la page du cas de test sépare visuellement le contexte, les **étapes de test**, les **données de test** et les **résultats attendus** ;
5. un fil d’Ariane rappelle en permanence `Projet / Plan / Suite ou dossier / Cas` et permet de revenir au niveau précédent sans perdre les données enregistrées.

Le formulaire de création d’un cas exige la sélection d’une suite ou d’un dossier parent. Tant qu’aucun parent compatible n’existe, l’action de création du cas est indisponible et l’interface indique l’étape préalable. Chaque formulaire conserve les valeurs invalides lors de l’affichage d’une erreur, associe le message au champ concerné et ne crée aucun objet partiel.

L’éditeur du cas de test présente les quatre sections dans un ordre stable. Les données de test restent facultatives, mais leur section est toujours visible. Pour le mode pas-à-pas, chaque étape possède exactement un résultat attendu placé au même rang ; un nombre différent d’étapes et de résultats bloque l’enregistrement.

### 3.5.2 Configuration administrable

Les administrateurs de l’outillage peuvent adapter le vocabulaire et les guides sans modifier le code de l’application. Les fichiers de configuration peuvent définir :

- les types de test disponibles ;
- les profils d’approche de test et leurs versions ;
- les modèles de cas de test ;
- les phrases décrivant les intentions fonctionnelles ;
- les valeurs de tags autorisées ;
- les environnements et profils de données disponibles ;
- les profils LLM de conception et d’exécution ;
- les cibles GitLab et GitHub autorisées pour la publication manuelle vers un
  environnement de développement ;
- les aides, exemples et champs obligatoires par contexte.

Chaque entrée de configuration possède un identifiant stable, un libellé visible, une description destinée au métier et, lorsque nécessaire, une représentation technique non visible dans le formulaire.

Le MVP prévoit au minimum les fichiers administrables suivants :

```text
config/test-types.yaml          # types de test, libellés et aides
config/test-approaches.yaml     # profils versionnés d’approche de test
config/test-models.yaml         # modèles de cas de test et questions LLM
config/test-intents.yaml         # phrases d’intention fonctionnelle
config/tags.yaml                 # tags sélectionnables
config/environments.yaml         # environnements, URLs et origines autorisées
config/data-profiles.yaml        # profils de données et fixtures
config/load-profiles.yaml        # profils de charge paramétrés
config/llm-profiles.yaml         # fournisseurs, endpoints, modèles et paramètres LLM
config/git-targets.yaml          # dépôts GitLab et GitHub autorisés
```

Un profil d’approche de test est décrit en YAML et contient au minimum :

```yaml
id: functional-risk-based
versions:
  - version: 1
    name: Tests fonctionnels orientés risques
    description: Priorise les parcours selon la probabilité et l’impact.
    test_levels: [test système, test d’acceptation]
    test_types: [test fonctionnel, test de régression]
    test_design_techniques:
      - partitionnement en classes d’équivalence
      - analyse des valeurs limites
      - tables de décision
    risk_based: true
    automation_strategy: Automatiser les parcours critiques et répétables.
    evidence_requirements: [résultat de chaque assertion, capture en cas d’échec]
    generation_instructions:
      - relier chaque cas à un risque identifié
      - expliciter des résultats attendus observables
    enabled: true
```

L’écran de configuration des approches de test doit permettre de consulter les
profils existants, de créer un profil et d’enregistrer la modification d’un
profil. Une création utilise un identifiant stable unique et commence à la
version `1`. Une modification conserve cet identifiant et ajoute une nouvelle
version au fichier YAML ; elle ne réécrit ni ne supprime les versions déjà
référencées par des plans. La désactivation rend uniquement la dernière version
indisponible pour de nouveaux choix.

Les formulaires de création et de modification d’un plan présentent une liste
des dernières versions actives. Ils n’acceptent aucune description libre de
l’approche. Le plan conserve l’identifiant et la version sélectionnés afin que
sa génération et ses exports restent reproductibles après une évolution du
catalogue. Un profil absent, une version inconnue, une structure YAML invalide
ou une sélection désactivée bloque l’enregistrement avec un diagnostic
explicite.

Lors de la migration d’une version antérieure, une description libre existante
est conservée comme donnée historique et le plan référence le profil désactivé
`legacy-free-text` (« Approche historique à requalifier »). Le système ne
déduit jamais silencieusement un profil actif à partir de ce texte. La prochaine
modification du plan exige la sélection explicite d’un profil actif.

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

Une cible Git de développement peut par exemple déclarer :

```yaml
id: enterprise-quality
label: GitLab entreprise - Qualité
provider: gitlab
environment: development
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

Une cible GitHub utilise le même contrat avec `provider: github`, un dépôt
`owner/repository` et un mode `pull_request`. La cible désigne le dépôt, la
branche et le chemin qui alimentent l’environnement de développement ; elle
n’autorise pas à publier vers une autre branche ou un autre environnement.

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

Il décrit les parcours métier, fournit des exemples visuels, organise les cas de test, examine les scénarios proposés et valide chaque cas de test sans devoir écrire l’intégralité du script. Il peut résoudre un plan en une sélection de cas, la lancer depuis son poste, examiner ses résultats puis publier la sélection vérifiée vers l’environnement de développement autorisé.

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
6. Il analyse les pages nécessaires ; le système lui présente les champs, boutons,
   liens et éléments vérifiables pouvant être référencés dans les étapes.
7. Il ajoute et ordonne des cartes pas-à-pas contenant chacune un prérequis local,
   une action typée et une validation observable.
8. Le LLM de conception reçoit la structure courante, les observations de page et
   les règles applicables. Il pose les questions nécessaires, signale les cibles ou
   données manquantes et propose uniquement des modifications structurées.
9. L’utilisateur accepte, corrige ou refuse chaque proposition. Le système met à
   jour la représentation structurée et la description synthétique.
10. L’utilisateur examine la structure de génération complète, résout les
    hypothèses restantes puis la confirme explicitement.
11. Le générateur produit un artefact candidat Playwright et calcule son empreinte.
12. L’utilisateur lance individuellement cet artefact candidat en mode validation.
13. Le runner isolé exécute exactement le code candidat et conserve les preuves.
14. L’utilisateur corrige le cas de test ou personnalise le script si nécessaire,
    ce qui invalide la validation précédente, puis le relance.
15. Il approuve une version immuable liant le cas de test structuré, le script
    validé et son empreinte.

### 5.2 Exécuter une suite dans une CI

1. La CI récupère le dépôt ou le paquet de suites et cas de test approuvés.
2. Elle fournit la configuration de cible et les secrets par variables ou fichiers protégés.
3. Elle lance le runner par une commande ou une image conteneur versionnée.
4. Le runner sélectionne une suite de tests, un tag ou un cas de test ; un dossier de classement ne constitue pas une cible d’exécution.
5. Il exécute le code sans appeler le service web de conception.
6. Il utilise le profil LLM d’exécution uniquement si un cas de test l’autorise explicitement.
7. Il publie un code de sortie standard, un rapport JUnit et les artefacts configurés.
8. GitHub Actions, GitLab CI ou l’autre orchestrateur décide du succès du pipeline à partir du code de sortie.

### 5.3 Vérifier localement, sélectionner et publier un plan

1. Depuis la page d’un plan, l’utilisateur ouvre le mode **Sélection et
   publication**.
2. Le système résout la version du plan en suites et cas de test approuvés, puis
   affiche l’arbre avec les versions, dépendances, tags et derniers résultats.
3. L’utilisateur inclut ou exclut des suites et cas de test, choisit
   l’environnement logique de vérification et la politique de traces.
4. Le système affiche la procédure de test résultante et signale les
   dépendances manquantes, versions non publiables ou exclusions incohérentes.
5. L’utilisateur lance manuellement la sélection depuis son poste au moyen du
   runner local, installé ou conteneurisé.
6. Le runner exécute les cas sélectionnés, sans considérer le plan comme une
   unité exécutable, et produit les résultats, journaux et traces configurés.
7. L’utilisateur examine le résultat de chaque cas. Il corrige et relance les
   échecs, ou les exclut explicitement de la sélection à publier.
8. Lorsque tous les cas retenus ont réussi sur leurs versions exactes, le
   système fige une sélection de publication et l’empreinte du bundle associé.
9. L’utilisateur choisit une cible de développement GitLab ou GitHub
   administrée, consulte le dépôt, la branche, le chemin, la liste des fichiers
   et le diff.
10. Après confirmation explicite, le système publie exactement le bundle
    vérifié sur une branche autorisée et retourne le commit ainsi que, selon la
    cible, la merge request ou la pull request.

## 6. Exigences fonctionnelles

### 6.1 Conception et organisation des plans, suites et cas de test

Cette partie décrit les fonctions utilisées par les fonctionnels métier pour définir, comprendre, organiser et valider des plans, suites et cas de test. Elle ne lance pas directement les scripts dans le processus de l’application de conception.

### EF-001 — Gestion des projets

Le système doit permettre de créer, consulter, modifier et archiver un projet contenant au minimum un nom, une description, une cible web et une politique de sécurité. Un projet peut contenir plusieurs plans de test indépendants.

Un plan de test doit contenir au minimum :

- un nom, des objectifs et un périmètre explicite ;
- une base de test et les éléments de l’objet de test concernés ;
- la référence et la version d’un profil d’approche de test actif comprenant les niveaux, types, techniques et priorités retenus ;
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
- modifier le nom, la description, la cible web et la politique de sécurité
  depuis le catalogue, sans réécrire les cibles propres aux plans existants ;
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

### EF-001.3 — Présentation cohérente, ajout progressif et thèmes

Les pages qui présentent un catalogue d’objets suivent un patron commun. La liste
occupe d’abord toute la largeur disponible. Le formulaire de création n’est pas
affiché dans une colonne latérale permanente : un bouton `+`, placé immédiatement
sous la liste, le déplie sur toute la largeur. Le libellé du bouton nomme l’objet
créé, par exemple **Ajouter un projet** ou **Ajouter un profil de génération**.

Le formulaire est replié par défaut. Son ouverture place le focus sur son premier
champ utilisable. Le même bouton et la touche Échap permettent de le replier sans
réinitialiser les valeurs déjà saisies. Les formulaires de modification restent
associés à l’objet concerné dans la liste. Dans une arborescence, un ajout enfant
reste placé auprès de son parent ; il applique les mêmes principes de bouton `+`,
de dévoilement progressif et de conservation de la saisie. Le comportement et
l’ordre de lecture doivent rester identiques sur ordinateur et sur mobile.

L’en-tête de toutes les pages de Sentinelle propose un choix de thème parmi une
liste fermée et diversifiée : **Forêt**, **Océan**, **Prune**, **Coucher de soleil**,
**Graphite**, **Contraste élevé** et **Défense — ministère des Armées**. Le choix
modifie les couleurs par des variables
de présentation communes, conserve les états de focus visibles et un contraste
lisible, puis est mémorisé dans le stockage local du navigateur. Il n’est pas une
donnée métier, n’est pas enregistré en base, ne modifie ni les prompts ni les
exports et revient à **Forêt** lorsque le stockage est indisponible ou invalide.
La cible RH de démonstration conserve volontairement son thème indépendant et son
HTML hétérogène, car elle est une application testée et non une page de Sentinelle.

Chaque thème possède un identifiant technique stable, un libellé, une palette de
jetons sémantiques, une pile typographique, des règles de contraste et, s’il est
institutionnel, des ressources de marque locales et leur provenance :

| Identifiant | Libellé | Intention visuelle |
|---|---|---|
| `forest` | Forêt | palette sobre verte, thème de repli |
| `ocean` | Océan | bleus lisibles sur fonds clairs |
| `plum` | Prune | violets doux et contrastés |
| `sunset` | Coucher de soleil | tons chauds rouge-orangé |
| `graphite` | Graphite | neutres gris et faible saturation |
| `high-contrast` | Contraste élevé | séparateurs, textes et focus renforcés |
| `defense` | Défense — ministère des Armées | identité de l’État et symbolique du ministère |

Le thème `defense` reprend le [bloc-marque du DSFR](https://www.systeme-de-design.gouv.fr/version-courante/fr/composants/bloc-marque/code-du-bloc-marque)
avec l’intitulé officiel **Ministère des Armées et des Anciens combattants** observé
sur [defense.gouv.fr](https://www.defense.gouv.fr/). Il utilise le Bleu France
`#000091`, le Rouge Marianne `#e1000f`, les neutres clairs du
[Système de Design de l’État](https://www.systeme-de-design.gouv.fr/version-courante/fr/fondamentaux/couleurs),
la police Arial comme substitution autorisée lorsque Marianne n’est pas distribuée,
ainsi que le pictogramme Rafale filaire bleu et rouge publié par le ministère. Le
bloc-marque et le pictogramme sont livrés localement, sans appel réseau au chargement,
conservent leurs proportions et leurs couleurs, et ne doivent pas être redessinés,
recolorés, déformés ou employés comme indication d’un résultat de test.

La marque de l’État et le DSFR étant réservés aux services et sites autorisés de
l’État, l’activation du thème `defense` en production relève de la configuration et
de la responsabilité de l’entité habilitée. Le thème n’accorde aucune affiliation,
ne modifie pas le contenu métier et ne doit pas être appliqué à l’application cible,
aux captures de celle-ci ou aux artefacts exportés. Toute mise à jour du bloc-marque,
de l’intitulé ministériel ou du pictogramme doit conserver la source, la version et
la date de vérification.

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

L’interface web fournit une page de catalogue des projets, une page d’arborescence
complète par projet et un éditeur détaillé par cas de test. Une URL stable identifie
chaque projet, plan et cas ; un rechargement ou un redémarrage doit restaurer le
même contexte. Les anciennes URL d’un plan peuvent rester disponibles pour les
vues calculées et les favoris, mais le parcours principal ne doit plus imposer une
page intermédiaire séparée.

Le catalogue porte l’édition du projet à côté de chaque projet. La page du projet
affiche et permet d’éditer dans une même arborescence les quatre niveaux **Plan de
test → Dossier → Suite → Cas de test**. Le plan est une racine visible ; son bouton
`+` crée un dossier, celui du dossier crée une suite et celui de la suite crée un
cas. Chaque ligne différencie sa nature, expose ses actions au même emplacement et
conserve son identifiant. L’édition détaillée du contenu d’un cas reste dans la page
du cas, qui affiche séparément :

- son contexte, son objectif, son acteur, ses préconditions et postconditions ;
- ses étapes ordonnées ;
- ses données référencées ou importées ;
- ses résultats attendus, alignés avec les étapes lorsque le mode le permet.

La navigation arrière, le fil d’Ariane et les liens de l’arbre doivent conserver les identifiants métier plutôt que reconstruire le contexte à partir des noms. Les commandes de renommage, déplacement et archivage restent disponibles au niveau du plan sans encombrer le formulaire principal du cas.

### EF-002.2 — Profils d’approche de test

L’application doit fournir un catalogue administrable de profils d’approche de
test initialisé à partir de descriptions YAML livrées avec le produit. Chaque
version de profil possède un identifiant stable, un numéro de version, un
libellé, une description métier, un état actif ou désactivé, des niveaux et
types de test, des techniques de conception de tests, un indicateur d’approche
fondée sur les risques, une stratégie d’automatisation, des exigences relatives
aux éléments de preuve et des instructions de génération.

Dans les formulaires d’un plan de test, l’approche de test est obligatoirement
choisie dans la liste des dernières versions actives. Le plan persiste
l’identifiant et la version du profil sélectionné. Une modification ultérieure
du profil ne modifie pas silencieusement les plans existants.

L’écran de configuration doit permettre à un administrateur :

- de consulter les profils et leur état ;
- de créer et enregistrer un nouveau profil à la version `1` ;
- de modifier un profil existant en créant la version suivante ;
- d’activer ou de désactiver la nouvelle version ;
- de conserver dans le YAML toutes les versions encore référencées.

La validation doit refuser les identifiants dupliqués, les numéros de version
dupliqués, les champs obligatoires vides, les listes de nature incorrecte et les
documents YAML dont la version de schéma n’est pas prise en charge.

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

Pour Ollama, le diagnostic distingue explicitement :

1. la disponibilité du service sur l’origine configurée ;
2. la présence du nom exact du modèle ;
3. une inférence réelle avec le contexte et le contrat de sortie du profil.

Un succès obtenu avec un contexte réduit constitue seulement un diagnostic
matériel. Il ne valide pas un profil déclarant un contexte supérieur. Le bouton
de contrôle reste utilisable avant activation ; un délai de chargement, une
sortie non JSON ou un contrat invalide laisse le profil désactivé et indique
l’étape en échec.

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

Avant tout appel au LLM, l’application calcule de manière déterministe les
informations manquantes à partir de l’intention fonctionnelle sélectionnée et de
la structure courante. Chaque question affiche son utilité et la zone structurée
qui recevra la réponse. Une information déjà présente ne doit pas être demandée
de nouveau.

Les pages HTML analysées sont transmises sous forme d’un inventaire borné et
normalisé. Pour chaque élément, l’assistant distingue les actions compatibles,
les validations observables et les exemples de valeurs autorisés. Le HTML brut
ne constitue ni une instruction pour le LLM ni une autorisation de modifier le
cas. L’utilisateur peut utiliser une référence proposée sans exposer ni
fabriquer directement un sélecteur CSS.

Le dialogue est attaché au cas et restauré après redémarrage. Un échange
explicite transmet au LLM uniquement :

- le brouillon structuré courant ;
- l’intention fonctionnelle versionnée ;
- le diagnostic déterministe des informations manquantes ;
- l’inventaire minimisé des champs HTML, sans HTML brut ni localisateur ;
- les huit derniers messages au maximum ;
- un contrat fermé de réponse.

La réponse comporte une version de schéma, au plus huit questions et au plus
douze opérations `add` ou `replace`. Chaque opération possède un identifiant,
un chemin autorisé, une valeur, un libellé et une justification. Les chemins
modifiables sont limités à l’objectif, l’acteur, les listes métier, le profil
d’acteur, les références de fixtures ou de secrets, la préparation, le
nettoyage, les hypothèses et les champs éditables des étapes. Les pages
analysées, les profils LLM et de génération et le marqueur `confirmed` ne sont
jamais modifiables par une réponse LLM.

Le système conserve l’empreinte du brouillon qui a produit chaque proposition.
Si le brouillon change avant la décision, l’acceptation est refusée et
l’utilisateur doit relancer le dialogue. Une sortie inconnue, mal typée, trop
longue ou visant un chemin interdit est refusée avant la persistance du message
utilisateur.

Le dialogue est attaché au cas et restauré après redémarrage. Un échange
explicite transmet au LLM uniquement :

- le brouillon structuré courant ;
- l’intention fonctionnelle versionnée ;
- le diagnostic déterministe des informations manquantes ;
- l’inventaire minimisé des champs HTML, sans HTML brut ni localisateur ;
- les huit derniers messages au maximum ;
- un contrat fermé de réponse.

La réponse comporte une version de schéma, au plus huit questions et au plus
douze opérations `add` ou `replace`. Chaque opération possède un identifiant,
un chemin autorisé, une valeur, un libellé et une justification. Les chemins
modifiables sont limités à l’objectif, l’acteur, les listes métier, le profil
d’acteur, les références de fixtures ou de secrets, la préparation, le
nettoyage, les hypothèses et les champs éditables des étapes. Les pages
analysées, les profils LLM et de génération et le marqueur `confirmed` ne sont
jamais modifiables par une réponse LLM.

Le système conserve l’empreinte du brouillon qui a produit chaque proposition.
Si le brouillon change avant la décision, l’acceptation est refusée et
l’utilisateur doit relancer le dialogue. Une sortie inconnue, mal typée, trop
longue ou visant un chemin interdit est refusée avant la persistance du message
utilisateur.

### EF-005 — Mise à jour de la description

Après chaque échange accepté ou modification structurée d’un cas de test, le système doit proposer une nouvelle description synthétique et factuelle.

La mise à jour doit :

- reposer sur la version structurée courante plutôt que sur le seul dernier message ;
- préserver les faits confirmés ;
- retirer les éléments devenus faux ou obsolètes ;
- éviter les formulations spéculatives ;
- être visible avant l’enregistrement de la nouvelle version ;
- rester modifiable par l’utilisateur.

La synthèse n’est pas copiée depuis la prose du LLM. Après une décision, elle
est reconstruite par une fonction déterministe depuis l’objectif, l’acteur, les
préconditions et le dernier résultat attendu observable du brouillon accepté.
Une opération refusée et une question sans réponse ne peuvent donc pas apparaître
dans la description. L’utilisateur peut ensuite corriger cette description ;
une nouvelle proposition porte sur l’empreinte comprenant cette correction.

La synthèse n’est pas copiée depuis la prose du LLM. Après une décision, elle
est reconstruite par une fonction déterministe depuis l’objectif, l’acteur, les
préconditions et le dernier résultat attendu observable du brouillon accepté.
Une opération refusée et une question sans réponse ne peuvent donc pas apparaître
dans la description. L’utilisateur peut ensuite corriger cette description ;
une nouvelle proposition porte sur l’empreinte comprenant cette correction.

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

À partir de la version 2 du workflow de génération, chaque traduction de
précondition est conservée dans `precondition_dependencies` avec un identifiant,
la phrase métier source, un type fermé (`verification`, `fixture`,
`technical_dependency`, `setup` ou `cleanup`), une description exécutable, une
référence technique facultative et un statut de confirmation humaine. Une
fixture ou une dépendance technique exige une référence non secrète. La
confirmation du workflow est refusée tant qu’une précondition ne possède pas de
traduction ou qu’une traduction reste non confirmée.

L’éditeur doit permettre de resynchroniser les cartes de traduction après une
modification des phrases sources sans confirmer automatiquement une nouvelle
carte. Toute modification du type, de la description ou de la référence invalide
la confirmation de la carte. Le contrôle de préparation restitue séparément le
profil d’environnement, l’origine de la destination, les traductions, les
fixtures, la présence des références de secrets et le runtime Playwright. Il ne
retourne aucune valeur de secret. Pour un workflow de version 2, un échec
bloquant interdit la production du candidat ; un workflow historique de version
1 reste lisible et signale la revue à effectuer lors de sa prochaine édition.

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

### EF-007.4 — Workflow pas-à-pas et vues d’organisation

L’éditeur expose trois représentations d’un même workflow canonique. Le passage
d’un mode à l’autre ne crée ni une seconde spécification ni une autre source de
vérité :

1. des formulaires pas-à-pas séparant l’action et le contrôle ;
2. une liste extensible contenant un texte autonome par étape ;
3. un texte unique décrivant l’ensemble du parcours.

Le premier mode utilise des cartes ajoutables, supprimables, duplicables et
réordonnables. Un contrôle peut être ajouté immédiatement après une action sous
la forme d’une étape sans action. Une carte contient :

- un identifiant et un nom d’étape ;
- la page courante et un éventuel prérequis local ;
- une action choisie dans le vocabulaire supporté ;
- une cible de page et une valeur ou référence de donnée lorsque l’action les
  exige ;
- une validation observable, sa cible et le résultat attendu ;
- l’indication qu’une preuve doit être conservée pour cette étape.

Dans les deux modes narratifs, le texte original est conservé dans le brouillon.
Un petit LLM propose des opérations transformant ce texte en étapes canoniques ;
il ne confirme jamais le workflow et n’invente ni cible HTML, ni donnée, ni
résultat. Un brouillon narratif sans étape structurée peut être enregistré mais
ne peut pas être confirmé ou généré.

Les données de test sont saisies dans une liste de références extensible, une
référence par ligne. Les résultats attendus ne forment plus une zone globale
ambiguë : ils appartiennent au contrôle de l’étape concernée. Cette proximité
doit permettre de lire successivement « contexte, action, donnée, contrôle ».

L’arbre reste l’organisation primaire. Le filtre et les vues calculées sont
masqués par défaut et s’ouvrent lorsqu’un filtre est actif. L’interface fournit en complément des
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

Lorsqu’un cas utilise plusieurs fichiers, la génération ne fusionne pas
implicitement leurs premières lignes et ne produit pas leur produit cartésien.
Chaque source possède un identifiant, un chemin relatif et une colonne clé.
Une matrice de cas nommés sélectionne exactement une clé de ligne par source.
Les valeurs utilisent alors une référence qualifiée
`{{data.source.colonne}}`. Une association incomplète, une clé dupliquée ou une
source inconnue est refusée avant génération.

### EF-007.6 — Structure de génération et champs nécessaires

Le cas de test conserve une structure `generation_workflow` de schéma versionné.
Cette structure contient au minimum :

- la page de départ ;
- les profils d’environnement et d’acteur ;
- la référence versionnée de l’intention fonctionnelle ;
- les références de fixtures, jeux de données et secrets ;
- la préparation et le nettoyage confirmés ;
- la politique de preuve ;
- la politique d’usage du LLM ;
- la référence versionnée du profil d’accès LLM ;
- la référence versionnée du profil de génération de code ;
- le délai maximal ;
- les hypothèses ou ambiguïtés ouvertes ;
- le mode de saisie (`form`, `step_text` ou `scenario_text`) ;
- les textes d’étapes et le récit complet, lorsqu’ils existent ;
- l’état de confirmation ;
- les pages analysées avec leur empreinte et leurs éléments ;
- les étapes ordonnées décrites par `EF-007.4`.

Trois skills locaux cadrent l’analyse par un petit LLM :
`analyze-form-test-steps`, `analyze-step-test-narratives` et
`analyze-full-test-narrative`. La requête de conception indique le skill du mode
courant, ses instructions et le contrat de sortie fermé. Tous produisent des
questions et des opérations JSON validables ; aucun ne produit directement du
code.

Depuis le mode de saisie actif, l’utilisateur doit pouvoir ouvrir un panneau de
traçabilité affichant le nom du skill, la partie du workflow analysée, le prompt
de cadrage exact et les règles principales. Ce panneau ne révèle ni secret ni
valeur résolue par le runner.

Depuis le mode de saisie actif, l’utilisateur doit pouvoir ouvrir un panneau de
traçabilité affichant le nom du skill, la partie du workflow analysée, le prompt
de cadrage exact et les règles principales. Ce panneau ne révèle ni secret ni
valeur résolue par le runner.

Après confirmation, la page du cas expose un lien de téléchargement vers le
candidat Python Playwright. Le code n’est pas injecté dans le HTML et n’est pas
affiché sur la page. Une génération impossible doit produire une erreur
explicite plutôt qu’un fichier partiel.

Les valeurs variables utilisent les espaces de noms :

```text
{{data.nom_colonne}}
{{data.source.nom_colonne}}
{{fixture.reference}}
{{secret.reference}}
```

Une valeur `secret` est toujours une référence ; sa valeur ne peut apparaître
dans la structure. L’utilisateur peut afficher et copier la structure JSON à
tout moment. La présence d’une hypothèse ouverte interdit de confirmer le
workflow. Une structure sans étape ou sans validation observable est refusée.
Lorsque plusieurs sources de données sont déclarées, la structure affichée
contient également leurs colonnes clés et la matrice exacte des associations ;
le nombre de cas qui seront collectés est visible avant génération.

### EF-007.7 — Configuration des accès LLM et de la génération

L’administration sépare deux catalogues logiques conservés dans un même fichier
YAML versionné :

1. un **profil d’accès LLM** décrit le fournisseur, l’URL de base, le modèle,
   le délai, les nouvelles tentatives et les noms de variables d’environnement
   portant l’authentification ;
2. un **profil de génération de code** référence une version exacte du profil
   LLM et fixe le langage, le framework, la racine relative de sortie, les
   motifs de fichiers, l’usage des Page Objects, les preuves, la politique
   d’écriture, les validations autorisées, les instructions et la limite de
   fichiers.

Ces responsabilités sont présentées sur deux pages distinctes. **Accès aux
LLM** ne rend que les profils de connexion, leurs références de secrets et leurs
diagnostics. **Génération de code** ne rend que les profils de production et
référence un accès LLM versionné dans une liste. La navigation principale et
l’éditeur de cas donnent un accès direct à chaque page. L’ancienne URL combinée
reste une redirection de compatibilité vers **Accès aux LLM** et ne constitue
plus un écran d’administration.

Sur **Accès aux LLM**, les connexions existantes occupent la largeur disponible.
La création est déclenchée par un bouton `+` placé immédiatement sous la liste ;
le formulaire est masqué par défaut, se déplie sous ce bouton et peut être
refermé sans effacer les valeurs déjà saisies.

Le champ **Modèle** est une liste déroulante alimentée à la demande depuis
l’**URL de base**, pour la création comme pour la modification d’un accès. Un
bouton de rafraîchissement adjacent interroge le fournisseur sans enregistrer le
formulaire. La liste est dédupliquée et triée. Lors d’une modification, le modèle
courant est conservé et explicitement signalé s’il n’est plus retourné. Une
erreur réseau ou d’authentification laisse la sélection intacte et produit un
message contextualisé ; aucun secret ni valeur de clé ne transite dans la page.

Les valeurs de clés API, jetons et identifiants secrets ne sont jamais saisies
ni persistées. Seuls des noms de variables conformes à
`[A-Z_][A-Z0-9_]*` peuvent être enregistrés. Une URL distante doit utiliser
HTTPS ; HTTP est limité à une origine de boucle locale. Les URL contenant des
identifiants, paramètres ou fragments sont refusées.

Les chemins de sortie doivent être relatifs, sans remontée `..`, lettre de
lecteur ni chemin absolu. Les motifs de tests et de Page Objects restent des
noms de fichiers et contiennent respectivement `{case_slug}` et `{page_slug}`.
La validation du code utilise un vocabulaire fermé ; aucune commande shell
libre n’est enregistrée.

Une modification crée une nouvelle version sans altérer les cas ou profils de
génération liés à une version antérieure. Le workflow du cas conserve les
références `identifiant@version`. Lorsqu’un profil de génération et un profil
LLM sont tous deux sélectionnés, leur liaison doit être cohérente.

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

Avant l’exploration interactive, l’application peut analyser une page HTML
statique de la même origine que la cible du projet. L’analyse est bornée en
taille, refuse une redirection vers une autre origine, n’utilise aucun secret et
inventorie au minimum les champs de formulaire, listes, boutons, liens et
titres. Pour chaque élément elle conserve une référence de rédaction, un rôle,
un libellé, un type, les options éventuelles et un localisateur candidat. Une
page nécessitant JavaScript ou une session doit être transmise à l’adaptateur
d’exploration Playwright ; l’analyse statique ne doit pas inventer son contenu.

L’exploration Playwright est décrite par un plan déclaratif versionné et non par
du code libre. Sa première verticale locale impose :

- une URL de départ et une URL de catalogue sur la même origine de boucle
  locale, avec port explicite ;
- une liste fermée d’actions (`fill`, `check`, `uncheck`, `click`, `select`,
  `wait_visible`, `wait_hidden`) et de stratégies de localisation (`label`,
  `role`, `test_id`, `placeholder`, `css`) ;
- au plus vingt actions et un délai compris entre une et cent vingt secondes ;
- des valeurs littérales synthétiques ou des jetons qualifiés
  `{{data.<source>.<colonne>}}` résolus depuis une ligne XLSX explicitement
  identifiée ;
- un contrôle de l’origine après chaque action et le refus de toute évaluation
  JavaScript, commande shell, URL portant des identifiants ou sortie du dépôt ;
- un artefact ne contenant ni les valeurs résolues ni le HTML source, mais
  l’empreinte du DOM rendu, les empreintes des données et les identifiants de
  lignes utilisés.

Après l’arrivée sur la page, l’adaptateur compare le HTML renvoyé par le serveur
dans la session courante au DOM sérialisé après exécution de JavaScript. Le
catalogue distingue ainsi les éléments déjà livrés par le serveur des références
apparues seulement après rendu. Cette classification est informative : le
générateur continue d’utiliser les rôles, libellés et localisateurs stables.

L’application d’un catalogue rendu à un workflow ne remplace pas aveuglément
les références de rédaction existantes. Un élément retrouvé par le même
localisateur et le même rôle conserve sa référence ; les nouveaux éléments
reçoivent une nouvelle référence. L’opération est refusée si une cible utilisée
par une action ou une validation disparaît.

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

Chaque candidat déterministe est accompagné d’un manifeste versionné contenant
au minimum l’empreinte canonique de l’entrée, l’empreinte du code, la version du
générateur, l’identité des sources de données et leurs empreintes. Le manifeste
n’inclut pas d’horodatage afin que les mêmes entrées produisent le même
artefact. Le runner refuse un code ou une source dont l’empreinte ne correspond
plus au candidat généré.

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
- des captures et vidéos selon la politique choisie ;
- des traces Playwright et des archives réseau HAR selon la politique de capture effective ;
- la version exacte du cas de test et du script exécutés.

Après chaque exécution, le runner doit produire un rapport détaillé et transmettre au service d’historisation un enregistrement de résultat contenant uniquement :

- la date de l’exécution ;
- un indicateur de réussite ;
- la durée mesurée.

L’association technique entre cet enregistrement et le cas de test est portée par la relation de stockage et ne constitue pas un champ de l’historique métier. Le service de conception doit pouvoir importer ces enregistrements et afficher l’historique des réussites et des durées sans charger les fichiers lourds. Les journaux, traces et rapports détaillés restent des artefacts liés à l’exécution, mais ne font pas partie de l’historique synthétique. Une exécution de CI ne doit pas modifier la définition du cas de test.

Pour un cas de test de type `performance`, le rapport détaillé conserve les mesures et les seuils comparés. L’historique synthétique ne conserve que la réussite et la durée. Une mesure dépassant un seuil produit un échec explicite, sans être transformée en simple information.

### EF-015.1 — Déclaration d’exécution du cas de test

Chaque cas de test possède une déclaration simple indiquant quand il peut être sélectionné par une CI, par exemple `on_commit`, `on_merge_request`, `nightly`, `release` ou `manual`. Cette déclaration est un attribut du cas de test, est visible dans le formulaire et peut être utilisée avec les tags pour construire une suite de tests destinée à une exécution donnée.

### EF-015.2 — Enregistrement des traces Playwright et HAR

Depuis l’éditeur d’un cas de test, la page d’un plan, la CLI ou la CI,
l’utilisateur doit pouvoir demander l’enregistrement des traces pour une
exécution ciblant :

- un cas de test et une version déterminés ;
- l’ensemble des suites et cas de test référencés par une version déterminée
  d’un plan de test.

Cette seconde possibilité est un **périmètre de sélection** : elle ne transforme
pas le plan de test en unité exécutable. Le runner exécute les cas de test
descendants et conserve une trace distincte pour chaque cas et chaque tentative.
Un index de niveau plan relie la version du plan, l’exécution, les cas
sélectionnés, leurs résultats et les chemins de leurs traces.

Les deux formats de trace pris en charge sont :

- `playwright` : archive `trace.zip` consultable avec Playwright Trace Viewer,
  contenant au minimum les actions, chronologies, captures ou instantanés DOM,
  journaux de console et informations réseau disponibles ;
- `har` : archive `network.har.zip` conforme au format HTTP Archive, contenant
  les requêtes, réponses, en-têtes, statuts, durées et corps autorisés par la
  politique de sécurité.

La liste des formats à produire est une combinaison de `playwright` et `har`.
La politique de capture de chacun est configurable avec les valeurs `off`,
`on`, `on-failure` et `on-first-retry`. Elle peut être définie par défaut dans
le profil d’approche, spécialisée sur un cas de test et surchargée explicitement
pour le lancement d’un cas ou la sélection d’un plan. Le runner calcule une
politique effective déterministe, l’inscrit dans `execution.json` et ne la
modifie pas pendant l’exécution.

Pour une sélection par plan, l’activation de la capture s’applique à tous les
cas descendants effectivement sélectionnés. L’index indique explicitement
chaque trace absente, incomplète ou non finalisée et sa cause ; il ne présente
jamais une collection partielle comme une trace complète du plan. Les traces de
tentatives différentes ne sont ni fusionnées ni écrasées.

Les en-têtes d’autorisation, cookies, jetons, mots de passe et données déclarées
sensibles doivent être masqués ou omis avant persistance. La capture HAR peut
être filtrée aux origines et motifs d’URL autorisés. L’interface et la CLI
signalent que les corps HTTP et les instantanés Playwright peuvent contenir des
données métier, et appliquent les règles d’accès, de téléchargement,
d’expiration et de suppression du projet.

### EF-015.3 — Lancement manuel d’une sélection de plan depuis le poste

La page d’un plan et la CLI doivent permettre à l’utilisateur de lancer
manuellement, depuis son poste, l’ensemble ou un sous-ensemble résolu des suites
et cas de test du plan. Le lancement utilise le même bundle, le même moteur de
sélection et le même contrat de runner que la CI/CD. Il doit fonctionner avec
un environnement Python verrouillé ou une image OCI locale, sans nécessiter une
publication préalable ni une connexion au service de conception après
l’export du bundle.

Avant le lancement, l’interface présente au minimum :

- la version du plan utilisée comme périmètre de sélection ;
- les suites et cas de test retenus, leurs versions et leur ordre ;
- les dépendances ajoutées automatiquement et les exclusions demandées ;
- l’environnement cible, les données et les références de secrets nécessaires ;
- les commandes équivalentes prêtes à copier ;
- la politique de traces et le répertoire local des artefacts.

Le contrôle des préconditions, les restrictions réseau, l’isolation, le
masquage des secrets et les codes de sortie sont identiques à ceux exigés en
CI. Le résultat local conserve l’identifiant d’exécution, l’empreinte du bundle,
la sélection résolue et un statut par cas. Un nouvel export, une modification
de sélection ou une modification de version rend ce résultat non applicable au
nouveau bundle et impose un nouveau lancement avant publication.

### EF-016 — Export et intégration Git

L’export et la publication sont des actions manuelles et explicites. Le système
doit guider l’utilisateur en lui faisant choisir un plan de test, une ou
plusieurs suites de tests, des cas de test, un environnement, une sélection de
tags et un format de sortie. Le mode **Sélection et publication** doit permettre
de vérifier localement cette sélection avant de la figer et de la publier. Les
commandes techniques sont affichées sous forme de commandes prêtes à copier,
mais ne sont pas exigées pour définir un cas de test.

Le système doit permettre de produire un paquet versionnable contenant :

- les scripts de test Playwright ;
- les spécifications structurées des cas de test ;
- l’arborescence ;
- la séquence assainie des prompts et réponses ayant contribué à la génération
  de chaque version de script, avec leurs métadonnées de modèle et de décision ;
- les données d’exemple non secrètes ;
- un manifeste de versions ;
- les commandes d’installation et d’exécution ;
- des modèles GitHub Actions et GitLab CI ;
- une documentation fonctionnelle lisible ;
- une documentation de déploiement pour GitHub Actions ;
- une documentation de déploiement pour GitLab CI.

L’écriture directe dans un dépôt Git exige une autorisation dédiée et limitée
au dépôt concerné. L’export local, la sélection et l’exécution CLI doivent
rester disponibles sans accès Git distant.

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

### EF-016.3 — Sélection de publication

Le mode **Sélection et publication** présente l’arborescence du plan avec des
cases à cocher et permet de sélectionner une suite entière, une sous-suite ou
des cas de test individuels. Il fournit des filtres par nom, tag, type, état,
déclaration CI et dernier résultat local. La sélection d’un parent sélectionne
par défaut ses descendants ; chaque exclusion reste visible et explicite.

Le système résout les dépendances avant exécution et publication. Une dépendance
requise peut être ajoutée automatiquement après confirmation ou bloquer la
sélection ; elle ne peut jamais être omise silencieusement. Un dossier de
classement n’est pas sélectionnable comme unité d’exécution, mais ses
descendants peuvent l’être.

Une **sélection de publication** figée contient au minimum :

- l’identifiant et la version du plan servant de périmètre ;
- les identifiants, versions et empreintes des suites et cas retenus ;
- l’ordre d’exécution et les dépendances résolues ;
- l’environnement logique de vérification et la cible de développement prévue ;
- l’identifiant de l’exécution locale réussie et l’empreinte de son bundle ;
- la date, l’auteur et les exclusions explicites ;
- l’empreinte globale de la sélection.

Seuls les cas de test dans l’état `approuvé` ou `actif` dont la version exacte a
réussi dans l’exécution locale associée sont publiables. Un cas brouillon,
candidat, retiré ou archivé, un échec, une absence de résultat, une version
différente ou une empreinte modifiée bloque la publication. Une nouvelle
sélection peut être préparée sans altérer la précédente.

### EF-016.4 — Publication manuelle vers un environnement de développement Git

Un administrateur doit pouvoir configurer une ou plusieurs cibles GitLab,
GitLab auto-hébergées ou GitHub. Une cible possède au minimum :

- un identifiant stable et un libellé ;
- le fournisseur `gitlab` ou `github` et l’environnement logique
  `development` ;
- l’URL de base HTTPS de l’instance ;
- un projet ou dépôt autorisé, identifié par son chemin ou son identifiant ;
- une branche par défaut, un préfixe de branche de publication et un chemin de destination dans le dépôt ;
- un mode de publication autorisé : commit sur une branche dédiée,
  création/mise à jour d’une merge request GitLab ou d’une pull request GitHub ;
- une référence vers un secret d’authentification ;
- les autorités de certification, délais et paramètres de proxy nécessaires, sans désactiver silencieusement la vérification TLS.

La connectivité et les droits de lecture doivent pouvoir être vérifiés séparément sans effectuer d’écriture. Le secret doit être limité au projet et aux opérations nécessaires à la publication.

Depuis le mode **Sélection et publication**, un utilisateur autorisé doit
pouvoir choisir une sélection figée et une cible configurée, puis déclencher
manuellement la publication du bundle. Avant confirmation, le système affiche
l’instance, le projet ou dépôt, l’environnement `development`, la branche, le
chemin, la liste des cas, la liste des fichiers, le dernier résultat local et
le diff prévu. La publication doit :

- utiliser exactement la sélection et le bundle vérifiés, sans régénération ;
- créer un commit traçable indiquant l’utilisateur, le plan de test,
  l’identifiant de sélection, l’exécution locale et les versions publiées ;
- ne jamais effectuer de `force push` ni écraser silencieusement une modification distante ;
- refuser un projet, une branche ou un chemin hors des valeurs autorisées ;
- proposer une nouvelle branche ou signaler un conflit lorsque la branche distante a divergé ;
- retourner l’identifiant du commit et, le cas échéant, l’URL de la merge
  request ou de la pull request ;
- enregistrer l’opération et son résultat dans le journal d’audit sans enregistrer le secret.

Dans cette spécification, publier vers l’environnement de développement
signifie déposer le bundle dans le dépôt, la branche et le chemin administrés
qui alimentent sa CI/CD. La publication peut déclencher le pipeline prévu par
GitLab ou GitHub, mais ne déploie pas directement l’application cible et ne
transforme pas un échec de pipeline en réussite.

La publication ne change pas automatiquement l’état du cycle de vie. Un cas
publié dans l’état `approuvé` reste exclu des sélections CI ordinaires jusqu’à
son activation explicite ; un cas déjà `actif` conserve son état.

L’indisponibilité de GitLab ou GitHub, ou un échec de publication, ne doit
invalider ni la sélection figée ni le bundle exporté localement. L’exécution du
bundle reste indépendante des API GitLab et GitHub.

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
- manuellement depuis le poste de l’utilisateur avec les mêmes sélecteurs et
  formats de résultats que dans la CI ;
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

Les jetons utilisés pour publier vers GitLab ou GitHub sont référencés depuis
le mécanisme de secrets de l’application. Ils doivent être limités au projet ou
dépôt configuré et aux droits strictement nécessaires à sa lecture, à la
création d’un commit et, si ce mode est autorisé, à la gestion d’une merge
request ou pull request. Leur rotation ou révocation ne doit pas nécessiter de
modifier un bundle exporté.

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

Les adaptateurs de publication manuelle peuvent utiliser les API d’une instance
GitLab ou GitHub configurée. Cette dépendance concerne uniquement le transfert
du bundle vérifié vers le dépôt ; elle ne doit jamais être nécessaire à sa
sélection, à son exécution locale ou à son exécution en CI.

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

Décrit les objectifs, le périmètre, la base de test, les risques, les ressources, les contraintes, les critères d’entrée et de sortie, les besoins d’environnement et de données, ainsi que l’ordonnancement prévisionnel. Il référence exactement un identifiant et une version de profil d’approche de test, ainsi qu’une ou plusieurs suites de tests. Il peut être versionné et exporté ; il n’est pas lui-même exécuté.

### Profil d’approche de test

Décrit de manière administrable et versionnée la façon dont les tests sont
sélectionnés et conçus : niveaux, types, techniques de conception, analyse des
risques, stratégie d’automatisation, éléments de preuve et instructions de
génération. Sa description canonique est stockée en YAML. La dernière version
active est proposée aux nouveaux plans ; les versions historiques restent
résolubles pour les plans qui les référencent.

### Suite de tests

Assemble une sélection ordonnée de cas de test ou de sous-suites en vue d’une exécution déterminée. La résolution de cet ordre et des dépendances produit une procédure de test. La suite possède un identifiant stable, un objectif d’exécution, des préconditions et postconditions communes facultatives, ainsi que des valeurs par défaut de type de test et de déclaration d’exécution. Elle peut être sélectionnée et exécutée indépendamment lorsque ses dépendances sont satisfaites.

### Sélection de publication

Fige un sous-ensemble résolu de suites et cas d’un plan, leurs versions,
dépendances, ordre et empreintes, ainsi que l’exécution locale réussie qui les a
vérifiés. Elle constitue l’entrée immuable d’une publication manuelle.

### Cible Git de développement

Décrit un fournisseur GitLab ou GitHub autorisé, une instance, un projet ou
dépôt, l’environnement logique `development`, une stratégie de branche, un
chemin de destination, un mode de publication et une référence de secret. Elle
ne contient jamais le jeton d’accès lui-même.

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

### Trace d’exécution

Associe une exécution, un cas de test, une tentative et un format
`playwright` ou `har` à un fichier, une empreinte, un état de finalisation et
une politique de conservation. Une sélection au niveau d’un plan de test
possède un index de traces, mais chaque trace reste rattachée au cas de test et
à la tentative qui l’ont produite.

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
                            Spécifications et tests Playwright
                            + séquences de génération
                            + données et manifeste
                            + configuration

                         PHASE D’EXÉCUTION
┌─────────────────┐       ┌──────────────────────┐       ┌───────────────┐
│ GitHub Actions, │──────▶│ Runner autonome OCI │──────▶│ Application   │
│ GitLab CI, CLI  │       │ ou paquet Python    │       │ cible         │
└─────────────────┘       └──────┬───────────────┘       └───────────────┘
                                 │
                                 ├── JUnit XML, traces Playwright/HAR, captures, code de sortie
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
- **Sorties :** code de sortie, JUnit XML, JSON structuré, journaux, captures,
  traces Playwright et archives HAR.
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
│   └── git/           # Export local et publication manuelle vers GitLab/GitHub
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

La frontière d’entrée est un bundle versionné et montable en lecture seule. Les
résultats sont écrits dans une arborescence d’artefacts séparée. Les deux
arborescences utilisent des identifiants ou slugs stables, portables et
indépendants des libellés affichés à l’utilisateur :

```text
sentinelle-bundle/
├── sentinelle-manifest.json
├── publication-selection.json
├── specifications/
│   ├── plan.yaml
│   ├── hierarchy.yaml
│   └── cases/
│       └── <case-id>.yaml
├── generation/
│   └── cases/
│       └── <case-id>/
│           └── <case-version>/
│               ├── sequence.jsonl
│               └── metadata.json
├── tests/
│   ├── cases/
│   │   └── test_<case-slug>.py
│   ├── pages/
│   └── fixtures/
├── test-data/
│   ├── datasets/
│   └── environments/
├── config/            # Paramètres d’exécution versionnables, sans secret
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

artifacts/
└── executions/
    └── <execution-id>/
        ├── execution.json
        ├── results/
        │   ├── summary.json
        │   ├── junit.xml
        │   ├── cases/
        │   │   └── <case-id>.json
        │   └── logs/
        └── traces/
            ├── index.json
            └── cases/
                └── <case-id>/
                    └── <attempt-id>/
                        ├── playwright/
                        │   └── trace.zip
                        └── har/
                            └── network.har.zip
```

Cette organisation sépare clairement :

- le **code des tests** dans `tests/` ;
- la **séquence de prompts de génération** dans `generation/` ;
- les **données de test** dans `test-data/` ;
- les **résultats des tests** dans `results/` ;
- les **traces des tests** dans `traces/`.

`sequence.jsonl` conserve dans l’ordre les messages assainis ayant réellement
contribué à la génération, le rôle de chaque message, l’identifiant et la
version du modèle ou gabarit de prompt, les réponses structurées et la décision
utilisateur associée. `metadata.json` conserve les empreintes, versions,
paramètres non secrets et liens vers le cas et le script produits. La
conversation exploratoire sans effet sur le script n’est pas recopiée. Toute
valeur secrète est remplacée par une référence ou un marqueur de masquage.

`execution.json` décrit le sélecteur utilisé (`case`, `suite`, `plan` ou tags),
les versions résolues, l’environnement logique, la politique de capture
effective et l’état de finalisation. `traces/index.json` inventorie les traces
par cas et tentative, avec leur format, chemin relatif, empreinte, taille, état
de finalisation et éventuelle cause d’absence. Pour une sélection par plan, cet
index constitue le point d’entrée de la trace agrégée du plan.

`publication-selection.json` est présent dans un bundle préparé pour
publication. Il contient la sélection figée définie par `EF-016.3`, référence
l’exécution locale qui l’a vérifiée et participe à l’empreinte globale du
bundle. Un export destiné uniquement à une vérification locale peut l’omettre.

Les répertoires `sentinelle-bundle/` et `artifacts/` ne doivent pas
être imbriqués. Le premier est versionnable et immuable pendant une exécution ;
le second est généré, soumis à une politique de conservation et ignoré par Git
par défaut. Aucun résultat ou trace ne doit être réécrit dans le bundle.

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
- les chemins des spécifications, scripts, séquences de génération et données
  de test ;
- l’éventuelle sélection de publication et l’exécution locale de vérification
  associée ;
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

### 10.10.1 Publication vers un environnement de développement Git

La publication manuelle utilise un port applicatif indépendant du générateur et
des adaptateurs GitLab et GitHub remplaçables. La configuration versionnable
contient uniquement les cibles et règles non secrètes ; le jeton est résolu au
moment de l’action depuis le mécanisme de secrets.

Le flux est le suivant :

1. l’utilisateur prépare une sélection depuis un plan et l’exécute localement ;
2. l’application vérifie que les versions retenues ont toutes réussi avec
   l’empreinte exacte du bundle ;
3. elle fige `publication-selection.json` et prévisualise l’export complet ;
4. l’utilisateur sélectionne une cible GitLab ou GitHub administrée pour
   l’environnement de développement ;
5. l’application vérifie la cible, les droits, la branche distante et le chemin
   autorisé ;
6. elle calcule le diff entre le bundle vérifié et le contenu distant ;
7. l’utilisateur confirme explicitement la publication ;
8. l’adaptateur crée ou met à jour une branche sans réécriture forcée de
   l’historique ;
9. il crée ou met à jour une merge request ou pull request uniquement si le
   profil l’autorise ;
10. l’application conserve la sélection, l’exécution locale, l’empreinte
    publiée, l’identifiant du commit, l’éventuelle demande de fusion et le
    résultat dans le journal d’audit.

Les adaptateurs doivent accepter les URL d’instances auto-hébergées lorsqu’elles
sont prises en charge, les autorités de certification d’entreprise configurées
et les proxys administrés. Ils doivent refuser les redirections vers une autre
origine, les certificats invalides non approuvés et toute cible sortant du
projet ou dépôt configuré.

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

Le MVP doit démontrer qu’un utilisateur peut élaborer un plan de test,
organiser ses cas de test en suites, les valider individuellement, lancer depuis
son poste la sélection résolue d’un plan, retenir les cas qui fonctionnent, puis
publier exactement cette sélection vers un environnement de développement
GitLab ou GitHub et l’exécuter en CI sans dépendre d’un LLM pendant l’exécution
nominale.

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
25. des écrans distincts pour le projet, le plan et le cas, avec création hiérarchique guidée et sections séparées pour les étapes, données et résultats attendus ;
26. le lancement manuel depuis le poste de l’utilisateur de l’ensemble ou d’un
    sous-ensemble résolu des cas d’un plan, avec résultats et traces locaux.

#### Tranche B — Exécution autonome et CI

1. un runner autonome capable de sélectionner un cas de test, une suite de tests ou des tags ;
2. des rapports console, JSON et JUnit XML ;
3. des captures et, selon la politique choisie, des traces Playwright et HAR
   pour un cas de test ou pour tous les cas sélectionnés depuis un plan ;
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
15. la configuration de cibles GitLab et GitHub pour l’environnement de
    développement ;
16. un mode de sélection par arbre et filtres, avec résolution explicite des
    dépendances et exclusions ;
17. le gel d’une sélection publiable liée à l’exécution locale réussie et à
    l’empreinte exacte du bundle ;
18. la publication manuelle de ce bundle sur une branche dédiée, avec création
    optionnelle d’une merge request GitLab ou d’une pull request GitHub.

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
|  |  |  |  | 73 | `ACC-073` |
|  |  |  |  | 74 | `ACC-074` |
|  |  |  |  | 75 | `ACC-075` |
|  |  |  |  | 76 | `ACC-076` |
|  |  |  |  | 77 | `ACC-077` |
|  |  |  |  | 78 | `ACC-078` |
|  |  |  |  | 79 | `ACC-079` |
|  |  |  |  | 80 | `ACC-080` |
|  |  |  |  | 81 | `ACC-081` |
|  |  |  |  | 82 | `ACC-082` |
|  |  |  |  | 83 | `ACC-083` |
|  |  |  |  | 84 | `ACC-084` |
|  |  |  |  | 85 | `ACC-085` |
|  |  |  |  | 86 | `ACC-086` |
|  |  |  |  | 87 | `ACC-087` |
|  |  |  |  | 88 | `ACC-088` |
|  |  |  |  | 89 | `ACC-089` |
|  |  |  |  | 90 | `ACC-090` |

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
32. Les profils d’approche de test, modèles de cas de test, types de test, tags, phrases d’intention et environnements sont chargés depuis les fichiers de configuration administrables.
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
49. Un administrateur configure une cible GitLab ou GitHub, vérifie sa connectivité sans écriture et la limite à un environnement de développement, un projet ou dépôt, une stratégie de branche, un chemin et une référence de secret.
50. Un utilisateur autorisé prévisualise puis confirme manuellement la publication du bundle exact vers la cible Git ; un commit traçable et, selon le fournisseur, une merge request ou pull request est créé sans `force push`, tandis qu’une divergence distante ou une cible hors périmètre bloque l’écriture et produit un résultat explicite.
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
63. Sans écrire de YAML, un utilisateur définit un cas dans un workflow pas-à-pas, ajoute, duplique, supprime et réordonne ses cartes ; chaque carte conserve son action et sa validation structurées, tandis qu’un ancien format reste lisible mais exige une requalification avant confirmation.
64. Une définition fonctionnelle conserve l’objectif, l’acteur, l’environnement, les préconditions, données, postconditions, exigences, règles métier et déclaration d’exécution ; une modification incrémente sa version et un redémarrage sur le même fichier SQLite restaure exactement le mode, la version et le contenu.
65. Un projet peut afficher les mêmes cas de test dans l’arbre ou dans des vues calculées par tag, exigence et règle métier, puis les rechercher par texte ; changer de vue ne modifie ni parent, ni ordre, ni identifiant.
66. Un même tableau valide importé en CSV UTF-8 puis en XLSX produit les mêmes colonnes et lignes canoniques ; un fichier trop volumineux, vide, sans itération, avec en-tête vide ou dupliqué, archive invalide, extension inconnue ou formule Excel est refusé avant persistance.
67. À partir de quatre lignes, la stratégie série produit quatre lots d’une itération dans l’ordre source, la stratégie parallèle produit des lots respectant la concurrence maximale et la stratégie aléatoire produit le nombre demandé d’itérations sans doublon ; une même graine reproduit le même ordre.
68. Depuis l’interface web, un utilisateur associe un CSV ou XLSX à un cas de test, choisit série, parallèle ou aléatoire et consulte les colonnes, lignes et lots prévus ; une modification incrémente la version et un redémarrage SQLite restaure exactement les données, l’empreinte et la stratégie sans conserver ni exécuter le fichier actif.
69. Depuis l’accueil, un utilisateur crée un projet, complète un plan de test dans un formulaire distinct puis atteint la page de ce plan ; le fil d’Ariane et les URL conservent les identifiants du projet et du plan après rechargement.
70. Depuis un plan, un utilisateur crée une suite de tests et un dossier, puis crée un cas directement sous chacun d’eux ; la création d’un cas à la racine du plan ou sous un autre cas est refusée explicitement.
71. L’éditeur d’un cas affiche dans cet ordre le contexte, les pages et champs, les étapes, les données et la structure de génération ; la section des données reste visible sans donnée et une étape incomplète produit un diagnostic ciblé.
72. L’utilisateur ouvre un cas depuis l’arbre, enregistre sa définition, revient au plan puis rouvre le même cas ; le projet, le plan, le parent, les sections et les valeurs enregistrées sont restaurés sans confusion avec une suite, un dossier ou un autre cas.
73. Un administrateur ouvre la configuration des approches de test, crée un profil valide puis modifie ce profil ; le fichier YAML contient les versions `1` et `2`, les nouveaux plans proposent la dernière version active dans une liste sans champ libre et un plan déjà enregistré conserve l’identifiant et la version initialement sélectionnés.
74. Depuis un cas, un utilisateur analyse une page HTML de la cible du projet et obtient les champs, boutons, liens et titres avec leurs références, rôles, libellés et localisateurs candidats ; une autre origine, une redirection externe, une ressource non HTML ou une page trop volumineuse est refusée.
75. L’utilisateur enregistre un workflow contenant profils, références de fixtures et secrets, préparation, nettoyage, politiques, délai, pages et étapes ; un redémarrage SQLite restaure exactement la structure versionnée et son aperçu JSON.
76. L’éditeur ajoute et réordonne des cartes action/validation alimentées par la palette de page ; une action nécessitant une cible, une valeur requise absente, un workflow sans assertion ou une confirmation avec hypothèse ouverte est refusé explicitement.
77. L’accueil donne accès à un tutoriel détaillé couvrant la configuration, l’analyse de page, la syntaxe des références, la rédaction des étapes, la finalisation LLM et la vérification de la structure de génération ; les nouveaux champs possèdent une infobulle et un lien documentaire.
78. Un administrateur crée un profil d’accès LLM contenant fournisseur, endpoint, modèle, limites et noms de variables d’environnement ; le YAML conserve ces références et versions sans jamais conserver une valeur de clé envoyée au formulaire.
79. Un administrateur crée un profil de génération lié à une version exacte d’accès LLM et définit langage, framework, chemins relatifs, motifs, preuves, politique d’écriture, validations, instructions et limite de fichiers ; un chemin dangereux, une validation libre ou une référence inconnue est refusé.
80. L’éditeur d’un cas permet de sélectionner les versions d’accès LLM et de génération ; le JSON, SQLite et un redémarrage restaurent les références, tandis qu’une liaison incohérente entre les deux profils est refusée.
81. Pour l’exécution d’un cas de test, l’utilisateur active la capture
    Playwright et HAR ; chaque tentative produit un `trace.zip` et un
    `network.har.zip` consultables, rattachés à la version exacte du cas et
    inventoriés avec leur empreinte, tandis que les secrets configurés sont
    absents des fichiers persistés.
82. Pour une sélection correspondant à une version d’un plan de test, le runner
    applique la politique de capture à tous les cas descendants effectivement
    sélectionnés et produit un index qui relie chaque résultat et tentative à
    sa trace Playwright et HAR ou indique explicitement la cause de son absence,
    sans présenter le plan comme une unité exécutable.
83. Un export présente une arborescence stable séparant spécifications, code des
    tests, séquences assainies de prompts de génération et données de test dans
    le bundle en lecture seule, puis résultats et traces dans les artefacts
    d’exécution ; deux exécutions ne s’écrasent pas et aucun artefact
    d’exécution n’est écrit dans le bundle.
84. Depuis la page d’un plan ou la CLI sur son poste, l’utilisateur lance
    manuellement l’ensemble ou un sous-ensemble de ses cas avec le même bundle
    et le même moteur de sélection que la CI ; les versions résolues, résultats,
    codes de sortie et traces sont conservés sans présenter le plan comme une
    unité exécutable.
85. Le mode Sélection et publication permet d’inclure ou exclure suites et cas,
    de filtrer l’arbre et de résoudre les dépendances ; il refuse de figer une
    sélection contenant un cas qui n’est ni approuvé ni actif, qui est en
    échec, non exécuté ou différent de la version vérifiée, puis produit
    `publication-selection.json` avec l’empreinte du bundle et l’exécution
    locale associée.
86. L’utilisateur choisit une cible de développement GitLab ou GitHub,
    prévisualise le dépôt, la branche, le chemin, les cas, fichiers et
    différences, puis publie après confirmation exactement la sélection
    vérifiée ; le commit et l’éventuelle merge request ou pull request sont
    audités, tandis qu’une modification d’empreinte, une divergence ou une
    cible hors périmètre bloque la publication.
87. Sur les catalogues de projets, plans, approches, accès LLM et profils de
    génération, le formulaire de création est replié sous la liste, s’ouvre par
    un bouton `+`, reçoit le focus et se replie sans perdre sa saisie ; l’utilisateur
    choisit l’un des sept thèmes depuis l’en-tête et retrouve ce choix après une
    navigation ou un rechargement, tandis qu’une valeur locale inconnue revient
    au thème Forêt ; le thème Défense affiche le bloc-marque ministériel et le
    pictogramme Rafale depuis les ressources locales, avec les couleurs officielles
    Bleu France et Rouge Marianne.
88. Depuis le catalogue, un utilisateur autorisé modifie le projet concerné : nom,
    description, sa cible web et sa politique de sécurité ; les valeurs sont
    restaurées après redémarrage, une saisie invalide ne produit aucune mutation
    partielle et la cible déjà enregistrée dans chaque plan reste inchangée.
89. Dans le catalogue, chaque projet possède sa commande de modification. Après
    ouverture d’un projet, les plans sont les racines d’une arborescence unique qui
    affiche dans l’ordre plans, dossiers, suites et cas ; les quatre niveaux sont
    modifiables sans passer par une page de plan séparée, les boutons `+` créent le
    niveau enfant attendu et le retour d’un cas retrouve cette arborescence.
90. Un profil de génération affiche et versionne les skills utilisés. Depuis un
    cas confirmé, l’utilisateur ouvre un prompt final demandant explicitement la
    production du code, retrouve les versions exactes du LLM, du profil et des
    skills, puis accède séparément au téléchargement du code candidat ; le prompt
    censure les valeurs des champs de mot de passe et porte une empreinte stable.

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
- le dévoilement progressif des formulaires de création, le focus, le repli sans
  perte et la présentation pleine largeur des catalogues ;
- la liste fermée des thèmes, leur application globale, leur persistance locale
  et le repli sûr sur le thème par défaut ; pour les thèmes institutionnels, les
  ressources locales, leur provenance, leur intégrité visuelle et leur usage
  autorisé sont également contrôlés ;
- les sections séparées des étapes, données et résultats attendus et leur validation croisée ;
- les sept types de test, leur héritage et les incompatibilités ;
- la synthèse factuelle des descriptions ;
- les champs obligatoires, aides, exemples, validations et assistance de la saisie guidée ;
- les attributs simples `requirements` et `business_rules` ;
- les modèles de cas de test et leurs questions de clarification ;
- le catalogue de phrases d’intention et sa configuration ;
- la validation des fichiers de configuration administrables ;
- les cibles GitLab et GitHub de développement, leurs restrictions de dépôt,
  branche, chemin, TLS et référence de secret ;
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
- le lancement manuel depuis le poste d’une sélection complète ou partielle
  issue d’un plan ;
- la sélection par arbre et filtres, la résolution des dépendances et le refus
  des versions non vérifiées ;
- le lien immuable entre sélection, exécution locale, bundle et empreinte ;
- la prévisualisation, la confirmation, l’audit et les conflits de publication
  manuelle vers GitLab et GitHub ;
- les codes de sortie et rapports du runner ;
- les politiques de capture, traces Playwright et HAR d’un cas de test ;
- la sélection par plan, l’index des traces par cas et tentative, ainsi que les
  traces absentes ou incomplètes ;
- la séparation entre code, séquences de génération, données, résultats et
  traces dans les arborescences d’export ;
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
| Acceptation | `ACC-001` à `ACC-090` | vérifications observables du MVP | à transformer en cas de test |

Une exigence ne peut être marquée comme implémentée que lorsqu’un cas de test ou une démonstration vérifie son comportement. Les statuts de développement (`à faire`, `en cours`, `implémentée`, `vérifiée`) doivent être suivis dans l’outil de gestion du projet, sans modifier l’identifiant stable de la spécification.

### 14.1 Génération des scripts de test

#### GEN-001 — Entrée de génération

Le générateur reçoit uniquement une version structurée confirmée du cas de test, le modèle de cas de test appliqué, la version du profil d’approche de test référencée par le plan, les autres configurations administratives validées et les versions de générateur déclarées. Il ne reçoit pas directement l’historique brut de conversation. Les niveaux, types, techniques, règles de risque, stratégie d’automatisation, exigences de preuve et instructions de génération du profil sont résolus explicitement et leur provenance est conservée.

L’entrée case-level respecte le contrat suivant ; les identifiants, versions,
chemins, types, tags et configurations effectives sont ajoutés par
l’orchestrateur avant la construction du modèle intermédiaire :

```json
{
  "schema_version": 1,
  "start_url": "https://recette.example.net/login",
  "environment_profile": "recette-eu",
  "actor_profile": "client-authentifie",
  "functional_intent": "authentication-login-success@1",
  "fixture_refs": ["client-standard"],
  "secret_refs": ["client-password"],
  "setup": ["Le compte client actif existe"],
  "cleanup": ["Fermer la session"],
  "evidence_policy": "on_failure",
  "llm_policy": "design_only",
  "llm_access_profile": "openai-recette@1",
  "code_generation_profile": "python-playwright@1",
  "timeout_seconds": 30,
  "assumptions": [],
  "confirmed": true,
  "pages": [
    {
      "url": "https://recette.example.net/login",
      "title": "Connexion",
      "fingerprint": "sha256...",
      "elements": [
        {
          "reference": "page:login#email",
          "kind": "input",
          "role": "textbox",
          "label": "Adresse électronique",
          "input_type": "email",
          "locator": {"strategy": "label", "value": "Adresse électronique"},
          "options": []
        }
      ]
    }
  ],
  "steps": [
    {
      "id": "step-1",
      "name": "Saisir l’adresse",
      "page_url": "https://recette.example.net/login",
      "precondition": "La page de connexion est visible",
      "action": "fill",
      "target": "page:login#email",
      "value": "{{data.email}}",
      "assertion": "value",
      "assertion_target": "page:login#email",
      "expected": "{{data.email}}",
      "evidence": false
    }
  ]
}
```

Le schéma JSON formel doit être versionné avec le générateur. Une propriété
inconnue, un type invalide, une cible obligatoire absente, une URL hors origine,
une référence de secret mal formée ou une version de schéma non prise en charge
est refusée explicitement.

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

#### GEN-002.1 — Finalisation structurée par le LLM

Avant la génération de code, et uniquement lorsque la politique l’autorise, le
LLM de conception reçoit :

- la structure `generation_workflow` courante ;
- le contexte effectif du cas et du profil d’approche ;
- les pages analysées et leurs éléments ;
- le vocabulaire d’actions et d’assertions supportées ;
- les règles de données, de secrets, de destinations et de localisateurs ;
- le schéma de sortie attendu.

Il doit retourner une proposition structurée contenant les questions
bloquantes, les modifications proposées et leur justification courte. Le
système calcule le diff, distingue visuellement proposition et valeur confirmée
et exige une décision utilisateur pour chaque changement. Après acceptation, le
schéma est reconstruit depuis les valeurs structurées puis soumis aux contrôles
déterministes.

L’implémentation conserve séparément le dialogue, les propositions, leur
empreinte de base et l’état `pending`, `accepted` ou `rejected` de chaque
opération. Le client envoie la liste exacte des opérations acceptées ; toutes
les autres sont enregistrées comme refusées. Une proposition déjà décidée ne
peut pas être rejouée.

L’implémentation conserve séparément le dialogue, les propositions, leur
empreinte de base et l’état `pending`, `accepted` ou `rejected` de chaque
opération. Le client envoie la liste exacte des opérations acceptées ; toutes
les autres sont enregistrées comme refusées. Une proposition déjà décidée ne
peut pas être rejouée.

Le LLM ne reçoit pas de valeur secrète, ne navigue pas pendant cette étape, ne
marque pas le workflow comme confirmé, ne déclare pas un contrôle système
réussi et ne produit pas directement un artefact approuvé. Une sortie non
conforme au schéma ne modifie pas la définition.

#### GEN-002.2 — Résolution de la configuration effective

Avant tout appel LLM, l’orchestrateur résout la référence
`llm_access_profile` vers une version immuable du catalogue. Il charge la
valeur secrète uniquement depuis la variable d’environnement référencée et ne
la place ni dans le prompt, ni dans les journaux, ni dans un manifeste.
L’absence de variable, un profil désactivé ou une version inconnue produit un
blocage explicite avant l’appel réseau.

Avant de produire les fichiers, l’orchestrateur résout
`code_generation_profile`, contrôle qu’il référence le même accès LLM et
construit une configuration effective immuable. Cette configuration borne les
chemins, le nombre de fichiers, les technologies, la politique de preuve et les
contrôles autorisés. Le modèle ne peut pas modifier ces valeurs ; toute
proposition hors profil est rejetée avant écriture.

#### GEN-002.3 — Prompt final et skills de génération

Chaque profil de génération référence une liste ordonnée et non vide de skills
versionnés. La configuration affiche leur référence, leur rôle et leur source ;
une référence absente, dupliquée ou inconnue est refusée. Le prompt final
assemble exclusivement :

- l’identité et la version du cas confirmé ;
- le workflow canonique et les catalogues HTML analysés ;
- les versions exactes de l’accès LLM et du profil de génération ;
- la configuration effective bornant technologie, chemins, fichiers, preuves et
  validations ;
- les références, sources et règles des skills déclarés ;
- un contrat JSON fermé contenant les fichiers candidats, hypothèses et alertes.

Le prompt demande explicitement la production du code, possède une version et
une empreinte SHA-256. Les valeurs ciblant un champ de mot de passe sont
censurées avant sa construction et aucune valeur de clé API n’entre dans
l’artefact. Depuis un cas confirmé, l’utilisateur peut ouvrir ce prompt dans une
vue séparée et télécharger séparément le code candidat ; aucun des deux n’est
affiché directement dans le formulaire de saisie.

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

Le code Playwright Python doit respecter les catégories du contrat de bundle
défini en `10.7` et séparer au minimum :

```text
tests/
├── cases/       # scénarios et assertions
├── pages/       # Page Objects réellement réutilisés
└── fixtures/    # préparation et nettoyage
test-data/       # jeux de données non secrets
generation/      # séquences et métadonnées de génération assainies
config/          # paramètres sans secrets
```

Le répertoire `artifacts/` est extérieur au bundle et n’est jamais une source
de génération. Chaque fichier de code généré doit indiquer l’identifiant du cas
de test et la version de génération, sans inclure le prompt complet ni de
secret. La séquence assainie est conservée séparément dans `generation/`.

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
- lancer manuellement depuis le poste de l’utilisateur les cas sélectionnés à
  partir d’un plan afin de vérifier leur bon fonctionnement avant publication ;
- sélectionner les suites et cas vérifiés, figer leur version et leur empreinte,
  puis publier exactement ce bundle vers une cible de développement GitLab ou
  GitHub administrée ;
- exécuter ces scripts indépendamment de la conception ;
- enregistrer et organiser les traces Playwright et HAR d’un cas de test ou de
  l’ensemble des cas sélectionnés depuis un plan de test ;
- séparer lisiblement le code, les séquences de prompts de génération, les
  données, les résultats et les traces dans les fichiers exportés ;
- réserver le LLM d’exécution à des cas exceptionnels ;
- configurer séparément les LLM de conception et d’exécution ;
- faciliter le déploiement et l’intégration à GitHub Actions et GitLab CI.

Les exigences de sécurité, de versionnement, de validation humaine, d’isolation, de portabilité et d’audit sont dérivées de ces besoins afin de rendre la capacité contrôlable et exploitable.
