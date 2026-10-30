# Preuve — itération 012.1

Spécifications : `GEN-001` à `GEN-006`, contribution à `EF-010` et `EF-007.2`

Acceptation : première verticale exécutable de `ACC-041` et `ACC-042`

Fichiers modifiés :

- cible intégrée `src/sentinelle_fonctionnelle/web/hr_demo.py` ;
- pages et ressources `hr_demo_*`, `hr-demo.js` et `hr-demo.css` ;
- générateur `application/code_generation.py` et commande
  `generate-playwright` ;
- workflow `config/examples/hr-demo-workflow.json` ;
- classeurs dans `outputs/hr-demo/` et constructeur reproductible dans
  `tools/build_hr_demo_workbooks.mjs` ;
- scénario `tests/generated/test_hr_demo_workflow.py` ;
- guide `docs/hr-demo.md`.

Test RED : non conservé séparément ; la verticale a d’abord refusé les actions
sans localisateur et les chemins XLSX non sûrs.

Test GREEN :

- `tests/acceptance/test_hr_demo_target.py` : 2 réussis ;
- `tests/acceptance/test_hr_demo_generation.py` : 2 réussis ;
- scénario généré Chromium : `1 passed in 4.40s`.

Suite complète : `Ran 55 tests in 5.926s`, puis `OK`.

Point d'entrée réel :

- serveur démarré par la CLI sur `127.0.0.1:8770` ;
- test généré exécuté par `pytest-playwright` avec Chromium 149 ;
- connexion manager, saisie XLSX, redirection et contrôles finaux réussis.
- inspection visuelle ordinateur et mobile dans le navigateur intégré ;
- débordement horizontal mobile détecté, corrigé et recontrôlé avec une largeur
  de document de `382 px` dans un viewport de `390 px`.

Limites externes :

- le parseur HTML courant n’exécute pas JavaScript et ne fabrique pas de
  session ; les éléments dynamiques sont catalogués explicitement dans
  l’exemple ;
- cette verticale génère Python avec `pytest-playwright` uniquement ;
- une seule ligne par classeur est consommée.

Revue sécurité :

- données et comptes exclusivement synthétiques ;
- chemins tabulaires relatifs et contrôlés ;
- aucune formule Excel exécutée ;
- aucune valeur de donnée recopiée dans le code généré.
