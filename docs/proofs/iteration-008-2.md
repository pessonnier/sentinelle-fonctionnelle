# Preuve — configuration LLM et génération de code

Date : 28 juillet 2026

## Périmètre

- `EF-007.7` : profils versionnés d’accès LLM et de génération ;
- `EF-007.6` : références des profils dans le workflow du cas ;
- `GEN-002.2` : résolution future de la configuration effective ;
- `ACC-078` à `ACC-080`.

## Test RED

```powershell
.\.venv\Scripts\python.exe -m unittest `
  tests.acceptance.test_generation_configuration -v
```

Échec initial observé :

```text
TypeError: ServerSettings.__init__() got an unexpected keyword argument
'generation_profiles'
```

## Chemin vérifié

```text
configuration LLM
→ référence de variable d’environnement
→ configuration de génération
→ liaison LLM identifiant@version
→ sélection dans le cas
→ JSON generation_workflow
→ persistance SQLite
→ restauration après redémarrage
```

## Sécurité vérifiée

- aucune valeur de clé API n’est acceptée comme propriété du modèle ou écrite
  dans le YAML ;
- les noms de variables d’environnement sont validés ;
- HTTP distant, identifiants dans l’URL, paramètres et fragments sont refusés ;
- HTTP reste possible sur la boucle locale pour Ollama ;
- les chemins absolus, lettres de lecteur et remontées `..` sont refusés ;
- les motifs de fichiers exigent `{case_slug}` ou `{page_slug}` ;
- les validations de code utilisent un vocabulaire fermé sans commande shell ;
- le profil de génération doit référencer une version LLM existante.

## Vérification automatisée

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node --check .\src\sentinelle_fonctionnelle\web\static\case-editor.js
.\.venv\Scripts\python.exe -m compileall -q .\src .\tests
```

Résultat :

```text
Ran 41 tests
OK
```

Les deux vérifications syntaxiques retournent le code `0`.

## Vérification dans le navigateur

- création d’un profil OpenAI sans valeur de secret ;
- affichage du statut `Variable absente` lorsque `OPENAI_API_KEY` n’est pas
  injectée ;
- activation du formulaire de génération après création de l’accès ;
- création du profil Python / pytest-playwright et affichage de sa référence ;
- inspection sur ordinateur et viewport mobile de 390 px ;
- correction de la navigation mobile en deux rangées sans débordement ;
- absence de message d’erreur dans la console.

## Limites

Cette tranche configure et versionne les accès et les règles de génération.
Elle ne réalise pas encore le contrôle de connexion, l’appel réseau au LLM,
la construction du prompt final, l’écriture des fichiers ni leur exécution.
