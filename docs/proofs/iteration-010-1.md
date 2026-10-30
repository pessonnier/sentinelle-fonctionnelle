# Preuve — itération 010.1

Date : 1er août 2026

## Périmètre

- workflow de génération version 2 compatible avec les versions 1 existantes ;
- traduction de chaque précondition métier en condition vérifiable, fixture,
  dépendance technique, préparation ou nettoyage ;
- confirmation humaine explicite, invalidée lors d’une modification ;
- refus de confirmer un workflow v2 incomplet ;
- transport des traductions dans le code candidat et son manifeste ;
- contrôle serveur de la destination, des fixtures, de la présence des secrets
  et du runtime Playwright, sans exposer une valeur sensible ;
- affichage détaillé des contrôles dans l’éditeur.

## Vérifications automatisées

```text
pytest tests/acceptance/test_precondition_readiness.py
3 passed

pytest tests/acceptance/test_precondition_readiness.py \
       tests/acceptance/test_guided_workflow_editor.py \
       tests/acceptance/test_hr_demo_generation.py \
       tests/acceptance/test_generation_configuration.py \
       tests/acceptance/test_web_documentation_help.py
16 passed

pytest
80 passed, 30 subtests passed
```

La syntaxe de `case-editor.js` et des modules Python modifiés a également été
contrôlée.

## Vérification navigateur

Sur le cas RH conservé dans la base locale :

1. la précondition existante a produit une carte non confirmée ;
2. le JSON visible a exposé `schema_version: 2` et
   `precondition_dependencies` ;
3. **Vérifier la préparation** a affiché un blocage portant uniquement sur la
   traduction non confirmée ;
4. après confirmation locale de la carte, les six contrôles sont passés et
   l’écran a affiché **Préparation vérifiée** ;
5. le formulaire n’a pas été envoyé et les données persistées n’ont pas changé.

## Frontière conservée

`ACC-033` est couvert par cette verticale. `ACC-034` ne l’est que partiellement :
le contrôle web est déterministe et la génération v2 est bloquée, mais le futur
runner isolé devra refaire ces contrôles juste avant l’exécution. Les catalogues
administrables de profils d’environnement et de données, la résolution réelle
des fixtures et la transformation des préparations en fonctions exécutables
restent à réaliser dans la suite de la tranche 010.
