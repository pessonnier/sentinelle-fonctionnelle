# Preuve de l’itération 012.3

Date : 30 juillet 2026

## Périmètre vérifié

- plan d’exploration Playwright déclaratif et borné ;
- résolution d’une ligne XLSX sans persistance de ses valeurs ;
- catalogues rendus connexion, agent et manager ;
- comparaison HTML serveur / DOM rendu ;
- application du catalogue avec références stables ;
- génération et exécution de deux cas depuis le workflow dérivé.

## Résultats observés

| Preuve | Résultat |
|---|---|
| Tests ciblés du contrat | 4 réussis |
| Catalogue connexion | 7 éléments, 1 ajouté par JavaScript |
| Catalogue saisie agent | 22 éléments, 4 ajoutés par JavaScript |
| Catalogue saisie manager | 25 éléments, 5 ajoutés par JavaScript |
| Différence manager / agent | budget, commentaire et note dynamique manager |
| Application au workflow | 16 références reconnues, 9 nouvelles |
| Empreinte du code régénéré | `f5700dbbaf68fc441a7dde9ce1f001998d7903f82805efc71f9ac8aad4e89d4d` |
| Exécution Chromium | 2 collectés, 2 réussis, 0 échec, 4,738 s |

Le rapport structuré se trouve dans
`outputs/hr-demo/execution-rendered-catalog/execution.json`. Les catalogues sont
dans `outputs/hr-demo/catalog-*.json`.

## Garde-fous exercés

Les tests refusent une origine distante, l’action `javascript` et un plan de plus
de vingt actions. Ils vérifient également qu’un mot de passe et un courriel
résolus ne figurent pas dans l’artefact, et qu’une référence de titre existante
reste stable lors de l’application du catalogue.

## Frontière

La preuve porte sur une cible locale synthétique. Elle ne qualifie pas
l’exploration d’une recette distante, la résolution d’un vrai secret, le worker
isolé ou l’intégration interactive dans l’éditeur.
