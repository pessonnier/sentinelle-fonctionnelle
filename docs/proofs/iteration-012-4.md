# Preuve de l’itération 012.4 — saisie multimodale

Date : 31 juillet 2026.

## Périmètre vérifié

- trois modes de saisie alimentent le même `GenerationWorkflowInput` ;
- les références de données et les textes d’étape sont des listes extensibles ;
- un contrôle peut être inséré à la suite d’une action ;
- un récit non structuré reste enregistrable en brouillon mais non confirmable ;
- le skill associé au mode est transmis à la requête du petit LLM ;
- le prompt exact, la source analysée et les règles des trois skills sont
  consultables depuis le mode actif ;
- un cas confirmé propose le code Python Playwright en téléchargement, sans
  l’afficher dans le HTML ;
- le filtre du plan est fermé par défaut et ouvert lorsqu’une recherche est
  active.

## Vérifications exécutées

- `66 passed, 28 subtests passed` sur `tests/acceptance` et
  `tests/documentation` ;
- `10 passed` sur l’éditeur guidé, le dialogue et le plan ;
- les trois skills réussissent `quick_validate.py` ;
- `node --check` réussit sur `case-editor.js` ;
- revue réelle dans le navigateur local : bascule des trois modes, ajout d’un
  second récit, ajout d’une seconde donnée, insertion d’un contrôle et
  synchronisation immédiate du JSON ;
- revue visuelle du sélecteur de modes après correction de la taille des radios ;
- contrôle du filtre : `open=false` sans recherche, `open=true` et badge
  `actif` avec `?q=Parcours`.

Le 31 juillet 2026, Sentinelle et la cible RH ont été relancées sur
`127.0.0.1:8000`. Un cas réel en version 2 a catalogué six champs de la connexion
RH, produit un candidat Python téléchargeable (`HTTP 200`, pièce jointe,
SHA-256 `96c95f8b09234ba7189fc42628fb720af3841b9b9bf08a8b9a027fee8a91525e`) et
ce candidat a réussi dans Chromium : `1 passed in 0.88s`.

## Frontières conservées

Le téléchargement génère le candidat à la demande ; il ne constitue pas encore
un bundle persisté, approuvé et relié à un manifeste dans l’interface. Le petit
LLM n’a pas été sollicité en direct pendant cette itération : son contexte et
son contrat ont été vérifiés avec le double déterministe des tests. Les quatre
tests Playwright générés collectés par un `pytest` sans sélection exigent le
serveur RH sur `127.0.0.1:8000` ; ils n’ont pas été relancés dans cette revue.
