---
name: analyze-step-test-narratives
description: Turn one natural-language description per functional-test step into ordered canonical actions and assertions. Use when a small LLM analyzes step-by-step prose in SentinelleFonctionnelle and prepares controlled workflow patches for subsequent code generation.
---

# Analyser un texte par étape

1. Respecter l’ordre et la frontière de chaque texte ; ne pas fusionner deux étapes sans justification.
2. Extraire pour chaque texte : intention, page, prérequis local, action, cible, valeur, contrôle, cible observée et résultat attendu.
3. Résoudre les éléments uniquement avec le catalogue HTML et les espaces de noms de données fournis.
4. Si une phrase contient plusieurs actions indépendantes, proposer plusieurs étapes ordonnées.
5. Poser une question lorsqu’un verbe, une cible, une donnée ou un résultat observable manque. Ne rien inventer.
6. Produire uniquement le contrat JSON demandé par l’appelant.

Pour SentinelleFonctionnelle, retourner `schema_version`, `questions` et
`operations`. Utiliser seulement `add` ou `replace` sur les chemins autorisés.
Une nouvelle étape contient exactement : `id`, `name`, `page_url`,
`precondition`, `action`, `target`, `value`, `assertion`, `assertion_target`,
`expected`, `evidence`.

Ne jamais interpréter une phrase vague comme une réussite, recopier un mot de
passe ou confirmer le workflow. La décision humaine précède la génération.
