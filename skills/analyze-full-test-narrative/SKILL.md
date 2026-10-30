---
name: analyze-full-test-narrative
description: Segment a complete natural-language functional-test scenario into canonical ordered steps, data references, and observable controls. Use when a small LLM analyzes one block describing the whole SentinelleFonctionnelle case and prepares bounded workflow patches for code generation.
---

# Analyser le récit complet d’un cas

1. Identifier le comportement métier unique, l’acteur, les préconditions et la fin observable.
2. Segmenter le récit en étapes minimales et ordonnées sans changer sa causalité.
3. Pour chaque étape, extraire page, action, cible, valeur, assertion, cible observée et résultat attendu.
4. Utiliser uniquement les références du catalogue HTML et les espaces de noms de données fournis.
5. Poser des questions sur les ambiguïtés bloquantes. Si le récit couvre plusieurs comportements, demander sa séparation.
6. Produire uniquement le contrat JSON demandé par l’appelant.

Pour SentinelleFonctionnelle, retourner `schema_version`, `questions` et
`operations`. Utiliser seulement `add` ou `replace` sur les chemins autorisés.
Une nouvelle étape contient exactement : `id`, `name`, `page_url`,
`precondition`, `action`, `target`, `value`, `assertion`, `assertion_target`,
`expected`, `evidence`.

Ne jamais compléter silencieusement une donnée, un secret ou un résultat. Ne
jamais confirmer le workflow ni générer le code avant la décision humaine.
