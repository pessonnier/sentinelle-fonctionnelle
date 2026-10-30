# Preuve — workflow guidé et analyse HTML

Date : 27 juillet 2026

## Périmètre

- `EF-007.4` : workflow pas-à-pas unique ;
- `EF-007.6` : structure case-level de génération ;
- `EF-010` : première analyse HTML bornée avant exploration Playwright ;
- `GEN-001`, `GEN-002.1` : entrée structurée et finalisation LLM spécifiée ;
- `ACC-074` à `ACC-077`.

## Chemin observable

```text
éditeur du cas
→ analyse d’une page de la cible
→ palette de champs
→ cartes action/validation
→ aperçu JSON
→ validation métier
→ persistance SQLite
→ restauration après redémarrage
```

## Test RED

```powershell
.\.venv\Scripts\python.exe -m unittest `
  tests.acceptance.test_guided_workflow_editor -v
```

Échec observé avant implémentation :

```text
ModuleNotFoundError:
No module named 'sentinelle_fonctionnelle.adapters.page_analysis'
```

## Vérification ciblée

```powershell
.\.venv\Scripts\python.exe -m unittest `
  tests.acceptance.test_guided_workflow_editor `
  tests.documentation.test_playwright_reference_snapshot -v
```

Résultat :

```text
Ran 4 tests
OK
```

## Vérification ergonomique dans le navigateur

- parcours complet projet → plan → dossier → suite → cas ;
- affichage contrôlé sur ordinateur et sur une largeur mobile de 390 px ;
- analyse de la page cible et insertion d’une référence depuis la palette ;
- ajout et réordonnancement de cartes avec mise à jour du JSON ;
- copie de la structure dans le presse-papiers ;
- aucun message d’erreur dans la console.

Cette vérification a conduit à exclure le contenu des infobulles de la palette
HTML et à corriger les opérations de déplacement haut/bas.

## Vérification syntaxique

```powershell
node --check `
  .\src\sentinelle_fonctionnelle\web\static\case-editor.js

.\.venv\Scripts\python.exe -m compileall -q .\src .\tests
```

Résultat : codes de sortie `0`.

## Suite complète

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Résultat :

```text
Ran 39 tests
OK
```

## Sécurité et limites

- l’analyse accepte uniquement HTTP(S) sur l’origine de la cible du projet ;
- une redirection vers une autre origine, une ressource non HTML ou une réponse
  supérieure à 2 Mio est refusée ;
- aucun cookie, profil d’acteur ou secret n’est envoyé pendant l’analyse ;
- seules les références de secrets sont persistées ;
- une destination modifiée dans le JSON soumis est revalidée côté serveur ;
- une structure confirmée contenant une hypothèse est refusée ;
- l’analyse courante lit le HTML statique ; les applications rendues par
  JavaScript ou protégées par session exigent le futur adaptateur Playwright ;
- l’interaction LLM et la génération de code restent spécifiées mais non
  implémentées dans cette tranche.
