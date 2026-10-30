# Preuve — 012.6 Prompt final et traçabilité des skills

Date : 2 août 2026

## Résultat livré

Chaque profil de génération porte une liste ordonnée de skills versionnés. Le
cas confirmé assemble un artefact `code-generation-v1` prêt à adresser au LLM :
messages `system` et `user`, modèle, profils, skills, workflow assaini, contrat
de sortie et empreinte SHA-256.

L’écran de configuration montre les skills et leurs sources. L’écran du cas
donne accès à une page de consultation du prompt, au téléchargement du JSON exact
et au téléchargement séparé du code candidat. Le skill
`generate-python-playwright-code@1` a été créé avec le guide `skill-creator` et
validé avec son validateur officiel.

## Vérifications automatisées

- phase RED : absence initiale de la route de prompt et du champ `Skills` ;
- tests ciblés après implémentation : `5 passed` ;
- suite complète : `85 passed`, `32 subtests passed` ;
- validation du skill : `Skill is valid!` ;
- empreinte de l’artefact identique à l’en-tête `X-Prompt-SHA256` ;
- absence de `Cactus!2026` et présence de
  `<secret-value-redacted>` dans le prompt final ;
- téléchargement du JSON et du candidat avec un nom de fichier explicite.

## Vérifications sur l’application réelle

Le cas **Créer et consulter Zoé Nébuleuse** du projet RH a produit un prompt
HTTP `200` avec :

- accès LLM `ollama-qwen36-128k-11436@1` ;
- modèle `qwen3.6-35b-a3b-q4_K_M_128k:latest` ;
- profil `python-playwright-qwen36-11436@1` ;
- 2 skills et 23 étapes ;
- empreinte `5816ec86047003a7bb690a909ca7a4e5d3ed1c60493f44a446eaf6d1028f2303` ;
- candidat Playwright téléchargé : 7 083 octets.

Dans Chromium intégré, la configuration affiche les deux skills avec leurs
sources. La page de prompt montre les deux messages, le JSON repliable et le
bouton de téléchargement. La censure est visible, le mot de passe est absent et
la page ne présente aucun débordement horizontal.

## Frontière

Le prompt est produit, vérifiable et téléchargeable, mais n’est pas encore envoyé
au fournisseur LLM de génération. Le code accessible reste le candidat construit
par le générateur déterministe existant.
