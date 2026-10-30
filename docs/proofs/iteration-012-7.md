# Preuve — 012.7 Génération réelle par Ollama 11436

Date : 3 août 2026

## Résultat livré

Un cas confirmé peut désormais envoyer son prompt final audité au profil LLM
versionné qu’il référence. La page de consultation du prompt porte l’action
**Générer avec le LLM local**. Le candidat déterministe existant reste une action
séparée.

L’adaptateur de génération :

- transmet directement les messages `system` et `user` déjà présentés à
  l’utilisateur ;
- appelle `/v1/chat/completions` avec une sortie JSON et une température nulle ;
- désactive le raisonnement Ollama et borne la sortie à 32 768 jetons ;
- conserve le délai et les reprises du profil versionné.

Avant téléchargement, la réponse est refusée si le schéma, le nombre de fichiers,
la racine relative, l’extension, les doublons, la taille ou la syntaxe Python sont
invalides. Le fichier de test attendu doit être présent. Un candidat multifichier
est livré en ZIP avec un manifeste ; aucun résultat du LLM n’est écrit
automatiquement dans le dépôt.

## Vérifications automatisées

- tests ciblés de l’adaptateur, du prompt, de l’éditeur et des profils :
  `17 passed`, `2 subtests passed` ;
- suite produit et documentation : `80 passed`, `32 subtests passed` ;
- six scripts Playwright générés : `6 passed` avec la cible RH locale active ;
- refus vérifié d’un chemin LLM `../outside.py` ;
- compilation Python des modules modifiés réussie.

## Vérification sur Ollama réel

Le 3 août 2026, `http://127.0.0.1:11436` répondait avec Ollama `0.32.3` et
exposait le modèle `qwen3.6-35b-a3b-q4_K_M_128k:latest`.

Le cas RH nominal de 23 étapes a été envoyé par la nouvelle route :

- statut : `200` ;
- durée totale du contrôle final : 57,8 secondes ;
- profil : `ollama-qwen36-128k-11436@1` ;
- modèle : `qwen3.6-35b-a3b-q4_K_M_128k:latest` ;
- fichiers retournés : 1 ;
- hypothèses et alertes retournées : 3 et 2 ;
- livraison : archive ZIP de 2 613 octets avec manifeste, afin de conserver ces
  réserves avec le code ;
- empreinte du prompt :
  `6ca70119c0761deb5f040df8bd2b29ea6fa1624e235e73d24342ba15d34a3281` ;
- empreinte du candidat :
  `38d42379ee61d6ed09af28e37245359b1d66556cd1b9b85bcca4097278af2a8e`.

Le code n’a pas été persisté pendant cette preuve ; seule sa réponse HTTP validée
a été mesurée.

## Frontière

Cette verticale produit un candidat téléchargeable. Elle ne le persiste pas encore
dans le cycle de vie, ne calcule pas de diff avec un candidat précédent, ne le lance
pas automatiquement et ne l’approuve jamais. Le pipeline déterministe complet et
le bundle contrôlé restent à réaliser.
