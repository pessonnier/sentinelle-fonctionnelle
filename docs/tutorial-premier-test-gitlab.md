# Tutoriel — du premier cas de test à son exécution dans GitLab

Ce guide utilise **Sentinelle Fonctionnelle** pour concevoir un petit test,
générer son code Playwright, le vérifier localement, l’approuver puis le faire
exécuter par GitLab CI/CD. Il suit les écrans et les commandes implémentés dans
le projet. Le fichier est prévu pour être adapté à votre application.

Le résultat attendu est un job GitLab vert, un rapport contenant **un test
réussi** et des journaux téléchargeables. La conception et la génération de cet
exemple sont déterministes : aucun modèle LLM ni clé API n’est nécessaire.

## 1. Le cas d’usage choisi

**Intention :** vérifier que le formulaire du Comptoir des commandes permet de
renseigner un demandeur de type « Entreprise ».

**Acteur :** un acheteur utilisant la page publique du démonstrateur.

**Page testée :**
[Identifier le demandeur](http://127.0.0.1:8000/demo/commandes/client).

| Étape | Action | Résultat vérifié |
| --- | --- | --- |
| 1 | Ouvrir le formulaire client | Le titre « Identifier le demandeur » est visible. |
| 2 | Saisir `Ada Martin` dans « Nom ou raison sociale » | Le champ contient exactement `Ada Martin`. |
| 3 | Saisir `ada@example.test` dans « Adresse e-mail » | Le champ contient exactement `ada@example.test`. |
| 4 | Choisir `Entreprise` dans « Type de client » | La valeur sélectionnée est `Entreprise`. |

Ce premier cas contrôle la saisie et une liste déroulante. Il s’arrête avant
l’envoi du formulaire : il ne crée pas de commande et ne vérifie pas encore
l’enregistrement côté serveur. Le [parcours complet de commandes](orders-demo.md)
permettra ensuite d’ajouter les tableaux, les calculs et les changements d’écran.

Le chemin suivi est : **définition → candidat → exécution locale réussie →
approbation humaine → export du bundle → exécution GitLab**. Un candidat est
une version du code proposée par Sentinelle ; le bundle est le paquet portable
de cette version approuvée, accompagné de son manifeste et de ses empreintes.

## 2. Préparer Sentinelle sur votre poste

Prévoyez Python 3.12, Git et une copie des sources contenant les fonctionnalités
de génération, d’approbation et d’export CI. La base de ce guide est le commit
[`6a2d931`](https://github.com/pessonnier/sentinelle-fonctionnelle/commit/6a2d9317ca149cf76498cd5b8db3fb951890ed49).
Si vous partez de zéro, la branche publiée correspondante est :

```powershell
git clone --branch codex/rename-sentinelle-fonctionnelle https://github.com/pessonnier/sentinelle-fonctionnelle.git
cd sentinelle-fonctionnelle
```

Depuis la racine du dépôt, dans PowerShell :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c requirements/constraints-py312.txt -e ".[test]"
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m sentinelle_fonctionnelle.cli serve --port 8000
```

Si votre environnement `.venv` existe déjà et que les dépendances sont installées,
lancez simplement la dernière commande. Gardez ce terminal ouvert.

Ouvrez [le catalogue Sentinelle](http://127.0.0.1:8000/) puis, dans un autre
onglet, [le formulaire de démonstration](http://127.0.0.1:8000/demo/commandes/client).
Vérifiez que vous voyez « Identifier le demandeur ».

Si le port 8000 est occupé, utilisez `serve --port 8010` et remplacez `8000` par
`8010` dans les URL de conception et les commandes locales de ce guide. Dans
l’exemple GitLab, la cible repart dans un environnement distinct sur le port 8000.

## 3. Créer le projet, le plan et le cas

Dans le **Catalogue**, cliquez sur **Créer mon premier projet** ou **Ajouter
un projet**, selon le contenu de votre base. Renseignez :

| Champ du projet | Valeur |
| --- | --- |
| Nom | `Tutoriel — Premier test GitLab` |
| Description | `Vérifier la saisie d’un demandeur entreprise.` |
| Cible web | `http://127.0.0.1:8000/demo/commandes/client` |
| Politique de sécurité | `demo-only same-origin local-loopback` |

Cliquez sur **Créer et définir le plan**, puis dépliez **Ajouter un plan de
test** si nécessaire.

| Champ du plan | Valeur |
| --- | --- |
| Nom du plan | `Contrôles du formulaire client` |
| Objectif | `Vérifier les saisies de base du formulaire client.` |
| Périmètre | `Nom, e-mail et type de client ; avant soumission.` |
| Profil d’approche de test | `Régression fonctionnelle automatisée` (`automated-regression@1`) |
| Cible ou environnement | `http://127.0.0.1:8000/demo/commandes/client` |
| Type par défaut | `Smoke` |
| Tags | `tutoriel, commandes` |

Cliquez sur **Créer le plan et ajouter un cas**. Dans **Créer mon premier
cas**, saisissez `Renseigner un demandeur entreprise`, puis cliquez sur
**Créer mon premier cas**. La suite « Parcours principal » est créée
automatiquement et l’éditeur du cas s’ouvre.

## 4. Définir le contexte du test

Dans **Contexte et exécution**, utilisez les valeurs suivantes :

| Champ | Valeur |
| --- | --- |
| Objectif du cas | `Vérifier que le demandeur peut saisir son nom, son e-mail et sélectionner Entreprise.` |
| Acteur métier | `Acheteur` |
| Profil d’acteur | `acheteur-demo` |
| Profil d’environnement | `commandes-demo-local` |
| Page de départ | `http://127.0.0.1:8000/demo/commandes/client` |
| Délai maximal | `30` secondes |
| Politique de preuve | `Capture en cas d’échec` |
| Politique LLM | `Aucun LLM` |
| Accès LLM / Génération de code | Laisser `À configurer` pour ce parcours déterministe. |
| Description synthétique | `Un acheteur ouvre le formulaire, renseigne Ada Martin et son e-mail, puis sélectionne Entreprise.` |

Dans **Assistant de conception**, choisissez l’intention **Accéder à une
fonctionnalité** (`access-feature@1`). Vous pouvez utiliser **Analyser les
informations manquantes** pour relire le diagnostic, sans appeler de LLM.

Cet exemple n’utilise ni compte connecté, ni fichier de données, ni fixture.
Laissez donc les préconditions, les références de données et de secrets ainsi
que le nettoyage vides. Les profils d’acteur et d’environnement renseignés ici
décrivent le contexte ; ils ne créent pas de compte ni de session.

## 5. Analyser la page et ajouter les quatre étapes

Dans **Pages et champs**, renseignez la page à analyser :

```text
http://127.0.0.1:8000/demo/commandes/client
```

Cliquez sur **Analyser la page**. La palette doit proposer notamment le titre
« Identifier le demandeur », les champs « Nom ou raison sociale » et « Adresse
e-mail », ainsi que la liste « Type de client ».

Utilisez les références réellement proposées dans cette palette pour remplir
les cibles. Une référence `page:…#…` désigne un élément analysé ; ne la remplacez
pas par son simple libellé. La génération en déduira un localisateur Playwright.

Pour cette page, les références sont `page:client#identifier-le-demandeur`,
`page:client#customer-name`, `page:client#email` et
`page:client#customer-type`. Le libellé analysé de la liste « Type de client »
peut aussi afficher ses options ; choisissez bien sa référence
`page:client#customer-type`.

Dans **Étapes**, choisissez **Formulaires action et contrôle**. Complétez la
première carte existante puis utilisez **Ajouter une action** pour obtenir
exactement quatre cartes. Pour chaque carte, indiquez la page courante
`http://127.0.0.1:8000/demo/commandes/client`.

| Nom de l’étape | Type d’action | Cible de l’action | Valeur | Type de validation | Cible de la validation | Résultat attendu |
| --- | --- | --- | --- | --- | --- | --- |
| Ouvrir le formulaire | Ouvrir la page | Vide | Vide | Est visible | Référence du titre « Identifier le demandeur » | Vide |
| Saisir le nom | Saisir | Référence du champ « Nom ou raison sociale » | `Ada Martin` | Contient la valeur | Même référence que l’action | `Ada Martin` |
| Saisir l’e-mail | Saisir | Référence du champ « Adresse e-mail » | `ada@example.test` | Contient la valeur | Même référence que l’action | `ada@example.test` |
| Choisir le type de client | Sélectionner | Référence de la liste « Type de client » | `Entreprise` | Contient la valeur | Même référence que l’action | `Entreprise` |

Pour **Ouvrir la page**, c’est la **Page courante** qui fournit l’URL à ouvrir.
Pour la liste déroulante de cette démo, le libellé et la valeur de l’option sont
tous deux `Entreprise`, avec cette majuscule. Les données de l’exercice sont
des valeurs littérales synthétiques ; aucun fichier CSV ou Excel n’est requis.

## 6. Confirmer la définition et préparer les déclenchements CI

Dans **Données**, laissez **Hypothèses ou ambiguïtés** vide après votre revue.
Dans **Déclaration CI**, saisissez exactement ces deux lignes :

```text
manual
on_merge_request
```

Ces valeurs autorisent la sélection du cas par le runner Sentinelle. Elles
ne déclenchent pas GitLab à elles seules : les règles du fichier CI de
l’étape 10 détermineront quand le job se lance.

Relisez les quatre étapes dans **Structure de génération**, cochez
**Définition confirmée**, puis cliquez sur **Enregistrer la définition structurée**.
Vérifiez après rechargement que le cas conserve ses pages, ses quatre cartes et
les deux déclarations CI.

## 7. Générer, exécuter et approuver le code

Dans **Candidats, validation et décision** :

1. Cliquez sur **Générer et enregistrer un candidat**. Ce bouton utilise la
   génération déterministe à partir des cartes confirmées.
2. Téléchargez le candidat pour relire le code si nécessaire.
3. Sélectionnez **Chromium**, puis cliquez sur **Lancer ce candidat**. Le serveur
   local et le démonstrateur doivent rester actifs.
4. Attendez une **Réussite**. Le candidat passe à l’état validé ; consultez le
   chemin des preuves indiqué dans son historique si vous devez diagnostiquer.
5. Saisissez une note, par exemple `Quatre contrôles relus et exécutés avec succès.`,
   puis cliquez sur **Approuver l’empreinte exécutée**.

La réussite et l’approbation sont deux décisions distinctes. Le lien
**Exporter le bundle CI** apparaît sur le candidat approuvé. Si vous corrigez
ensuite la définition ou personnalisez le code, générez ou créez un nouveau
candidat, puis répétez l’exécution et l’approbation avant de l’exporter.

## 8. Exporter et essayer le même bundle sur votre poste

Cliquez sur **Exporter le bundle CI**. Renommez le ZIP téléchargé en
`sentinelle-premier-test.zip` et placez-le à la racine de votre copie des sources.
Dans un deuxième terminal PowerShell, toujours depuis cette racine :

```powershell
Expand-Archive -LiteralPath .\sentinelle-premier-test.zip -DestinationPath .\sentinelle-bundle
.\.venv\Scripts\python.exe -m sentinelle_fonctionnelle.runner_cli --bundle .\sentinelle-bundle --artifacts .\artifacts-local --base-url http://127.0.0.1:8000 --allow-origin http://127.0.0.1:8000 --declaration manual
```

Vous devez obtenir `"status": "passed"` et `"exit_code": 0`. Ouvrez
`artifacts-local/junit.xml`, `artifacts-local/execution.json` et
`artifacts-local/stdout.log` pour voir le résultat et le détail pytest.

Le manifeste doit se trouver directement dans
`sentinelle-bundle/sentinelle-manifest.json`. Les résultats doivent rester
**à côté du bundle**, comme ci-dessus : le runner refuse les fichiers ajoutés
ou modifiés à l’intérieur du paquet approuvé.

## 9. Préparer le dépôt GitLab

Pour cet exercice, utilisez un projet GitLab contenant **les sources de
Sentinelle et le bundle extrait**. Vous pouvez importer le dépôt GitHub dans
GitLab ou pousser votre copie vers un projet GitLab vide. Assurez-vous que la
branche transférée contient les fonctionnalités utilisées ici.

Le job ci-dessous installe Sentinelle depuis ces sources. Le seul fichier
`requirements.lock` du bundle ne suffit pas à installer la commande
`sentinelle-run` ni le module importé par le test généré.

À la racine du dépôt, créez ou complétez `.gitattributes` avec :

```gitattributes
sentinelle-bundle/** -text
```

Cette règle doit être présente **avant le premier `git add` du bundle** : elle
empêche Git de convertir les fins de ligne entre Windows et Linux, ce qui
changerait les empreintes approuvées. Ne reformatez aucun fichier du bundle et
n’ajoutez pas de documentation personnelle à l’intérieur.

L’arborescence utile doit ressembler à ceci :

```text
votre-depot/
├── .gitattributes
├── .gitlab-ci.yml
├── pyproject.toml
├── README.md
├── requirements/
│   └── constraints-py312.txt
├── src/sentinelle_fonctionnelle/
└── sentinelle-bundle/
    ├── sentinelle-manifest.json
    ├── pytest.ini
    ├── requirements.lock
    ├── tests/cases/test_case_….py
    ├── specifications/
    ├── generation/
    ├── config/
    ├── ci/
    └── docs/
```

Conservez **tout** le contenu extrait, y compris les fichiers cachés du bundle.
Les noms du fichier de test et des cas dépendent des identifiants créés chez vous.
Les bases SQLite, `.venv`, le ZIP téléchargé et les résultats locaux n’ont pas à
être ajoutés au dépôt GitLab.

## 10. Installer la configuration GitLab CI/CD

Un exemple prêt à copier est fourni dans
[`deployment/examples/gitlab-ci-tutorial.yml`](../deployment/examples/gitlab-ci-tutorial.yml).
Depuis la racine du dépôt :

```powershell
Copy-Item .\deployment\examples\gitlab-ci-tutorial.yml .\.gitlab-ci.yml
```

Si `.gitlab-ci.yml` existe déjà, intégrez le job dans votre configuration au
lieu de remplacer celle-ci. Ajoutez son stage `test` s’il n’est pas déjà déclaré
et conservez les variables et règles nécessaires au job.

L’exemple complet :

```yaml
image: python:3.12-slim-bookworm

stages:
  - test

variables:
  PIP_DISABLE_PIP_VERSION_CHECK: "1"
  TARGET_BASE_URL: "http://127.0.0.1:8000"
  SENTINELLE_FONCTIONNELLE_DECLARATION: "manual"
  PYTEST_ADDOPTS: "--tracing=retain-on-failure --screenshot=only-on-failure"

sentinelle-premier-test:
  stage: test
  timeout: 20m
  before_script:
    - python -m pip install -c requirements/constraints-py312.txt -e ".[test]"
    - python -m playwright install --with-deps chromium
  script:
    - mkdir -p artifacts
    - test -f sentinelle-bundle/sentinelle-manifest.json
    - python -m sentinelle_fonctionnelle.cli serve --host 127.0.0.1 --port 8000 --database /tmp/sentinelle-tutorial.db > artifacts/target.log 2>&1 &
    - TARGET_PID=$!
    - trap 'kill "$TARGET_PID" 2>/dev/null || true' EXIT
    - |
      python - <<'PY'
      import os
      import time
      import urllib.error
      import urllib.request

      url = os.environ["TARGET_BASE_URL"] + "/demo/commandes/client"
      for attempt in range(30):
          try:
              with urllib.request.urlopen(url, timeout=2) as response:
                  if response.status == 200:
                      print("Cible de démonstration disponible :", url)
                      break
          except (urllib.error.URLError, TimeoutError):
              pass
          time.sleep(1)
      else:
          raise SystemExit("Cible indisponible ; consulter artifacts/target.log")
      PY
    - sentinelle-run --bundle ./sentinelle-bundle --artifacts ./artifacts --base-url "$TARGET_BASE_URL" --allow-origin "$TARGET_BASE_URL" --declaration "$SENTINELLE_FONCTIONNELLE_DECLARATION"
  artifacts:
    when: always
    expire_in: 7 days
    reports:
      junit: artifacts/junit.xml
    paths:
      - artifacts/
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      variables:
        SENTINELLE_FONCTIONNELLE_DECLARATION: "on_merge_request"
    - if: '$CI_PIPELINE_SOURCE == "web"'
      variables:
        SENTINELLE_FONCTIONNELLE_DECLARATION: "manual"
```

Le job démarre une **nouvelle instance éphémère du démonstrateur dans le même
conteneur** que Chromium. C’est pourquoi `127.0.0.1:8000` fonctionne dans cet
exemple. Votre serveur Windows n’est pas contacté.

L’installation `playwright install --with-deps chromium` fournit le navigateur
et ses dépendances Linux, selon la
[documentation Playwright pour la CI](https://playwright.dev/python/docs/ci).
Prévoyez un runner GitLab Linux utilisant l’exécuteur Docker, avec les droits
d’installation dans le conteneur et un accès aux registres Python, Debian et aux
téléchargements Playwright. Ce job ne nécessite pas de Docker dans Docker ni
d’image Sentinelle prépubliée.

Dans GitLab, vérifiez qu’un runner compatible est disponible sous **Settings →
CI/CD → Runners**. Si votre organisation exige des tags, ajoutez au job les tags
du runner convenu avec votre administrateur.

## 11. Versionner et lancer le premier pipeline

Depuis votre copie locale, créez une branche et versionnez les trois éléments
de l’exercice :

```powershell
git switch -c codex/premier-test-gitlab
git add .gitattributes .gitlab-ci.yml sentinelle-bundle
git diff --cached --stat
git commit -m "Ajoute le premier test fonctionnel Sentinelle dans GitLab CI"
```

Si votre dépôt local possède déjà un remote GitLab, utilisez son nom pour le
push. Sinon, ajoutez-le en remplaçant l’adresse suivante par **l’URL de votre
projet GitLab contenant les sources**, puis poussez la branche :

```powershell
git remote add gitlab https://gitlab.com/VOTRE_GROUPE/VOTRE_PROJET.git
git push -u gitlab codex/premier-test-gitlab
```

Dans **Build → Pipeline editor**, sélectionnez cette branche et vérifiez la
configuration avec l’outil de validation. Le fichier `.gitlab-ci.yml` doit se
trouver à la racine du dépôt ; voir le
[guide de l’éditeur GitLab](https://docs.gitlab.com/ci/pipeline_editor/).

Pour un premier lancement, ouvrez **Build → Pipelines → New pipeline**,
sélectionnez `codex/premier-test-gitlab`, puis lancez le pipeline. La règle
`web` sélectionne alors la déclaration Sentinelle `manual`.

Créez ensuite une **merge request** depuis cette branche vers la branche
principale de votre dépôt GitLab. Le même job s’exécute avec la déclaration
`on_merge_request`. Un simple push sans merge request ouverte n’est pas un
déclencheur prévu par cet exemple. Ces événements et règles sont décrits dans la
[documentation GitLab des règles de jobs](https://docs.gitlab.com/ci/jobs/job_rules/).

## 12. Lire les résultats et savoir quand le parcours est terminé

Dans le pipeline, ouvrez le job **sentinelle-premier-test**. Une exécution
réussie se termine avec le code `0`. Dans les artefacts téléchargés :

| Fichier ou répertoire | Utilité |
| --- | --- |
| `artifacts/junit.xml` | Résultat du test affichable par GitLab. |
| `artifacts/execution.json` | Statut, déclaration sélectionnée, empreinte du bundle et identifiant d’exécution. |
| `artifacts/stdout.log` | Détail de l’exécution pytest, dont le nombre de tests réussis. |
| `artifacts/stderr.log` | Erreurs émises pendant l’exécution. |
| `artifacts/target.log` | Journaux de démarrage et requêtes du démonstrateur. |
| `artifacts/playwright/` | Captures et traces si un test navigateur échoue avec les options fournies. |

La déclaration `artifacts:reports:junit` permet la lecture des résultats dans
l’onglet **Tests** du pipeline et le résumé des tests de la merge request.
`when: always` conserve les fichiers disponibles même si le job échoue ; le
statut d’échec du job provient du code de sortie du runner. Voir les
[rapports de tests GitLab](https://docs.gitlab.com/ci/testing/unit_test_reports/).

Votre exercice est terminé lorsque le cas est approuvé dans Sentinelle, le
bundle réussit localement, le job GitLab est vert et le rapport JUnit contient
un test réussi. L’exécution CI reste autonome : elle n’est pas réimportée
automatiquement dans l’historique de conception de Sentinelle.

## 13. Résoudre les problèmes courants

| Symptôme | Vérification ou correction |
| --- | --- |
| La page locale ne répond pas | Garder le serveur actif ; vérifier le port et l’URL `/demo/commandes/client`. |
| Python affiche « did not find executable » | L’environnement virtuel pointe vers un Python déplacé ou supprimé. Installer Python 3.12 et créer un nouvel environnement, par exemple `.venv-tutoriel`, puis adapter les chemins des commandes. |
| Les cibles ne sont pas proposées | Analyser la page et utiliser les références de la palette dans les cartes. |
| La génération est bloquée | Vérifier la confirmation, les quatre étapes et leurs validations, la même origine et l’absence d’hypothèse ouverte. Si des préconditions ont été ajoutées, confirmer leurs traductions. |
| Chromium est introuvable | Lancer l’installation Playwright avec le même Python que celui qui exécute Sentinelle. |
| « Exporter le bundle CI » est absent | Exécuter le candidat avec succès puis approuver son empreinte. |
| « Aucun cas approuvé ne correspond… » | Vérifier `manual` et `on_merge_request` dans la définition, puis régénérer, valider, approuver et réexporter si elles manquaient. |
| Empreinte différente sous Linux | Vérifier `.gitattributes`, repartir du ZIP approuvé et réajouter le bundle sans conversion de fins de ligne. |
| Manifeste absent | Vérifier le chemin du bundle : pas de sous-dossier d’extraction supplémentaire. |
| Fichiers non déclarés | Retirer du paquet les ajouts personnels ou repartir de l’export ; garder les artefacts à côté. |
| Job en attente d’un runner | Vérifier la disponibilité, l’exécuteur et les tags du runner GitLab. |
| Aucun job au simple push | Lancer un pipeline depuis l’interface ou ouvrir une merge request ; vérifier aussi les éventuelles règles `workflow` du dépôt existant. |
| Pas de JUnit après un échec | Une installation, un démarrage ou un précontrôle échoué peut arrêter le job avant pytest. Consulter les logs du job et `target.log` s’il existe. |

## 14. Adapter ce premier exercice à votre application

Remplacez la cible, les champs et les résultats par un comportement métier réel,
puis refaites la génération, la validation et l’approbation. Dans GitLab,
supprimez le démarrage du démonstrateur, son attente et son `trap` ; fournissez
`TARGET_BASE_URL` avec l’origine de votre environnement de recette, par exemple
`https://recette.votre-application.fr`, sans chemin de page. Conservez les
sources Sentinelle pour installer le runner, ou fournissez une image contenant
la version correspondante.

Un runner distant ne peut pas joindre votre poste avec `127.0.0.1`. La cible de
recette doit être accessible depuis son réseau. Le code déterministe utilise
`TARGET_BASE_URL` pour remplacer l’origine de conception tout en conservant les
chemins des pages du test. `--allow-origin` fournit l’origine autorisée au
précontrôle du runner ; le filtrage effectif du trafic relève aussi de
l’environnement réseau du runner.

Pour un cas authentifié, injectez les secrets par les variables CI/CD adaptées
et réservez leur utilisation à des branches ou environnements approuvés. Ne
placez aucune valeur sensible dans les cartes ou dans le bundle. Pour passer
à une image de runner préparée, consultez le
[guide d’exploitation](operations-lot4.md) et le
[modèle GitLab existant](../deployment/gitlab-ci.yml) : l’image
`sentinelle-fonctionnelle-runner:0.1.0` de ce modèle doit être construite et
rendue accessible à votre runner avant utilisation.

Pour aller plus loin dans la conception, consultez le
[démonstrateur de commandes multi-écrans](orders-demo.md), la
[cible RH avec données Excel](hr-demo.md) et le
[tutoriel intégré de création d’un cas](http://127.0.0.1:8000/tutorials/test-case).

## Vérification de ce guide

Le 31 octobre 2026, le parcours a été rejoué dans une base isolée : création
par les routes web, analyse de la page réelle, définition des quatre étapes,
génération déterministe, exécution Chromium, approbation et export. Le bundle
exporté a ensuite réussi avec `manual` et `on_merge_request`, avec **un test
réussi et un rapport JUnit pour chaque exécution**. Les liens locaux, le YAML,
sa correspondance avec le fichier copiable et la syntaxe Bash du script ont
également été contrôlés.

Cette vérification locale utilise Windows et Python 3.12. Le job Linux doit
encore être validé dans l’éditeur puis exécuté sur votre runner GitLab ; aucun
pipeline distant n’a été lancé pour rédiger ce document.
