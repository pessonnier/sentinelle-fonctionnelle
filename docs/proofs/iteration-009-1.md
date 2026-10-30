# Preuve — intentions et diagnostic guidé

Date : 28 juillet 2026

## Périmètre

- `EF-004` : préparation déterministe du dialogue depuis les informations
  manquantes ;
- `EF-017` : catalogue YAML versionné des intentions fonctionnelles ;
- `ACC-032` : chargement du catalogue administrable ;
- préparation de `ACC-007` sans appel réseau au LLM.

Cette verticale est volontairement nommée `009.1` : elle fournit le diagnostic
qui guidera le futur échange LLM, mais ne prétend pas implémenter cet échange.

## Chemin observable

```text
éditeur du cas
→ choix d’une intention fonctionnelle versionnée
→ analyse du brouillon structuré
→ questions portant uniquement sur les informations manquantes
→ explication de l’utilité de chaque réponse
→ analyse HTML de la page
→ actions, validations et exemples compatibles par élément
→ insertion d’une référence dans une carte d’étape
→ conservation de functional_intent dans generation_workflow
```

## Test RED

```powershell
.\.venv\Scripts\python.exe -m unittest `
  tests.acceptance.test_design_guidance -v
```

Échec observé avant implémentation :

```text
ImportError: cannot import name 'FunctionalIntentCatalog'
```

## Vérification ciblée

```powershell
.\.venv\Scripts\python.exe -m unittest `
  tests.acceptance.test_design_guidance `
  tests.acceptance.test_guided_workflow_editor `
  tests.acceptance.test_server_settings -v
```

Résultat :

```text
Ran 9 tests
OK
```

## Suite complète

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Résultat :

```text
Ran 43 tests
OK
```

La compilation Python et `node --check` sur `case-editor.js` réussissent
également.

## Vérification ergonomique dans le navigateur

Le parcours local réel a couvert :

- création d’un projet, d’un plan, d’un dossier, d’une suite et d’un cas ;
- sélection de `authentication-login-success@1` ;
- affichage d’une complétude à 33 % et de quatre questions ciblées ;
- présence de l’utilité et du bouton de retour au champ pour chaque question ;
- analyse de la page de l’application : 17 éléments utilisables détectés ;
- distinction entre éléments manipulables et éléments uniquement observables ;
- affichage des actions, validations et exemples de valeurs compatibles ;
- insertion d’une référence HTML dans la cible d’une étape ;
- lecture de la documentation et du tutoriel depuis leurs routes réelles ;
- contrôle à 1 280 px sans débordement horizontal.

## Sécurité et limites

- le diagnostic est déterministe, local et sans appel LLM ;
- le catalogue ne contient ni prompt libre ni secret ;
- le brouillon transmis au diagnostic est borné à 512 Kio ;
- le HTML brut n’est pas interprété comme une instruction ;
- le diagnostic ne modifie, ne confirme et n’enregistre aucune proposition ;
- la référence d’intention est validée côté serveur avant enregistrement ;
- l’échange LLM, le diff de propositions et la description synthétique restent
  à implémenter pour terminer la tranche `009`.
