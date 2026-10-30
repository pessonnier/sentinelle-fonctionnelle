# Preuve — lot 3 : cycle de vie du candidat

Date : **8 septembre 2026**

## Objectif

Fermer la verticale **générer → conserver → comparer → exécuter → décider** sans
approbation implicite ni perte des versions antérieures.

## Contrats obtenus

- la migration SQLite v8 ajoute des tables dédiées aux candidats et à leurs
  exécutions ; elles ne dépendent pas de la reconstruction technique de
  l’arborescence ;
- chaque candidat conserve son origine (`deterministic` ou `llm`), la version et
  l’empreinte de la définition structurée, le prompt éventuel, ses fichiers,
  leurs empreintes, son manifeste et l’empreinte canonique du bundle ;
- une nouvelle génération conserve l’historique, compare les chemins et
  empreintes, et invalide toute validation individuelle devenue obsolète ;
- une modification de la définition invalide les brouillons et validations liés
  à l’ancienne version, mais laisse la version approuvée immuable et traçable ;
- le runner rematérialise exactement le fichier persistant sous
  `tests/generated`, vérifie son manifeste avant pytest, puis conserve JUnit,
  journaux, traces/captures Playwright et `execution.json` ;
- une réussite place le candidat en **Validé individuellement**. L’état
  **Approuvé** exige ensuite une action humaine séparée ; un rejet exige un
  motif.

Le manifeste déclare également la structure de bundle simple
`tests/cases`, `tests/pages`, `tests/fixtures`, `test-data`, `generation` et
`config`. Les abstractions vides ne sont pas générées : un cas autonome reste un
seul fichier lisible.

## Vérification automatisée

Le test `tests/acceptance/test_lot3_candidate_lifecycle.py` couvre :

- refus d’approuver avant une réussite ;
- exécution de l’empreinte exacte et persistance des preuves après redémarrage ;
- décision humaine distincte ;
- comparaison de deux générations ;
- invalidation après régénération ou changement de spécification ;
- immutabilité d’une version approuvée ;
- génération et restitution du cycle depuis la page du cas.

`tests/acceptance/test_code_generation_prompt.py` contrôle en plus que la réponse
LLM validée est persistée avec le profil, le modèle, l’empreinte du prompt et le
manifeste exacts.

Résultats finaux : **104 tests et 40 sous-tests réussis**, lint critique, formatage
progressif, typage et liens documentaires réussis.

## Vérification navigateur réelle

Le cas **Refuser une connexion invalide** du projet RH a été ouvert depuis
l’interface puis traité uniquement par les actions de l’écran du cas :

1. génération du candidat #1 et affichage de son empreinte de bundle
   `75b3f4fdb9e1e0c7400b695eba9f121589daf4e229a847072e3cc6a841eb8c20` ;
2. conservation d’un échec de validation avec ses journaux ;
3. correction de l’origine transmise au runner, puis réussite Chromium en
   **1,766 s** sur l’empreinte source `941b87618920…` ;
4. maintien en **Validé individuellement** jusqu’au clic explicite
   **Approuver l’empreinte exécutée** ;
5. nouvelle génération donnant un candidat #2 **À valider**, identifié comme
   inchangé, tandis que le candidat #1 reste **Approuvé** avec ses preuves ;
6. contrôle à 390 px : cartes de 324,6 px, document de 375 px, aucun débordement
   horizontal ; aucune erreur ni alerte dans la console.

La réussite est enregistrée sous
`outputs/candidate-validations/39f61c989b8e4d2fae85dd6859f715ba/188b0c7653cb47dbaaf04fbfe3745d0d/`.

## Frontière restante

Le lot 3 couvre le bundle simple réellement généré et son cycle de validation.
L’éditeur de zones personnalisées avec fusion/conflits (`GEN-010` avancé) et le
runner OCI non privilégié restent des incréments séparés ; ils ne sont pas
présentés comme vérifiés ici.
