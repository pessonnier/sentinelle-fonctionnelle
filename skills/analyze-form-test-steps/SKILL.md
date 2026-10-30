---
name: analyze-form-test-steps
description: Validate and normalize a functional test entered as structured action and control forms. Use when a small LLM must review form-based steps, identify missing facts, and prepare safe patch operations for the canonical SentinelleFonctionnelle workflow used by code generation.
---

# Analyser des étapes saisies par formulaire

1. Traiter chaque carte comme une étape ordonnée comportant contexte, action et contrôle.
2. Conserver les références `page:*`, `{{data.*}}`, `{{fixture.*}}` et `{{secret.*}}` sans les réécrire.
3. Vérifier la compatibilité action/cible/valeur et assertion/cible/résultat.
4. Poser une question pour tout fait métier, cible ou donnée absent. Ne rien inventer.
5. Préférer les rôles, libellés et références du catalogue HTML fourni.
6. Produire uniquement le contrat JSON demandé par l’appelant.

Pour SentinelleFonctionnelle, retourner `schema_version`, `questions` et
`operations`. Utiliser seulement `add` ou `replace` sur les chemins autorisés.
Une nouvelle étape contient exactement : `id`, `name`, `page_url`,
`precondition`, `action`, `target`, `value`, `assertion`, `assertion_target`,
`expected`, `evidence`.

Ne jamais confirmer le workflow, exposer une valeur secrète, inventer un
résultat réussi ou produire directement du code. Le générateur consommera le
workflow après décision humaine.
