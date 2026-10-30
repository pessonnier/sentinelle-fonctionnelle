# Preuve — 012.5 Projet RH d’exemple dans Sentinelle

Date : 1er août 2026

## Résultat livré

La commande `seed-hr-demo-project` installe de façon idempotente dans SQLite le
projet **Exemple — Bureau des Talents Intersidéraux**, un plan, un dossier, deux
suites et deux cas confirmés. Le cas nominal parcourt connexion, saisie et
consultation en 23 étapes ; le cas négatif vérifie le refus d’un compte inconnu.

Les deux classeurs XLSX sont attachés aux cas. Les valeurs employées par les
workflows unitaires sont des données synthétiques matérialisées pour rendre les
téléchargements immédiatement exécutables malgré l’absence actuelle
d’assemblage multi-XLSX dans la route de téléchargement d’un cas.

Les workflows sont reliés à `ollama-qwen36-128k-11436@1` et au profil de
génération compatible `python-playwright-qwen36-11436@1`. L’instance locale
`127.0.0.1:11436` expose bien le modèle exact
`qwen3.6-35b-a3b-q4_K_M_128k:latest`.

## Vérifications

- import et lecture visuelle des feuilles des deux classeurs ;
- parcours manuel Chromium du manager jusqu’à la consultation de Zoé Nébuleuse ;
- parcours manuel Chromium du profil refusé ;
- contrôle de l’arborescence et des 23 étapes dans l’interface Sentinelle ;
- téléchargement HTTP des deux candidats depuis leur écran de cas : `200` et
  aucun jeton `{{data.*}}` non résolu ;
- exécution directe des deux fichiers téléchargés dans Chromium :
  `2 passed in 2.20s` ;
- test d’acceptation du seeder et de sa resynchronisation : `1 passed`.
- sonde applicative Ollama : état `ok`, modèle disponible en 177 ms ;
- inférence de contrôle : JSON structuré valide en 14,062 s ;
- relecture réelle du cas nominal par Qwen : réponse en 33,5 s, deux
  propositions conservées en attente et aucune modification appliquée ;
- non-régression seeder, connectivité et profils : `5 passed`.

Le premier essai du cas négatif a exposé une ambiguïté d’accessibilité : le
contenu d’un élément `role="alert"` n’est pas nécessairement son nom accessible.
Le catalogue utilise désormais le sélecteur CSS stable `[role="alert"]`, puis
vérifie son texte. Le test d’acceptation protège ce choix.

## Artefacts

- `src/sentinelle_fonctionnelle/application/hr_demo_seed.py` ;
- `tests/acceptance/test_hr_demo_project_seed.py` ;
- `outputs/hr-demo/generated-project/test_sentinelle_hr_nominal.py` ;
- `outputs/hr-demo/generated-project/test_sentinelle_hr_rejected.py` ;
- `docs/hr-demo.md`.
