# Preuve d’itération 008 — Profils d’approche de test YAML

Spécifications : `EF-002.2`, `GEN-001`

Acceptation : `ACC-073`

Fichiers modifiés :

- domaine et catalogue YAML des profils d’approche de test ;
- référence versionnée dans le plan de test et migration SQLite ;
- formulaires de sélection des plans et écran de configuration ;
- spécifications, documentation et tests d’acceptation.

Test RED : le parcours d’acceptation échouait avant l’ajout du catalogue, des
routes de configuration et de la référence versionnée.

Test GREEN : `test_yaml_catalog_preserves_versions` et
`test_configuration_form_creates_profile_selected_by_test_plan` réussissent.

Suite complète : `python -m unittest discover -v` — 35 tests réussis.

Point d’entrée réel : application FastAPI créée par
`sentinelle_fonctionnelle.web.app.create_web_app`.

Limites externes : aucune ; le catalogue est local et stocké en YAML.

Revue sécurité : chargement avec `yaml.safe_load`, validation stricte des
identifiants et des champs, aucune donnée secrète dans les profils.
