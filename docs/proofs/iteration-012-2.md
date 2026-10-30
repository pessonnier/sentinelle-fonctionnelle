# Preuve — itération 012.2

Spécifications : `EF-007.5`, `EF-007.6`, `EF-012`, contribution locale à
`EF-015`

Acceptation : approfondissement de `ACC-041` et `ACC-042`, sans revendiquer le
runner OCI de `ACC-017` à `ACC-025`

Fichiers modifiés :

- matrice `data_sources` / `data_cases` dans
  `config/examples/hr-demo-workflow.json` ;
- génération et manifeste dans `application/code_generation.py` ;
- validation locale dans `application/execution_runner.py` ;
- commandes `generate-playwright` et `run-playwright` ;
- troisième ligne du classeur collaborateurs ;
- test paramétré et manifeste sous `tests/generated` ;
- guide `hr-demo.md` et introspection
  `design/iteration-012-2-introspection.md`.

Test RED :

- absence de `data_case_count` et du manifeste ;
- association de lignes incomplète non refusée ;
- absence du port applicatif de runner.

Test GREEN :

- tests ciblés de génération, intégrité et runner réussis ;
- matrice incomplète refusée ;
- cible distante refusée ;
- fichier extérieur à `tests/generated` refusé ;
- code modifié après génération refusé.

Suite complète : `Ran 61 tests in 6.187s`, puis `OK`.

Point d'entrée réel :

- génération CLI : deux cas, empreinte du workflow
  `1a94f15753018418dc5625b712a8032367700d4f31aca07ba6588ce3df6f5adc` ;
- exécution CLI sur `127.0.0.1:8772` ;
- Chromium : `2 passed in 3.86s` ;
- JUnit : deux tests, zéro échec ;
- `execution.json` : statut `passed`, code de sortie `0`.

Limites externes :

- validation locale sans isolation OCI ;
- boucle locale uniquement ;
- pas encore de sélection de suite ou de tags ;
- pas de capture sur réussite avec la politique `on_failure`.

Revue sécurité :

- aucune commande shell libre ;
- test limité à `tests/generated` ;
- manifeste obligatoire et empreinte du code vérifiée avant exécution ;
- chemins XLSX relatifs ;
- empreinte de chaque classeur vérifiée lors de la collecte ;
- aucune valeur XLSX recopiée dans le manifeste.
