# Avancement de l'implémentation

Ce document est le tableau de bord durable de SentinelleFonctionnelle. Il est mis à
jour après chaque tranche verticale et complète les spécifications sans en
modifier les identifiants.

Dernière mise à jour : **9 septembre 2026** — lot 4, exécution portable et collaboration.

## Règles de suivi

Les états signifient :

- `À faire` : aucun test d'acceptation écrit ;
- `RED` : test écrit et observé en échec pour la raison attendue ;
- `En cours` : implémentation engagée ;
- `Implémentée` : test ciblé réussi ;
- `Vérifiée` : test ciblé, suite complète et véritable point d'entrée réussis ;
- `Bloquée` : dépendance ou décision manquante explicitée.

Une fonctionnalité n'est jamais déclarée `Vérifiée` sur la seule présence de
code ou de documentation.

## Tableau de bord MVP

| Indicateur | Avancement |
|---|---:|
| Capacités de la tranche A vérifiées | 5 / 25 |
| Capacités de la tranche B vérifiées | 0 / 15 |
| Critères d'acceptation vérifiés | 42 / 90 |
| Tests automatisés réussis | 110 tests produit/documentation et 40 sous-tests ; bundle réel exécuté avec Chromium |
| Dernière vérification navigateur | export CI visible uniquement sur le candidat approuvé ; route ZIP vérifiée |
| Dernier contrôle de l’assistant | Ollama 11436 : candidat Qwen réel validé et téléchargé en 57,8 s |

## Tranches verticales

| Tranche | Spécifications | Acceptation | État | Preuve |
|---|---|---|---|---|
| 001 — Projet et arborescence initiale | `EF-001`, `EF-002`, `EF-007` | `ACC-002`, `ACC-003` | Vérifiée | [`proofs/iteration-001.md`](proofs/iteration-001.md) |
| 002 — Modes local/en ligne et isolation | `EF-001.1`, `ENF-008`, `ENF-013` | `ACC-051`, `ACC-052` | Vérifiée | [`proofs/iteration-002.md`](proofs/iteration-002.md) |
| 003 — Persistance SQLite locale | `EF-001`, `EF-002`, `ENF-001`, `ENF-013` | `ACC-053` | Vérifiée | [`proofs/iteration-003.md`](proofs/iteration-003.md) |
| 004 — Tutoriel HTML local | `DOC-001` à `DOC-006` | `ACC-054` | Vérifiée | [`proofs/iteration-004.md`](proofs/iteration-004.md) |
| 005 — Interface web locale persistante | `EF-001.2`, `EF-002`, `EF-002.1`, `ENF-013` | `ACC-060`, `ACC-061`, `ACC-062`, `ACC-069`, `ACC-070`, `ACC-071`, `ACC-072` | Vérifiée | [`proofs/iteration-005.md`](proofs/iteration-005.md) |
| 005.1 — Présentation globale et thèmes | `EF-001.3` | `ACC-087` | Vérifiée | tests d’acceptation et vérification navigateur du 2 août 2026 |
| 005.2 — Édition des projets | `EF-001`, `EF-001.2` | `ACC-088` | Vérifiée | tests d’acceptation et vérification navigateur du 1er août 2026 |
| 005.3 — Catalogue et arborescence unifiée | `EF-001.2`, `EF-002.1` | `ACC-089` | Vérifiée | tests d’acceptation et vérification navigateur du 1er août 2026 |
| 005.4 — Parcours guidé et accessibilité | `EF-001.2`, `EF-007.4`, `ENF-006` | parcours transversal du lot 2 | Vérifiée | [`proofs/lot-002-parcours-guide-accessibilite.md`](proofs/lot-002-parcours-guide-accessibilite.md) |
| 006 — Spécifications multi-formats et vues | `EF-007`, `EF-007.4` | `ACC-063`, `ACC-064`, `ACC-065` | Vérifiée | [`proofs/iteration-006.md`](proofs/iteration-006.md) |
| 007 — Données CSV/XLSX et stratégies | `EF-007.2`, `EF-007.5` | `ACC-066`, `ACC-067`, `ACC-068` | Vérifiée | [`proofs/iteration-007.md`](proofs/iteration-007.md) |
| 008 — Profils d’approche de test YAML | `EF-002.2`, `GEN-001` | `ACC-073` | Vérifiée | [`proofs/iteration-008.md`](proofs/iteration-008.md) |
| 008.1 — Workflow guidé et analyse HTML | `EF-007.4`, `EF-007.6`, `EF-010`, `GEN-001` ; `GEN-002.1` spécifié seulement | `ACC-074` à `ACC-077` | Vérifiée | [`proofs/iteration-008-1.md`](proofs/iteration-008-1.md) |
| 008.2 — Configuration LLM et génération | `EF-007.6`, `EF-007.7`, `GEN-002.2` | `ACC-078` à `ACC-080` | Vérifiée | [`proofs/iteration-008-2.md`](proofs/iteration-008-2.md) |
| 009 — Dialogue, description et catalogues | `EF-003`, `EF-004`, `EF-005`, `EF-017`, `GEN-002.1` | `ACC-007` à `ACC-009`, `ACC-032`, contribution à `ACC-057` et `ACC-059` | En cours (`009.3`) | [`proofs/iteration-009-1.md`](proofs/iteration-009-1.md), [`proofs/iteration-009-2.md`](proofs/iteration-009-2.md), [`proofs/iteration-009-3.md`](proofs/iteration-009-3.md) |
| 010 — Préconditions, données et contrôles | `EF-007.1`, `EF-007.2`, `ENF-012` | `ACC-033`, `ACC-034` | En cours (`010.1`, `ACC-033` vérifié) | [`proofs/iteration-010-1.md`](proofs/iteration-010-1.md) |
| 011 — Validation individuelle et empreinte | `EF-008`, `EF-009` | `ACC-010` à `ACC-014` | Vérifiée | [`proofs/lot-003-cycle-candidat.md`](proofs/lot-003-cycle-candidat.md) |
| 012 — Modèle intermédiaire et génération | `GEN-001` à `GEN-006`, contribution `EF-010` | `ACC-041`, `ACC-042`, `ACC-090`, contribution `ACC-074` | En cours (`012.7`) | [`proofs/iteration-012-1.md`](proofs/iteration-012-1.md), [`proofs/iteration-012-2.md`](proofs/iteration-012-2.md), [`proofs/iteration-012-3.md`](proofs/iteration-012-3.md), [`proofs/iteration-012-4.md`](proofs/iteration-012-4.md), [`proofs/iteration-012-5.md`](proofs/iteration-012-5.md), [`proofs/iteration-012-6.md`](proofs/iteration-012-6.md), [`proofs/iteration-012-7.md`](proofs/iteration-012-7.md) |
| 013 — Bundle, personnalisation et contrôles | `GEN-007` à `GEN-014` | `ACC-016`, `ACC-028`, `ACC-043` | En cours (zones protégées, préservation et conflits vérifiés ; contrôles complémentaires du bundle à poursuivre) | [`proofs/lot-003-cycle-candidat.md`](proofs/lot-003-cycle-candidat.md), [`orders-demo.md`](orders-demo.md) |
| 014 — Runner et rapports | `EF-012` à `EF-015`, `ENF-005` | `ACC-017` à `ACC-025` | En cours (runner vérifié ; OCI statique, qualification externe à faire) | [`proofs/lot-004-execution-collaboration.md`](proofs/lot-004-execution-collaboration.md) |
| 015 — Définition des profils de charge | `LOAD-001` à `LOAD-006` | `ACC-044`, `ACC-045` | À faire | — |
| 016 — Export de charge sécurisé | `LOAD-007` à `LOAD-011` | `ACC-046` | À faire | — |
| 017 — Export, CI et publication | `EF-016`, `ENF-011` | `ACC-026`, `ACC-027`, `ACC-047` à `ACC-050` | En cours (export et modèles CI ; publication Git distante à faire) | [`proofs/lot-004-execution-collaboration.md`](proofs/lot-004-execution-collaboration.md) |

## Dernier incrément — personnalisation et démonstrateur multi-écrans

Le générateur déclare maintenant une zone `sentinelle:custom` contractuelle.
L'import crée un nouveau candidat, refuse les changements extérieurs et vérifie
la syntaxe Python. Une régénération réapplique les zones compatibles ; les
contrats divergents deviennent des conflits visibles qui interdisent
l'exécution. La cible **Comptoir des commandes** complète la démonstration avec
quatre écrans, des saisies variées, des tableaux et des calculs déterministes.
Le parcours reproductible est décrit dans [`orders-demo.md`](orders-demo.md).

## Incrément précédent — lot 4, exécution portable et collaboration

Un candidat approuvé expose un ZIP stable incluant manifeste, définition,
source, documentation et modèles CI. `sentinelle-run` le contrôle puis l'exécute
hors du service. Le profil OCI, l'adaptateur PostgreSQL, les rôles, les révisions
optimistes et la rétention sont décrits dans
[`operations-lot4.md`](operations-lot4.md). La qualification Docker/PostgreSQL
reste explicitement ouverte faute de runtime sur l'hôte.

## Incrément précédent — lot 3, cycle candidat

Le candidat généré est désormais un agrégat durable distinct du cas. La migration
SQLite v8 conserve son origine déterministe ou LLM, la version et l’empreinte de
la définition structurée, les fichiers, le manifeste, l’empreinte du bundle, les
décisions et chaque rapport d’exécution. La reconstruction actuelle de
l’arborescence ne supprime donc plus l’historique des générations.

Depuis le cas, une action unique génère et enregistre le candidat. L’utilisateur
peut ensuite le télécharger, lancer exactement son fichier contrôlé par manifeste,
consulter réussite ou échec avec le répertoire de preuves, puis approuver ou
rejeter. Une réussite produit seulement l’état **Validé individuellement** : le
bouton d’approbation constitue une décision humaine distincte. Une régénération
conserve les versions précédentes et calcule les fichiers ajoutés, modifiés ou
supprimés.

La preuve ciblée, la suite complète et le parcours navigateur réel sont décrits
dans [`proofs/lot-003-cycle-candidat.md`](proofs/lot-003-cycle-candidat.md).

## Incrément précédent — 012.7

La page du prompt d’un cas confirmé peut maintenant appeler le profil LLM
versionné effectivement sélectionné. L’adaptateur transmet directement les deux
messages audités au point d’entrée compatible OpenAI, avec sortie JSON, température
nulle, raisonnement Ollama désactivé et limite de sortie bornée. Pour le projet RH,
l’appel utilise `http://127.0.0.1:11436/v1`, le profil
`ollama-qwen36-128k-11436@1` et le modèle
`qwen3.6-35b-a3b-q4_K_M_128k:latest`.

La réponse reste non fiable jusqu’à sa validation : version de schéma, nombre de
fichiers, racine relative, extension, doublons, taille, présence du fichier principal
et syntaxe Python sont contrôlés. Un candidat unique est téléchargé comme source ;
plusieurs fichiers forment une archive avec manifeste et empreintes. Aucun fichier
n’est écrit automatiquement dans le dépôt et le générateur déterministe demeure
disponible séparément.

Vérification du 3 août 2026 : `17 passed` sur le parcours ciblé, puis `80 passed`
et `32 subtests` pour le produit et la documentation. Les six scripts Playwright
collectés séparément réussissent avec la cible RH temporairement active. L’appel
réel Ollama final a répondu `200` en 57,8 secondes. Ses trois hypothèses et deux
alertes ont déclenché un ZIP de 2 613 octets avec manifeste, empreinte du prompt
et empreinte du candidat. La preuve est
[`proofs/iteration-012-7.md`](proofs/iteration-012-7.md).

### Frontière conservée

Cette frontière historique a été fermée par le lot 3 : le candidat LLM est
persisté, comparé et soumis au même cycle de validation et de décision.
L’édition de zones personnalisées avec résolution de conflits a depuis été
implémentée. Le runner OCI isolé prévu au lot 4 reste à qualifier sur un hôte
disposant du runtime approprié.

## Incrément précédent — 012.6

Un cas confirmé produit désormais un artefact `code-generation-v1` contenant les
messages exacts demandant au LLM de générer le code, le workflow assaini, le
contrat de fichiers, les profils versionnés, le modèle et les skills appliqués.
L’artefact est signé par SHA-256. Toute valeur ciblant un champ HTML de type mot
de passe est remplacée par `<secret-value-redacted>` avant composition.

La page **Génération de code** expose la liste ordonnée des skills de chaque
profil ainsi que leur nom et leur source. Dans un cas confirmé, **Ouvrir le
prompt de génération** mène à une page de lecture seule structurée ; son JSON
exact est téléchargeable. **Télécharger le code généré** reste adjacent mais
distinct, afin que ni le prompt complet ni le source ne saturent le formulaire.
Le projet RH utilise `ollama-qwen36-128k-11436@1`, le modèle
`qwen3.6-35b-a3b-q4_K_M_128k:latest` et le profil
`python-playwright-qwen36-11436@1`.

Vérification du 2 août 2026 : tests ciblés `5 passed`, suite complète
`85 passed` avec `32 subtests`. Les routes réelles renvoient le prompt et le code
avec un workflow de 23 étapes. Dans le navigateur intégré, la configuration et
la page du prompt affichent les deux skills, les messages, l’empreinte et la
censure, sans fuite du mot de passe ni débordement horizontal. La preuve est
[`proofs/iteration-012-6.md`](proofs/iteration-012-6.md).

### Frontière conservée

Cet incrément prépare et expose la demande exacte au LLM ; il ne l’envoie pas
encore au fournisseur de génération. Le téléchargement de code actuel reste le
générateur déterministe Playwright existant. L’appel LLM, la validation de son
contrat JSON et la matérialisation contrôlée de sa réponse constituent la suite
de `GEN-003`.

## Incrément précédent — 012.5

La commande `seed-hr-demo-project` alimente désormais la base SQLite locale
avec le projet **Exemple — Bureau des Talents Intersidéraux**. Son arborescence
comprend le plan **Parcours RH de démonstration**, un dossier, deux suites et
deux cas confirmés : création/consultation de Zoé Nébuleuse en 23 étapes et
refus d’une connexion invalide. Le seeder est idempotent et resynchronise un
workflow devenu obsolète sans dupliquer le projet.

Le projet sélectionne désormais explicitement le profil
`ollama-qwen36-128k-11436@1` et son générateur compatible
`python-playwright-qwen36-11436@1`. Le 2 août 2026, Ollama sur
`127.0.0.1:11436` a répondu et son catalogue a confirmé la présence du modèle
`qwen3.6-35b-a3b-q4_K_M_128k:latest`. L’inférence de contrôle a produit le JSON
structuré attendu en 14,062 s. Qwen a ensuite relu le vrai brouillon nominal de
23 étapes en 33,5 s ; ses deux propositions restent visibles en attente dans le
dialogue, sans modification automatique du cas. Le mode opératoire reste
documenté dans [`llm/ollama.md`](llm/ollama.md) et l’exemple dans
[`hr-demo.md`](hr-demo.md).

Les deux classeurs XLSX sont liés aux cas et les catalogues rendent visibles les
champs HTML statiques, JavaScript et conditionnels. Depuis les pages de cas, les
deux candidats ont été téléchargés par les routes utilisateur puis exécutés tels
quels dans Chromium : `2 passed in 2.20s`. La suite complète réussit avec
`83 passed` et `30 subtests`.

Le premier essai a permis de remplacer un localisateur ARIA ambigu pour
l’alerte de refus par `[role="alert"]` suivi d’une assertion de texte. Cette
décision et la procédure d’installation sont documentées dans
[`hr-demo.md`](hr-demo.md). La preuve détaillée est
[`proofs/iteration-012-5.md`](proofs/iteration-012-5.md).

### Frontière conservée

Les XLSX restent visibles et attachés aux cas, mais la route de téléchargement
unitaire ne compose pas encore plusieurs sources tabulaires. Le projet matérialise
donc uniquement ses valeurs de démonstration synthétiques dans les workflows
exécutables. La génération multi-XLSX de référence reste disponible par CLI.

## Incrément précédent — 010.1

L’éditeur transforme maintenant chaque phrase de précondition en une carte
explicitement typée : condition vérifiable, fixture, dépendance technique,
préparation ou nettoyage. La carte conserve sa phrase source, sa description,
une éventuelle référence non secrète et sa confirmation humaine. Une modification
décoche cette confirmation. Le workflow version 2 refuse la confirmation finale
tant qu’une phrase n’est pas couverte ou qu’une carte reste non confirmée ; les
workflows historiques version 1 restent lisibles.

Le bouton **Vérifier la préparation** appelle un contrôle serveur déterministe et
détaille le profil d’environnement, l’origine de destination, les traductions,
les fixtures, la présence des références de secrets et le runtime Playwright.
Aucune valeur sensible n’est renvoyée. Pour un workflow v2, ces blocages sont
aussi vérifiés avant le téléchargement du candidat. Les traductions confirmées
sont conservées dans le code candidat et son manifeste.

Vérification du 1er août 2026 : tests ciblés `16 passed`, puis suite complète
`80 passed` avec `30 subtests`. Dans Chromium, le cas RH a affiché
**Préparation bloquée** avant la confirmation de sa carte, puis **Préparation
vérifiée** après confirmation, sans enregistrement du formulaire. La preuve est
[`proofs/iteration-010-1.md`](proofs/iteration-010-1.md).

### Frontière conservée

`ACC-033` est vérifié. `ACC-034` reste partiel jusqu’à ce que le runner isolé
répète ces contrôles immédiatement avant l’exécution. Les catalogues
administrables d’environnements et de données ainsi que l’exécution concrète des
préparations seront les prochaines verticales de la tranche 010.

## Catalogue des projets et arborescence unifiée

L’action **Modifier le projet** appartient désormais au **Catalogue**, à côté de
chaque projet. Son ouverture conserve la carte et son formulaire dans un même
bloc pleine largeur. La page du projet se consacre ainsi à une arborescence
éditable unique à quatre niveaux : **Plan (P) → Dossier (D) → Suite (S) → Cas
(C)**. Le plan forme la racine visible, son formulaire de modification est
intégré au bloc, et chaque bouton `+` crée l’enfant attendu à l’endroit où il
sera inséré.

Les créations et les actions sur les nœuds reviennent maintenant à l’ancre du
plan dans cette arborescence. Les fils d’Ariane et le bouton de retour de
l’éditeur de cas suivent la même règle. Les anciennes adresses de plan restent
disponibles pour les vues calculées et les favoris existants, mais ne font plus
partie du parcours principal.

Vérification du 1er août 2026 : tests ciblés `17 passed`, puis suite complète
`77 passed` avec `30 subtests`. Dans le navigateur intégré Chromium, le
formulaire de plan, l’ajout d’un dossier et le retour d’un cas vers l’ancre de
son plan ont été contrôlés sans mutation des données.

## Édition persistante des projets

Le **Catalogue** propose maintenant, à côté de chaque projet, un panneau
repliable **Modifier le projet**. Il permet de changer le nom, la description,
la cible web et la politique de sécurité avec les mêmes aides contextuelles que
le formulaire de création. La route `/projects/{project_id}/details` passe par
le service applicatif commun : les rôles `owner` et `editor` sont admis, le rôle
`viewer` est refusé et la persistance SQLite utilise le dépôt existant.

Toutes les valeurs obligatoires sont normalisées avant la première mutation pour
éviter un projet partiellement modifié. Le changement de cible ne réécrit pas les
cibles des plans existants ; cette décision préserve leur contexte d’exécution et
est signalée dans le formulaire, la documentation et le tutoriel.

Vérification du 1er août 2026 : tests ciblés `13 passed` avec `12 subtests`, puis
suite complète `77 passed` avec `30 subtests`. Dans le navigateur intégré
Chromium, une description temporaire a été enregistrée depuis le catalogue,
relue après rechargement depuis SQLite, puis la description initialement vide a
été restaurée. L’application a été redémarrée et reste disponible sur son port
local par défaut.

## Ajustement ergonomique — présentation globale et thèmes

Le patron introduit sur la page **Accès aux LLM** est désormais appliqué aux
catalogues de projets, plans de test, approches de test et profils de génération.
Chaque liste occupe toute la largeur ; un bouton `+` placé dessous révèle le
formulaire de création pleine largeur. Le composant partagé gère le focus initial,
le libellé `− Masquer le formulaire`, le repli par Échap et la conservation des
valeurs tant que la page n’est pas quittée. Les ajouts hiérarchiques du plan restent
près de leur parent et suivent déjà ce principe de dévoilement local.

L’en-tête propose sept thèmes : **Forêt**, **Océan**, **Prune**, **Coucher de
soleil**, **Graphite**, **Contraste élevé** et **Défense — ministère des Armées**.
Ils reposent sur les mêmes variables
CSS et le choix est mémorisé uniquement dans `localStorage`. Le script initial est
chargé avant la feuille de styles pour éviter un changement visible de palette au
chargement. Une valeur absente ou inconnue conserve le thème Forêt. La cible RH de
démonstration reste volontairement indépendante.

Le thème Défense reprend le bloc-marque DSFR v1.15.0 avec l’intitulé officiel
« Ministère des Armées et des Anciens combattants », les couleurs Bleu France et
Rouge Marianne et le pictogramme Rafale publié sur `defense.gouv.fr`. Les deux
ressources sont embarquées localement ; la police Arial remplace Marianne lorsque
cette police réglementée n’est pas distribuée. Les spécifications rappellent que
l’usage institutionnel est réservé aux entités autorisées.

Vérification du 2 août 2026 : les contrôles ciblés des ressources, de la
documentation et du sélecteur réussissent avec `4 passed` et `2 subtests`.
La suite complète atteint `83 passed` avec `32 subtests`, mais conserve deux
échecs hors du périmètre du thème dans l’éditeur de cas et la configuration de
génération de code. Dans le navigateur intégré, le thème Défense a été
contrôlé sur une largeur d’ordinateur puis à `390 × 844` : bloc-marque, navigation,
liseré tricolore, pictogramme et absence de débordement horizontal. Le choix est
resté actif après rechargement et les feuilles de style comme le SVG provenaient
uniquement de l’application locale.

Vérification du 1er août 2026 : syntaxe des trois scripts JavaScript, tests ciblés
`14 passed` avec `9 subtests`, puis suite complète `76 passed` avec `30 subtests`.
Dans le navigateur intégré Chromium, les cinq catalogues affichent leur bouton
d’ajout, l’ouverture donne le focus au premier champ, Échap replie le formulaire
et un brouillon est retrouvé à la réouverture. Le thème Prune est resté sélectionné
après navigation entre l’accueil, la documentation et les deux configurations ;
le thème Forêt a ensuite été restauré.

## Ajustement ergonomique — configurations séparées

L’écran combiné a été remplacé par deux destinations indépendantes :

- `/configuration/llm-access` pour les fournisseurs, endpoints, modèles,
  références d’authentification et diagnostics de connexion ;
- `/configuration/code-generation` pour les technologies, chemins, motifs de
  fichiers, garde-fous et validations du code produit.

La navigation principale, l’éditeur de cas, le tutoriel et la documentation
pointent directement vers la bonne responsabilité. Les créations et mises à
jour reviennent sur leur page d’origine. `/configuration/generation` demeure
une redirection compatible vers la configuration des accès LLM.

Vérification du 1er août 2026 : tests ciblés `5/5`, suite complète
`Ran 69 tests` puis `OK`. Le contrat vérifie aussi que chaque page ne rend pas
les formulaires propres à l’autre responsabilité et que les retours après
enregistrement utilisent la nouvelle destination. Un parcours dans le
navigateur intégré confirme les deux titres, les formulaires isolés, la
navigation croisée et l’absence d’erreur de console.

Le formulaire permanent placé à droite de **Accès aux LLM** a ensuite été
remplacé par un bouton `+` sous les connexions existantes. Le formulaire de
création est replié par défaut, occupe toute la largeur lorsqu’il est ouvert et
conserve sa saisie lors d’un simple repli. La revalidation couvre la syntaxe
JavaScript, `Ran 69 tests` puis `OK`, ainsi que l’ouverture, le focus, le repli
par Échap et la conservation de la saisie dans le navigateur intégré.

Le modèle d’un accès LLM est désormais choisi dans un catalogue chargé depuis
son URL de base. Le rafraîchissement est explicite, disponible en création et en
modification, borné à 30 secondes et n’enregistre aucune donnée. Les catalogues
Ollama (`/api/tags`) et compatibles OpenAI (`/models`) sont normalisés en une
liste triée ; le modèle courant n’est jamais remplacé silencieusement. La suite
complète passe avec `Ran 72 tests` puis `OK`. Le contrôle réel sur Ollama local
11434 a retourné trois modèles, et les parcours de création et de modification
ont été validés dans le navigateur sans soumettre de formulaire.

Le catalogue prend également en charge les en-têtes propres à Anthropic
(`x-api-key`, `anthropic-version`) et Azure OpenAI (`api-key`) sans étendre par
erreur ces protocoles à l’adaptateur de dialogue compatible OpenAI.

## Dernier incrément — 012.4

Cette phase réorganise la rédaction du cas autour d’un workflow canonique et de
trois représentations ergonomiques : formulaires action/contrôle, un texte par
étape et un récit complet. Les références de données deviennent une liste
extensible ; les résultats attendus restent attachés au contrôle qu’ils
décrivent. Un bouton ajoute un contrôle immédiatement après une action.

Trois skills locaux spécialisés cadrent l’analyse par un petit LLM. Leur contrat
ne permet que des questions et des propositions structurées à accepter : aucun
skill ne confirme le cas ou ne produit directement le code. Le mode et les
textes sources sont persistés dans `GenerationWorkflowInput` et visibles à tout
moment dans le JSON.

Le mode actif expose désormais le nom du skill, sa source, son prompt exact et
ses règles dans un panneau de traçabilité. Le parcours réel sur la cible RH a
confirmé l’accès aux trois cadrages, le téléchargement du code et son exécution
Chromium (`1 passed in 0.88s`).

Un cas confirmé expose désormais un téléchargement du candidat Python
Playwright, sans afficher son code dans la page. Le filtre du plan est replié par
défaut et se déplie automatiquement lorsqu’il est actif. La revue visuelle a
également corrigé les boutons radio initialement étirés par la règle CSS globale.

La suite produit et documentation réussit avec `66 passed` et 28 sous-tests.
Les trois skills sont valides et la bascule des modes, les ajouts en liste, le
JSON ainsi que le filtre ont été vérifiés dans le navigateur local. La preuve est
[`proofs/iteration-012-4.md`](proofs/iteration-012-4.md).

### Frontière conservée

Le code téléchargé est encore un candidat généré à la demande, pas un bundle
persisté et approuvé. L’inférence réelle du petit LLM et la réexécution des cas
Playwright générés avec le serveur RH actif restent hors de cette revue.

## Incrément précédent — 012.3

Cette phase remplace le catalogue manuel des champs dynamiques par une
exploration Playwright locale, authentifiée et bornée :

- plans JSON versionnés limités à 20 actions et 120 secondes ;
- actions et stratégies de localisation issues de listes fermées, sans
  JavaScript libre ni shell ;
- chargement d’une ligne XLSX nommée et résolution de jetons qualifiés en
  mémoire ;
- contrôle de l’origine locale après chaque action ;
- catalogue du DOM rendu sans conserver les valeurs saisies ni le HTML source ;
- comparaison entre HTML serveur relu dans la session et DOM après JavaScript ;
- trois preuves : connexion `6 → 7`, agent `18 → 22`, manager `20 → 25` ;
- application du catalogue à une copie du workflow en conservant les références
  stables et en refusant toute cible utilisée devenue absente ;
- workflow dérivé régénérant exactement le même code que le workflow de
  référence ;
- deux cas réels réussis dans Chromium en 4,738 secondes.

Les tests refusent également une origine distante, une action `javascript`, un
plan trop long et la suppression d’une référence utilisée. La suite complète
compte désormais 65 tests.

Le guide opératoire est [`hr-demo.md`](hr-demo.md), le tutoriel applicatif est
accessible depuis l’accueil sous **Tutoriel de rédaction**, et le scénario 10 de
[`tutorial-local.html`](tutorial-local.html) donne les commandes reproductibles.
Les choix et limites sont détaillés dans
[`design/iteration-012-3-introspection.md`](design/iteration-012-3-introspection.md).
La preuve est [`proofs/iteration-012-3.md`](proofs/iteration-012-3.md).

### Frontière conservée

L’exploration authentifiée est actuellement un outil CLI séparé. L’intégration
dans l’éditeur, les cibles distantes autorisées, les vrais secrets, les iframes,
le shadow DOM fermé et l’exécution dans un worker isolé restent à réaliser.

## Incrément précédent — 012.2

Cette phase d’approfondissement transforme la preuve nominale en chaîne
auditable :

- remplacement de la fusion implicite des premières lignes par
  `data_sources` et `data_cases` ;
- références qualifiées comme `{{data.login.email}}` et
  `{{data.employee.first_name}}` ;
- refus des matrices incomplètes, identifiants dupliqués et chemins non sûrs ;
- paramétrage pytest de deux associations explicitement nommées ;
- manifeste déterministe avec empreintes du workflow, du code et des XLSX ;
- contrôle des empreintes des classeurs avant la collecte ;
- commande `run-playwright` limitée à `tests/generated` et à une cible locale ;
- refus d’un code modifié après génération ;
- lancement de pytest sans shell et avec délai global ;
- production de JUnit, `execution.json` et journaux séparés ;
- troisième ligne XLSX ajoutée et contrôle visuel de toutes les feuilles.

Le résultat réel est `2 passed in 3.86s` dans Chromium : Zoé Nébuleuse et Iris
Comète sont deux cas collectés séparément, avec zéro échec. Le rapport
`outputs/hr-demo/execution-012-2/execution.json` conserve le code de sortie,
la durée et les empreintes exécutées.

Les raisons, solutions écartées et frontières sont détaillées dans
[`design/iteration-012-2-introspection.md`](design/iteration-012-2-introspection.md).
La preuve technique est
[`proofs/iteration-012-2.md`](proofs/iteration-012-2.md).

### Frontière conservée

Cette validation locale ne vérifie pas `ENF-005` : elle ne possède encore ni
conteneur non privilégié, ni racine en lecture seule, ni filtrage réseau par
origine. Elle ne revendique donc aucun des critères complets du runner
`ACC-017` à `ACC-025`. Son utilité est la validation individuelle rapide et
traçable du candidat avant le futur passage dans le runner OCI.

## Incrément précédent — 012.1

La première verticale exécutable de la tranche `012` fournit un banc d’essai
RH complet et la matérialisation déterministe d’un scénario Playwright :

- trois pages intégrées sous `/demo/hr` : connexion, saisie et consultation ;
- esthétique volontairement loufoque et HTML de qualité variable ;
- champs statiques, injectés par JavaScript, créés dans un composant Web et
  rendus conditionnellement selon la session manager ;
- deux classeurs XLSX stylés, importables par le produit et reproductibles par
  script ;
- workflow confirmé décrivant trois catalogues de page et 23 étapes ;
- générateur Python `pytest-playwright` accessible par la commande
  `generate-playwright` ;
- chargement des valeurs depuis les XLSX au moment du test, sans les recopier
  dans le code ;
- localisateurs par libellé, rôle, identifiant de test et CSS ;
- exécution réelle de la connexion, de la saisie, de la redirection et des
  validations dans Chromium.

Le guide demandé est [`hr-demo.md`](hr-demo.md). Il documente les comptes
synthétiques, la matrice des technologies de champs, les URLs d’analyse, les
deux classeurs, la structure de génération et toutes les commandes.

### Vérification et limites

- suite complète : `Ran 55 tests` puis `OK` ;
- scénario généré : `1 passed in 4.40s` avec Chromium 149 ;
- inspection visuelle : connexion en ordinateur et mobile, formulaire manager
  en mobile, champs JavaScript et conditionnels présents ;
- défaut de débordement horizontal mobile détecté pendant la revue puis
  corrigé ; largeur finale du document `382 px` pour un viewport `390 px` ;
- l’analyseur HTML demeure statique : il n’exécute pas le JavaScript et
  n’établit pas de session ;
- cette verticale ne génère que Python avec `pytest-playwright` et consomme la
  première ligne des classeurs.

La tranche `012` reste **En cours** : la paramétrisation multi-lignes, les
autres technologies configurables, le bundle complet et le cycle
candidat/approbation ne sont pas encore implémentés. La preuve est
[`proofs/iteration-012-1.md`](proofs/iteration-012-1.md).

## Incrément précédent — 009.3

La troisième verticale de la tranche `009` rend le profil Ollama local
reproductible et testable :

- installation réelle d’Ollama `0.32.5` et vérification du port par défaut
  `127.0.0.1:11434` ;
- téléchargement du tag officiel `qwen3.6:35b-a3b-q4_K_M` d’environ 24 Go ;
- création par Modelfile de l’alias exact
  `qwen3.6-35b-a3b-q4_K_M_128k:latest` avec `num_ctx 131072` ;
- profil versionné relié au profil de génération Python Playwright ;
- sonde d’interface utilisable avant activation, sans contenu métier, qui
  exige le contrat JSON du dialogue ;
- limites de sortie distinctes pour la sonde et le dialogue, avec raisonnement
  Ollama désactivé ;
- trois amorces ergonomiques pour développer le cas complet, exploiter les
  champs HTML ou renforcer les validations ;
- contrat détaillant la forme exacte d’une étape, les énumérations, les chemins,
  un exemple valide et les garde-fous contre les valeurs secrètes, les URL
  inventées et les redirections transformées en navigation ;
- cas de connexion réellement développé par Qwen en quatre opérations
  applicables, puis validé par le parseur strict de l’application ;
- documentation intégrée et tutoriel complétés ;
- instantanés datés de quatre pages officielles Ollama, avec empreintes
  contrôlées par test.

Le guide demandé est
[`llm/ollama.md`](llm/ollama.md). Il documente l’installation, le profil, les
commandes de test, le résultat réel, le diagnostic matériel et le parcours
complet de rédaction assistée. Les sources conservées sont inventoriées dans
[`vendor/ollama/SOURCES.md`](vendor/ollama/SOURCES.md).

### Vérification et limite

- service Ollama et présence du modèle : réussis ;
- diagnostic JSON avec le même alias à 4 096 jetons : réussi en 112,3 secondes ;
- profil 128K exact : échec après 600 secondes avant la fin du chargement ;
- tests automatisés : `Ran 51 tests` puis `OK` ;
- compilation Python et syntaxe JavaScript : réussies ;
- point d’entrée CLI réel : santé et ancienne page combinée en HTTP 200, modèle
  exact, bouton de sonde et état désactivé visibles ;
- inspection navigateur de cette verticale : non réalisée, car le navigateur
  intégré a bloqué les URL locales avec `ERR_BLOCKED_BY_CLIENT`.

Le profil 128K reste donc **désactivé**. Le succès à contexte réduit ne valide
pas sa capacité déclarée et `ACC-057` n’est pas revendiqué. L’application et le
contrat sont vérifiés automatiquement, mais l’inférence 128K exige davantage de
mémoire disponible, un autre matériel ou un modèle plus petit explicitement
choisi par l’utilisateur.

## Incrément précédent — 009.2

La deuxième verticale de la tranche `009` est vérifiée :

- dialogue contextualisé conservé avec le cas et restauré depuis SQLite ;
- résolution de la version exacte du profil LLM avant l’appel ;
- contexte minimisé : brouillon, intention, diagnostic, capacités HTML sans
  HTML brut ni localisateur et huit derniers messages ;
- contrat de sortie fermé, borné à huit questions et douze opérations ;
- refus complet d’une sortie mal formée ou visant une page, un profil ou
  `workflow.confirmed` ;
- empreinte du brouillon empêchant l’application d’une proposition obsolète ;
- présentation séparée de chaque opération, de son chemin, de sa valeur et de sa
  justification ;
- acceptation sélective avec états persistés `accepted` et `rejected` ;
- reconstruction déterministe de la description depuis les seules données
  acceptées ;
- adaptateur HTTP compatible OpenAI utilisé par OpenAI, Mistral, Ollama et les
  endpoints compatibles, avec résolution tardive du secret ;
- documentation fonctionnelle, infobulles et tutoriel mis à jour.

Les critères `ACC-007`, `ACC-008` et `ACC-009` sont vérifiés. La tranche `009`
reste `En cours` uniquement parce que `ACC-032` couvre aussi les modèles de cas,
types, tags et environnements administrables, qui ne sont pas tous implémentés.
Le contrôle de connexion et de capacités d’un fournisseur réel reste dans les
critères `ACC-056` à `ACC-059` et n’est pas revendiqué par cette verticale.

## Incrément précédent — 008.2

La configuration nécessaire à la future génération de code est disponible sans
modifier le code de l'application :

- création et versionnement des profils d'accès LLM ;
- prise en charge des fournisseurs OpenAI, Azure OpenAI, Anthropic, Mistral,
  Ollama et des API compatibles OpenAI ;
- référencement des secrets uniquement par nom de variable d'environnement ;
- création et versionnement des profils de génération de code ;
- configuration du langage, du framework, des chemins, des motifs de fichiers,
  des preuves, de la politique d'écriture, des validations et des instructions ;
- liaison d'un cas de test à des références exactes `identifiant@version` ;
- refus d'une liaison incohérente entre le profil LLM et le profil de génération ;
- persistance YAML atomique des profils et restauration des références du
  workflow depuis SQLite ;
- consultation et modification depuis les pages `Accès aux LLM` et
  `Génération de code`, avec aides de saisie et affichage adapté aux écrans
  mobiles.

La vérification du 28 juillet 2026 couvre :

- la suite complète : `Ran 41 tests` puis `OK` ;
- la compilation Python et la vérification syntaxique du JavaScript ;
- le contrôle du diff ;
- un parcours réel dans le navigateur pour créer un accès LLM puis un profil de
  génération, en affichage ordinateur et mobile ;
- la vérification qu'aucune valeur de secret envoyée au formulaire n'est
  persistée ou réaffichée.

### Limite actuelle

Cette tranche configurait les paramètres d'entrée du workflow. La finalisation
assistée et l’appel borné de conception ont depuis été ajoutés par `009.2`.
Le contrôle de connexion et de capacités du fournisseur ainsi que la
matérialisation des fichiers de test restent à implémenter ; ils ne sont pas
comptés comme vérifiés au titre de `EF-003`, des critères `ACC-056` à
`ACC-059` ou de la tranche `012`.


## Contrat de preuve

Chaque fichier de preuve enregistre :

```text
Spécifications :
Acceptation :
Fichiers modifiés :
Test RED :
Test GREEN :
Suite complète :
Point d'entrée réel :
Limites externes :
Revue sécurité :
```
