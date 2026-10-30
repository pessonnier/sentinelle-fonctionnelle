# Spécifications du plugin Firefox d’aide à la conception des tests

> Statut : brouillon de travail à adapter  
> Priorité proposée : MVP `P0`, enrichissements `P1`, prospective `P2`  
> Application cible : Sentinelle Fonctionnelle  
> Format d’échange courant : `GenerationWorkflowInput`, schéma version 2

## 1. Objet

Le plugin Firefox doit permettre à un concepteur fonctionnel de parcourir une
application web, de sélectionner les éléments utiles, d’enregistrer les actions
et les contrôles attendus, puis de transférer un **brouillon structuré** vers un
cas de test Sentinelle Fonctionnelle.

Le plugin ne remplace ni la revue du cas, ni sa confirmation, ni la génération
du candidat Playwright. Il réduit le travail manuel nécessaire pour constituer :

- le catalogue des pages et des éléments ;
- les étapes fonctionnelles ;
- les données saisies et les valeurs attendues ;
- les premières assertions observables ;
- les preuves et diagnostics utiles à la conception.

## 2. Principes directeurs

1. **Capture explicite** : aucune page n’est inspectée avant une action claire
   de l’utilisateur.
2. **Brouillon avant confirmation** : un import du plugin ne doit jamais créer
   silencieusement un workflow confirmé.
3. **Localisateurs lisibles** : rôle accessible, libellé et identifiant de test
   sont préférés aux sélecteurs CSS structurels.
4. **Données séparées du scénario** : les valeurs réutilisables deviennent des
   jetons `{{data.*}}`, `{{fixture.*}}` ou `{{secret.*}}`.
5. **Aucun secret capturé** : mots de passe, jetons, cookies et en-têtes
   d’autorisation sont exclus par défaut.
6. **Traçabilité** : chaque élément importé indique sa page, son origine de
   capture et son empreinte.
7. **Moindre privilège** : le plugin demande l’accès uniquement à l’onglet ou à
   l’origine que l’utilisateur a choisi.

## 3. Liens avec l’application actuelle

### 3.1 Capacités déjà disponibles dans Sentinelle

| Capacité actuelle | Point d’ancrage | Utilisation par le plugin |
|---|---|---|
| Éditeur guidé d’un cas | `web/templates/case_guided.html` | Destination du brouillon importé et surface de revue finale |
| Analyse HTML d’une page | `POST .../cases/{case_id}/page-analysis` | Contrat de référence pour les pages et éléments analysés |
| Contrôle de préparation | `POST .../cases/{case_id}/readiness` | Vérification du brouillon avant confirmation |
| Modèle de workflow | `domain/workflow.py` | Contrat cible pour les pages, étapes, actions et assertions |
| Génération du candidat | `web/generation_routes.py` | Étape ultérieure, après revue et confirmation humaine |
| Zones de code protégées | `application/code_customization.py` | Extension manuelle après génération, hors capture navigateur |
| Démonstrateur multi-écrans | `/demo/commandes/client` | Cible de recette principale du plugin |

L’analyse de page actuelle est initiée par le serveur à partir d’une URL. Le
plugin apporte une capacité complémentaire : il observe le DOM réellement
affiché dans l’onglet, après les interactions et les traitements JavaScript.

### 3.2 Modèle de domaine cible

Le plugin doit produire des données compatibles avec les structures actuelles :

- `AnalyzedPage` : `url`, `title`, `fingerprint`, `elements` ;
- `PageElement` : `reference`, `kind`, `role`, `label`, `input_type`,
  `locator`, `options` ;
- `WorkflowStep` : `id`, `name`, `page_url`, `precondition`, `action`,
  `target`, `value`, `assertion`, `assertion_target`, `expected`, `evidence` ;
- `GenerationWorkflowInput` : contexte d’exécution, pages, étapes, données,
  profils et état de confirmation.

Actions actuellement acceptées :

`navigate`, `click`, `fill`, `select`, `check`, `uncheck`, `upload`, `wait`,
`none`.

Assertions actuellement acceptées :

`visible`, `hidden`, `text`, `value`, `url`, `count`, `enabled`, `checked`,
`none`.

Le plugin ne doit pas inventer une action ou une assertion supplémentaire sans
évolution préalable du schéma applicatif.

### 3.3 Exemple de correspondance avec le Comptoir des commandes

| Écran observé | Capture plugin | Objet Sentinelle produit |
|---|---|---|
| Client | nom, e-mail, type, date, priorité, instructions | une page analysée et des étapes `fill`, `select`, `check` |
| Articles | quantités du tableau, livraison, remise, emballage | éléments de tableau, étapes `fill`, `select`, `check` |
| Récapitulatif | sous-total, remise, TVA, total | assertions `text` sur des valeurs calculées |
| Suivi | statut et lignes d’articles | assertions `text` et `count` en lecture seule |

Le scénario nominal de recette doit retrouver le total `287.12 €`, le statut
`Confirmée` et deux lignes d’articles.

## 4. Utilisateurs et parcours principal

### 4.1 Utilisateur principal

Le concepteur de tests connaît le comportement métier attendu, mais ne maîtrise
pas nécessairement les sélecteurs CSS ou Playwright.

### 4.2 Parcours nominal

1. Le concepteur ouvre un cas de test dans Sentinelle.
2. Il associe le plugin à l’instance locale et sélectionne le projet, le plan et
   le cas.
3. Il ouvre l’application cible et démarre une session de capture.
4. Il sélectionne ou manipule les champs de la page.
5. Le plugin propose des étapes, des références et des assertions.
6. Le concepteur transforme les valeurs variables en données de test.
7. Il relit le scénario dans le panneau Firefox.
8. Il envoie un brouillon vers Sentinelle.
9. Sentinelle valide le schéma, affiche les différences et demande une
   confirmation humaine dans l’éditeur guidé.
10. La génération de code reste une action distincte dans Sentinelle.

## 5. Priorisation

### 5.1 Définitions

- `P0` : indispensable à une première version utilisable de bout en bout.
- `P1` : améliore fortement la qualité et la productivité après validation du
  socle.
- `P2` : fonction avancée ou dépendante d’évolutions supplémentaires.
- `Hors périmètre initial` : explicitement exclu du premier plugin.

### 5.2 Vue synthétique

| Priorité | Lot | Résultat attendu |
|---|---|---|
| P0 | Association à Sentinelle | instance locale et cas de destination sélectionnés |
| P0 | Inventaire de page | champs et contrôles convertis en `PageElement` |
| P0 | Enregistrement des actions | parcours multi-écrans converti en `WorkflowStep` |
| P0 | Assertions assistées | résultat observable ajouté sans écrire de code |
| P0 | Données et masquage | valeurs variables et sensibles correctement traitées |
| P0 | Revue et import | brouillon envoyé, validé et fusionné sans écrasement |
| P1 | Réseau et console | requêtes, erreurs et HAR associés aux étapes |
| P1 | Jeux de données avancés | cas limites et partitions proposés |
| P1 | Preuves visuelles | captures d’écran rattachées aux étapes |
| P1 | Composants complexes | modales, tableaux, autocomplétion et iframes |
| P2 | Rejeu dans Firefox | diagnostic pas-à-pas avant génération Playwright |
| P2 | Assistance LLM | suggestions contrôlées à partir du brouillon assaini |
| P2 | Collaboration | partage et comparaison de sessions de capture |

## 6. Spécifications fonctionnelles P0

### FP-001 — Associer le plugin à Sentinelle

Le plugin permet de déclarer une instance Sentinelle, par défaut
`http://127.0.0.1:8000`, puis de sélectionner un projet, un plan et un cas.

Exigences :

- tester `/health` avant l’association ;
- afficher clairement l’origine connectée ;
- mémoriser localement l’origine et les identifiants, jamais une valeur secrète ;
- distinguer une instance indisponible, incompatible ou non autorisée ;
- exiger une nouvelle sélection si le cas n’existe plus.

### FP-002 — Démarrer et arrêter une session de capture

Une session possède un identifiant, une date, l’URL initiale, l’origine cible et
le cas Sentinelle associé.

États proposés : `inactive`, `recording`, `paused`, `review`, `sent`.

L’arrêt de la capture ne doit pas envoyer automatiquement le brouillon.

### FP-003 — Inventorier la page affichée

Le plugin collecte pour chaque élément utile :

- balise, type d’entrée, rôle accessible et nom accessible ;
- libellé, `id`, `name`, `data-testid` et options d’un `select` ;
- visibilité, activation et état coché ;
- appartenance à un formulaire, un tableau, une modale ou une iframe ;
- URL, titre et empreinte stable de la page.

Les champs cachés, décoratifs ou sans intérêt fonctionnel restent exclus sauf
activation explicite d’un mode avancé.

### FP-004 — Proposer un localisateur robuste

Ordre de préférence proposé :

1. rôle accessible et nom stable ;
2. libellé associé ;
3. `data-testid` ou attribut de test explicitement configuré ;
4. identifiant HTML stable ;
5. texte stable ;
6. sélecteur CSS minimal en dernier recours.

Chaque proposition indique : stratégie, valeur, unicité, motifs de fragilité et
score de robustesse. Le concepteur peut choisir une autre proposition avant
l’import.

La sortie finale reste limitée aux stratégies comprises par le générateur
actuel, notamment `role`, `label`, `test_id` et `css`.

### FP-005 — Enregistrer les actions utilisateur

Le plugin traduit les interactions en actions du workflow existant :

| Interaction Firefox | Action Sentinelle |
|---|---|
| changement complet de document | `navigate` ou résultat d’un `click` précédent |
| clic sur bouton ou lien | `click` |
| saisie de texte, nombre, date | `fill` |
| changement d’une liste | `select` |
| activation d’une case ou radio | `check` |
| désactivation d’une case | `uncheck` |
| sélection d’un fichier | `upload`, sans capturer son contenu |
| attente explicitement ajoutée | `wait` |

Les frappes successives dans un même champ sont regroupées en une seule étape
`fill`. Les événements techniques sans valeur fonctionnelle sont ignorés.

### FP-006 — Suivre un parcours multi-écrans

Le plugin détecte les changements de document, conserve les pages déjà connues
et ajoute chaque nouvelle page au catalogue de la session.

Il doit :

- préserver l’ordre des étapes ;
- éviter de dupliquer une page dont l’empreinte est inchangée ;
- signaler une même URL avec une empreinte différente ;
- distinguer une navigation complète d’un changement dynamique sans rechargement ;
- conserver la relation entre l’action déclenchante et l’écran obtenu.

### FP-007 — Ajouter une assertion assistée

Après une action, l’utilisateur peut sélectionner un élément et choisir une
assertion compatible avec le modèle actuel.

Le plugin propose par contexte :

- `visible` ou `hidden` pour un composant ;
- `text` pour un titre, message, cellule ou montant ;
- `value` pour un champ ;
- `url` après navigation ;
- `count` pour les lignes d’un tableau ou une collection ;
- `enabled` pour une commande ;
- `checked` pour une case ou un bouton radio.

Une assertion proposée n’est ajoutée qu’après confirmation dans le panneau.

### FP-008 — Constituer les données de test

Pour chaque valeur saisie ou attendue, le concepteur choisit :

- constante conservée dans l’étape ;
- donnée réutilisable `{{data.<nom>}}` ;
- fixture `{{fixture.<nom>}}` ;
- secret `{{secret.<nom>}}`, dont seule la référence est conservée ;
- valeur ignorée ou remplacée.

Le plugin vérifie l’unicité des noms, propose un nom à partir du champ et affiche
toutes les étapes qui réutilisent la donnée.

### FP-009 — Protéger les données sensibles

Le plugin ne conserve jamais automatiquement :

- la valeur d’un champ `password` ;
- cookies ou stockage d’authentification ;
- en-têtes `Authorization`, `Proxy-Authorization` ou équivalents ;
- jetons détectés dans une URL ou un corps de requête ;
- contenu du fichier choisi lors d’un téléversement.

Une valeur suspecte est remplacée par une référence de secret ou par
`<redacted>`. L’interface indique la raison du masquage.

### FP-010 — Relire et modifier le brouillon

Avant l’envoi, le panneau présente :

- le contexte Sentinelle sélectionné ;
- la liste des pages et leurs empreintes ;
- les étapes ordonnées ;
- les données, fixtures et secrets référencés ;
- les localisateurs fragiles ou ambigus ;
- les étapes dépourvues d’assertion ;
- les valeurs masquées.

Le concepteur peut renommer, réordonner, supprimer ou désactiver une étape et
modifier les assertions sans quitter le panneau.

### FP-011 — Prévisualiser la fusion avec le cas

L’envoi commence par une prévisualisation côté serveur. Sentinelle retourne :

- les pages et étapes ajoutées ;
- les éléments mis à jour ;
- les conflits de références ou d’empreintes ;
- les informations de contexte manquantes ;
- le résultat du contrôle de préparation.

Aucune donnée existante n’est écrasée à cette étape.

### FP-012 — Importer comme brouillon non confirmé

Après validation explicite, Sentinelle crée une nouvelle version de la
spécification avec :

- `schema_version: 2` ;
- `authoring_mode: form` ;
- `confirmed: false` ;
- les pages et étapes importées ;
- une provenance `firefox-extension` et l’identifiant de capture dans les
  métadonnées d’audit à ajouter.

La confirmation définitive reste effectuée depuis l’éditeur de cas Sentinelle.
L’import ne génère et n’exécute aucun candidat.

### FP-013 — Exporter sans connexion

Si Sentinelle est indisponible, le plugin peut télécharger un fichier JSON
`sentinelle-browser-capture-v1`. Ce fichier est assaini et peut être importé
ultérieurement par l’application.

## 7. Spécifications fonctionnelles P1

### FP-101 — Capturer le contexte réseau

Un panneau DevTools peut associer aux étapes les requêtes terminées, leur
méthode, leur URL assainie, leur statut et leur durée. Un export HAR reste une
preuve optionnelle et séparée du workflow.

Le plugin propose sans l’imposer :

- une assertion de statut HTTP ;
- le repérage d’une requête en erreur ;
- une donnée extraite d’une réponse JSON non sensible ;
- le temps de réponse comme information diagnostique.

### FP-102 — Capturer les erreurs de console

Les erreurs JavaScript survenues entre deux étapes peuvent être rattachées à
l’étape active. Les messages sont assainis avant conservation.

### FP-103 — Générer des variantes de données

À partir du type HTML et des contraintes `min`, `max`, `minlength`, `maxlength`,
`pattern` et `required`, le plugin propose :

- valeur nominale ;
- valeur vide ;
- bornes minimale et maximale ;
- valeur juste en dehors des bornes ;
- format invalide ;
- option alternative d’une liste.

Ces propositions alimentent un jeu de données ; elles ne créent pas
automatiquement plusieurs cas de test.

### FP-104 — Capturer des preuves visuelles

Une capture peut être associée à une étape marquée `evidence: true`. Les zones
sensibles sont masquées avant l’enregistrement.

### FP-105 — Reconnaître les composants complexes

Le plugin traite explicitement les modales, onglets, autocomplétions, tableaux
paginés, menus personnalisés et composants encapsulés dans un Shadow DOM
accessible.

Les iframes d’une autre origine exigent une permission distincte et doivent être
signalées dans la revue.

### FP-106 — Comparer le DOM à une capture précédente

Lors d’une nouvelle capture du même cas, le plugin indique les éléments absents,
ajoutés, renommés ou dont le localisateur est devenu ambigu. Il ne modifie pas le
workflow sans décision humaine.

## 8. Spécifications fonctionnelles P2

### FP-201 — Rejouer localement le brouillon

Le plugin peut rejouer les étapes dans un onglet dédié pour détecter une cible
introuvable ou une assertion impossible. Ce rejeu ne remplace pas l’exécution du
candidat Playwright et ne produit pas une validation Sentinelle.

### FP-202 — Assistance LLM contrôlée

Une assistance optionnelle peut proposer des noms d’étapes, des regroupements et
des assertions. Seul le brouillon assaini est transmis, selon le profil LLM du
cas. Chaque proposition reste visible et révocable.

### FP-203 — Sessions collaboratives

Une session peut être exportée, comparée ou fusionnée avec une autre capture. La
collaboration en ligne dépendra du futur mode partagé et de son authentification.

## 9. Interface utilisateur proposée

### 9.1 Panneau principal

Un panneau DevTools **Sentinelle** contient cinq onglets :

1. **Contexte** : instance, projet, plan, cas et état de connexion ;
2. **Capture** : démarrage, pause, page courante et dernier événement ;
3. **Étapes** : scénario ordonné et assertions ;
4. **Données** : constantes, variables, fixtures, secrets et masquages ;
5. **Revue** : alertes, prévisualisation et envoi.

Une barre latérale Firefox simplifiée peut afficher l’état de la capture pendant
que les DevTools sont fermés. Elle reste une amélioration et ne duplique pas tout
l’éditeur.

### 9.2 Mode sélection

Quand l’utilisateur active **Sélectionner un élément**, le plugin surligne
l’élément survolé et affiche :

- nom accessible et rôle ;
- référence Sentinelle proposée ;
- localisateur choisi et alternatives ;
- type d’action ou d’assertion possible ;
- avertissement si l’élément est ambigu ou sensible.

La surbrillance ne modifie pas durablement la page.

### 9.3 Retours et erreurs

Les erreurs sont actionnables : permission manquante, origine non autorisée,
instance indisponible, cas supprimé, schéma incompatible, référence en conflit,
localisateur ambigu ou donnée sensible masquée.

## 10. Contrat d’échange proposé

Le plugin ne doit pas appeler directement les formulaires HTML actuels. Une API
versionnée dédiée est nécessaire, car les mutations web existantes appliquent
une politique de même origine et sont conçues pour l’interface serveur.

### 10.1 Endpoints à ajouter dans Sentinelle

| Méthode et route proposée | Rôle | Priorité |
|---|---|---|
| `GET /api/v1/browser-extension/capabilities` | versions et fonctions disponibles | P0 |
| `POST /api/v1/browser-extension/pairings` | créer une association locale courte | P0 |
| `GET /api/v1/browser-extension/contexts` | lister projets, plans et cas autorisés | P0 |
| `POST /api/v1/browser-extension/captures/preview` | valider et prévisualiser la fusion | P0 |
| `POST /api/v1/browser-extension/captures/import` | créer le brouillon après confirmation | P0 |
| `POST /api/v1/browser-extension/captures/{id}/artifacts` | joindre HAR ou capture assainie | P1 |

### 10.2 Association locale

Proposition pour le mode local :

1. Sentinelle affiche un code d’association court, à usage unique et expirant ;
2. l’utilisateur le saisit dans le plugin ;
3. le serveur retourne un jeton local limité aux opérations du plugin ;
4. le jeton est lié à l’origine Sentinelle et peut être révoqué ;
5. aucune authentification de l’application cible n’est transmise.

Le futur mode en ligne devra utiliser son mécanisme d’identité et d’autorisation,
sans réutiliser le protocole local comme authentification distante.

### 10.3 Enveloppe JSON

```json
{
  "schema_version": 1,
  "capture_id": "capture-2026-10-29-001",
  "source": "firefox-extension",
  "target": {
    "project_id": "...",
    "test_plan_id": "...",
    "case_id": "..."
  },
  "captured_at": "2026-10-29T16:00:00+01:00",
  "browser": {
    "name": "Firefox",
    "extension_version": "0.1.0"
  },
  "workflow_patch": {
    "schema_version": 2,
    "authoring_mode": "form",
    "confirmed": false,
    "pages": [],
    "steps": []
  },
  "data": {
    "values": {},
    "fixture_refs": [],
    "secret_refs": []
  },
  "warnings": []
}
```

Le serveur reconstruit le domaine avec `GenerationWorkflowInput.from_mapping`
et refuse tout champ, type ou taille non autorisé. Le plugin ne décide jamais à
la place du serveur qu’un document est valide.

## 11. Architecture technique proposée

### 11.1 Composants Firefox

- `manifest.json` Manifest V3 ;
- page DevTools et panneau Sentinelle ;
- content script injecté après action utilisateur ;
- script d’arrière-plan pour les messages et les appels à Sentinelle ;
- stockage local asynchrone pour les brouillons ;
- module partagé de sérialisation et d’assainissement.

### 11.2 Permissions minimales

Socle proposé :

- `activeTab` : accès temporaire à l’onglet explicitement choisi ;
- `scripting` : injection contrôlée du content script ;
- `storage` : conservation locale des brouillons ;
- `downloads` : export JSON hors connexion, si retenu ;
- `devtools` : panneau, de préférence facultatif si le parcours le permet ;
- permissions d’hôtes optionnelles demandées origine par origine.

Éviter `<all_urls>` dans le MVP.

### 11.3 Communications internes

Le content script lit le DOM et transmet uniquement des objets sérialisables au
script d’arrière-plan. Le panneau DevTools ne contacte pas directement la page
cible. L’appel vers Sentinelle passe par le script d’arrière-plan afin de gérer
les permissions, les erreurs réseau et l’association locale.

### 11.4 Limites Firefox à intégrer

- les pages privilégiées Firefox et certaines origines Mozilla ne sont pas
  inspectables par un content script ;
- un accès `activeTab` est révoqué lors d’une nouvelle navigation de document
  dans Firefox ; la capture multi-écrans peut donc exiger une permission d’hôte
  accordée pour la durée de la session ;
- les iframes d’une autre origine ne sont pas couvertes sans permission dédiée ;
- l’API DevTools ne fournit pas exactement toutes les fonctions de Chromium.

## 12. Sécurité et confidentialité

### 12.1 Menaces principales

- capture involontaire de données personnelles ou de secrets ;
- page hostile tentant de tromper le plugin ;
- import d’un JSON forgé ;
- accès trop large à l’historique de navigation ;
- transmission à une fausse instance Sentinelle ;
- rejeu d’un code d’association ;
- conservation trop longue de captures ou HAR.

### 12.2 Mesures obligatoires P0

- permissions limitées et révocables ;
- activation manuelle par onglet ou origine ;
- validation complète côté serveur ;
- association expirante et origine Sentinelle visible ;
- masquage des secrets avant stockage et transmission ;
- limite de taille par capture ;
- absence de code distant dans l’extension ;
- journal local des imports sans contenu sensible ;
- bouton de suppression de la session locale ;
- politique de rétention explicite.

## 13. Exigences non fonctionnelles

### ENF-PF-001 — Performance

L’inventaire d’une page courante ne doit pas bloquer l’interface. La collecte
doit être incrémentale sur les pages volumineuses et ignorer les sous-arbres non
pertinents.

### ENF-PF-002 — Accessibilité

Le panneau est utilisable au clavier, expose des libellés accessibles et ne
communique aucune information uniquement par la couleur.

### ENF-PF-003 — Robustesse

Une fermeture de DevTools ou un rechargement du panneau ne doit pas perdre une
session enregistrée. Une navigation inattendue produit un avertissement et non
un brouillon corrompu.

### ENF-PF-004 — Compatibilité

Le MVP cible Firefox bureau et Manifest V3. Toute compatibilité Chromium est
secondaire et ne doit pas dégrader la sécurité ou les fonctions Firefox.

### ENF-PF-005 — Auditabilité

Chaque import indique l’identifiant de capture, la version du plugin, la date,
les pages capturées et les avertissements acceptés.

## 14. Critères d’acceptation P0

1. Le plugin se connecte à une instance locale disponible et refuse une instance
   dont les capacités sont incompatibles.
2. L’utilisateur sélectionne explicitement un projet, un plan et un cas.
3. Le plugin catalogue les quatre pages du Comptoir des commandes.
4. Les champs texte, e-mail, date, liste, radio, case et quantités du tableau
   obtiennent une référence et un localisateur relus.
5. Le parcours produit uniquement des actions actuellement admises par
   `WorkflowAction`.
6. Le total `287.12 €`, le statut `Confirmée` et le nombre de lignes peuvent être
   capturés comme assertions existantes.
7. Le mot de passe d’une cible de recette n’apparaît ni dans le stockage local,
   ni dans l’export, ni dans l’import.
8. La prévisualisation signale les localisateurs ambigus et les références en
   conflit.
9. L’import crée un workflow `confirmed: false` et n’écrase pas silencieusement
   un workflow confirmé.
10. Le brouillon importé est accepté par `GenerationWorkflowInput.from_mapping`.
11. Le contrôle de préparation Sentinelle indique les informations encore
    manquantes avant confirmation.
12. Aucun candidat n’est généré ou exécuté par l’import du plugin.
13. Après revue dans Sentinelle, le scénario peut suivre le cycle existant :
    confirmation, génération, personnalisation protégée, exécution et décision.

## 15. Hors périmètre du MVP

- exécution autonome de Playwright dans le plugin ;
- contournement de l’authentification ou des protections du site cible ;
- collecte générale de l’historique Firefox ;
- enregistrement des mots de passe, cookies ou jetons ;
- génération automatique d’un candidat approuvé ;
- modification directe des zones `sentinelle:custom` depuis Firefox ;
- publication automatique dans Git ou une CI ;
- synchronisation multi-utilisateur en temps réel.

## 16. Découpage de réalisation proposé

### Lot PF-1 — Contrat et association P0

- schéma `sentinelle-browser-capture-v1` ;
- endpoints de capacités, association et contextes ;
- squelette Manifest V3 et panneau Contexte ;
- tests de sécurité de l’association locale.

### Lot PF-2 — Capture DOM P0

- sélection visuelle ;
- inventaire `PageElement` ;
- localisateurs et scores ;
- capture multi-écrans ;
- recette sur les écrans Client et Articles.

### Lot PF-3 — Étapes, données et assertions P0

- traduction des interactions ;
- gestion des données et secrets ;
- assertions ;
- revue locale complète ;
- recette sur Récapitulatif et Suivi.

### Lot PF-4 — Prévisualisation et import P0

- API de prévisualisation ;
- fusion non destructive ;
- import non confirmé ;
- contrôle de préparation ;
- tests de bout en bout jusqu’à l’éditeur Sentinelle.

### Lot PF-5 — Diagnostics P1

- réseau/HAR, console, preuves visuelles ;
- variantes de données ;
- composants complexes ;
- comparaison de captures.

## 17. Décisions restant à prendre

1. Le panneau DevTools est-il obligatoire, ou une barre latérale suffit-elle au
   MVP ?
2. L’association locale utilise-t-elle un code court ou un fichier de
   configuration explicitement importé ?
3. Quel format applicatif portera les valeurs `data` en plus du workflow actuel ?
4. La fusion doit-elle remplacer tout le brouillon ou fonctionner page par page ?
5. Quels attributs de test personnalisés doivent être configurables ?
6. Combien de temps une session et ses preuves sont-elles conservées ?
7. Le HAR P1 est-il conservé par Sentinelle ou uniquement téléchargeable ?
8. Quelle version minimale de Firefox doit être supportée ?

## 18. Références

### Sentinelle Fonctionnelle

- [`domain/workflow.py`](../src/sentinelle_fonctionnelle/domain/workflow.py)
- [`web/cases_routes.py`](../src/sentinelle_fonctionnelle/web/cases_routes.py)
- [`web/templates/case_guided.html`](../src/sentinelle_fonctionnelle/web/templates/case_guided.html)
- [`application/code_customization.py`](../src/sentinelle_fonctionnelle/application/code_customization.py)
- [`orders-demo.md`](orders-demo.md)

### Firefox WebExtensions

- [Étendre les outils de développement](https://developer.mozilla.org/docs/Mozilla/Add-ons/WebExtensions/Extending_the_developer_tools)
- [Panneaux DevTools](https://developer.mozilla.org/docs/Mozilla/Add-ons/WebExtensions/user_interface/devtools_panels)
- [Content scripts](https://developer.mozilla.org/docs/Mozilla/Add-ons/WebExtensions/Content_scripts)
- [Permission `activeTab`](https://developer.mozilla.org/docs/Mozilla/Add-ons/WebExtensions/activeTab_permission)
- [Permissions d’hôtes facultatives](https://developer.mozilla.org/docs/Mozilla/Add-ons/WebExtensions/manifest.json/optional_host_permissions)
- [API réseau DevTools](https://developer.mozilla.org/docs/Mozilla/Add-ons/WebExtensions/API/devtools/network)
- [Migration Manifest V3](https://extensionworkshop.com/documentation/develop/manifest-v3-migration-guide/)
