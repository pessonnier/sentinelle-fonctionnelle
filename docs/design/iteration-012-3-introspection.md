# Introspection 012.3 — du HTML source au DOM rendu

## Décision

La faiblesse la plus structurante du banc d’essai était connue : le parseur HTML
statique ne pouvait pas voir le code portail, les champs différés, le composant
Web ni les différences liées à une session réelle. Les décrire à la main dans le
workflow permettait d’exécuter le test, mais pas de démontrer que l’éditeur
pourrait assister l’utilisateur sur une application moderne.

La verticale 012.3 ajoute donc une exploration Playwright séparée du serveur web.
Elle n’est pas un robot généraliste : elle exécute un petit plan déclaratif,
atteint une page attendue, sérialise le DOM et le transmet au parseur déjà
utilisé par l’éditeur.

## Pourquoi ne pas donner la main au LLM

Un LLM aurait pu choisir à chaque écran où cliquer, mais cela aurait mélangé deux
problèmes : découvrir les capacités d’une page et décider dynamiquement d’un
parcours. Le résultat aurait été moins reproductible, plus difficile à auditer
et exposé aux instructions présentes dans la page.

Le plan fermé apporte au contraire :

- un historique diffable et versionnable ;
- une limite vérifiable de 20 actions et 120 secondes ;
- aucune primitive `evaluate`, aucun script, aucune commande shell ;
- des localisateurs inspectables avant exécution ;
- une frontière réseau locale contrôlée après chaque action ;
- un échec explicite si la page finale n’est pas celle annoncée.

Le LLM demeure utile en amont pour proposer un plan ou expliquer les champs,
mais sa proposition doit être validée et transformée dans ce contrat fermé avant
toute navigation.

## Données et confidentialité

Les valeurs d’authentification sont chargées depuis une ligne XLSX identifiée par
`source + colonne clé + clé de ligne`. Le plan contient seulement des jetons
qualifiés. Les actions résolues vivent en mémoire le temps de l’exploration.

L’artefact conserve :

- les identifiants de lignes ;
- les empreintes SHA-256 des classeurs ;
- le navigateur, l’URL finale et le nombre d’actions ;
- le catalogue et l’empreinte du DOM rendu.

Il ne conserve ni valeur résolue, ni HTML source, ni capture. Ce choix ne rend
pas le DOM intrinsèquement sans risque : une page peut réafficher une donnée
saisie. Avant d’étendre ce mécanisme à des environnements réels, il faudra une
politique de masquage des valeurs et attributs sensibles.

## Comparer le serveur au navigateur

Cataloguer seulement `page.content()` aurait trouvé les champs, mais n’aurait
pas expliqué leur origine. Après le parcours, le contexte Playwright relit donc
la page finale avec les mêmes cookies sans exécuter son JavaScript. Les
références du HTML serveur sont comparées à celles du DOM rendu.

Les résultats du banc RH sont nets :

| État | HTML serveur | DOM rendu | Ajouts JavaScript |
|---|---:|---:|---:|
| Connexion | 6 | 7 | 1 |
| Saisie agent | 18 | 22 | 4 |
| Saisie manager | 20 | 25 | 5 |

Le delta manager/agent contient exactement les deux champs serveur
`manager-budget`, `manager-comment` et le champ JavaScript
`manager-dynamic-note`. Cette distinction aide l’utilisateur à comprendre
pourquoi une analyse anonyme ou statique ne lui propose pas les mêmes actions.

## Stabilité des références

Un catalogue automatique nomme naturellement le titre
`page:saisie#declarer-un-nouveau-talent`, alors que le workflow existant
utilisait `page:saisie#heading`. Remplacer la page telle quelle aurait cassé le
cas tout en conservant un localisateur parfaitement valide.

L’application du catalogue rapproche donc les éléments par triplet :

1. stratégie de localisation ;
2. valeur du localisateur ;
3. rôle accessible.

Quand le triplet est inchangé, l’ancienne référence est conservée. Les éléments
sans équivalent reçoivent leur référence découverte. Enfin, toutes les cibles
utilisées par les étapes sont contrôlées ; une disparition bloque l’opération.

Cette règle a reconnu 16 éléments et ajouté 9 éléments informatifs. Le code
généré depuis le workflow dérivé a exactement la même empreinte que le code de
référence, puis ses deux cas ont réussi dans Chromium.

## Ce qui a été volontairement reporté

L’intégration dans l’interface de l’éditeur est la prochaine étape. La première
verticale reste une CLI car le processus web ne doit pas devenir implicitement
un navigateur capable d’utiliser des secrets. Une future interface devra
déléguer l’exploration à un worker identifié, afficher le plan avant lancement,
permettre l’arrêt et montrer la provenance `serveur` ou `rendu` dans la palette.

Sont aussi reportés :

- les origines de recette distantes et leur liste d’autorisation ;
- les secrets résolus par un coffre ;
- les redirections inter-origines explicitement approuvées ;
- les iframes, shadow DOM fermé et applications multi-onglets ;
- les captures masquées et traces ;
- la détection de doublons sémantiques au-delà du localisateur exact ;
- la promotion d’un catalogue après revue humaine.

## Conclusion

Cette verticale ne cherche pas à rendre Playwright autonome. Elle rend
l’exploration explicable, reproductible et suffisamment sûre pour le banc local.
Surtout, elle ferme la boucle utile : un champ absent du HTML initial est
observé après authentification, devient une référence stable, alimente le même
workflow, puis produit un test qui réussit réellement.
