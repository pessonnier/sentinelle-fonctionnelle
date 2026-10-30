# Preuve — dialogue contrôlé et description factuelle

Date : 29 juillet 2026

## Périmètre

- `EF-004` : échange contextualisé et propositions soumises à décision ;
- `EF-005` : description reconstruite depuis les faits acceptés ;
- `GEN-002.1` : sortie LLM structurée, bornée et non approbatrice ;
- `ACC-007`, `ACC-008`, `ACC-009`.

## Chemin observable

```text
éditeur du cas
→ intention fonctionnelle et accès LLM versionnés
→ diagnostic déterministe et capacités HTML minimisées
→ message explicite de l’utilisateur
→ réponse LLM validée contre un contrat fermé
→ questions et opérations séparées dans l’interface
→ sélection humaine des opérations acceptées
→ contrôle de l’empreinte du brouillon
→ application des seules opérations acceptées
→ description factuelle reconstruite
→ dialogue, décisions et brouillon accepté restaurés depuis SQLite
```

## Test RED

```powershell
.\.venv\Scripts\python.exe -m unittest `
  tests.acceptance.test_design_dialogue -v
```

Échec observé avant raccordement :

```text
AssertionError: 200 != 404
AssertionError: 400 != 404
```

Les routes d’échange et de décision n’existaient pas encore.

## Vérification ciblée

```powershell
.\.venv\Scripts\python.exe -m unittest `
  tests.acceptance.test_design_llm_adapter `
  tests.acceptance.test_design_dialogue -v
```

Résultat :

```text
Ran 4 tests
OK
```

Les scénarios vérifient notamment :

- l’absence de clé API et de mot de passe dans le contexte LLM ;
- la présence du secret uniquement dans l’en-tête HTTP ;
- la fermeture de la réponse réseau ;
- le refus d’une sortie visant `workflow.confirmed` sans persistance du message ;
- le refus d’une décision lorsque le brouillon a changé ;
- l’acceptation de trois opérations et le refus explicite de la quatrième ;
- l’absence du résultat attendu refusé dans la description ;
- la restauration du dialogue et du brouillon accepté après redémarrage.

## Suite complète et syntaxe

```powershell
node --check src/sentinelle_fonctionnelle/web/static/case-editor.js
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Résultat :

```text
Ran 47 tests in 5.469s
OK
```

`git diff --check` ne signale aucune erreur de whitespace.

## Vérification ergonomique dans le navigateur

Le point d’entrée réel a été lancé sur une base SQLite isolée. Le parcours a
couvert :

- création d’un projet, d’un plan, d’un dossier, d’une suite et d’un cas ;
- ordre visible `Assistant de conception` → `Dialogue avec le LLM` →
  `Pages et champs utilisables` ;
- présence du diagnostic, des capacités HTML, du message LLM, de la mention
  `Décision humaine` et de la description synthétique ;
- lisibilité du panneau à 1 280 px ;
- présence sur le tutoriel des étapes d’acceptation et du contrôle d’empreinte ;
- présence dans la documentation des données transmises et exclues.

Le fournisseur n’a pas été contacté pendant le contrôle navigateur ; les tests
injectent un adaptateur déterministe afin de vérifier l’interface et la
persistance sans dépendance réseau.

## Sécurité et limites

- le brouillon et la réponse sont bornés ; les clés inconnues sont refusées ;
- ni HTML brut, ni localisateur candidat, ni valeur de secret ne sont placés
  dans le contexte LLM ;
- les pages, profils et la confirmation du workflow ne sont pas modifiables ;
- une sortie invalide ne persiste même pas le message utilisateur ;
- une proposition est liée à l’empreinte exacte du brouillon ;
- la description est produite par le domaine, pas reprise du texte du LLM ;
- les fournisseurs Azure OpenAI et Anthropic restent explicitement sans
  adaptateur de dialogue dans cette verticale ;
- le contrôle de connexion et de capacités d’un fournisseur réel, la génération
  des fichiers et l’approbation du code restent hors périmètre.
