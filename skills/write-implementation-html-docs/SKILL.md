---
name: write-implementation-html-docs
description: Create or update standalone HTML documentation that truthfully reflects implemented specifications, with traceability, usage scenarios, configuration, launch instructions, expected results, limitations, and validation. Use for HTML tutorials, local or online deployment guides, operator guides, feature demonstrations, and implementation-status documentation derived from a specification repository.
---

# Rédiger une documentation HTML d’implémentation

## Établir la vérité documentaire

1. Lire les spécifications normatives, le tableau d’avancement et les preuves.
2. Inspecter les véritables points d’entrée, options CLI, fichiers de
   configuration et dépendances.
3. Exécuter les commandes documentées lorsque l’environnement le permet.
4. Classer chaque capacité comme `implemented` ou `planned`.
5. Ne jamais transformer une intention de spécification en fonction disponible.

Considérer le tableau d’avancement et les preuves d’exécution comme la source de
vérité du statut. Utiliser les spécifications pour expliquer le comportement et
ses identifiants stables.

## Construire le contenu

Inclure au minimum les sections portant les identifiants HTML suivants :

- `current-status` : état exact du produit et fonctions indisponibles ;
- `prerequisites` : versions, droits et dépendances ;
- `configuration` : paramètres, valeurs par défaut, secrets et différences de
  mode ;
- `launch` : commandes copiables, répertoire d’exécution et résultat attendu ;
- `scenarios` : scénarios numérotés utilisant uniquement des fonctions
  vérifiées ;
- `troubleshooting` : erreurs probables, diagnostic et correction ;
- `limitations` : fonctions planifiées ou dépendances externes ;
- `traceability` : correspondance entre scénarios, spécifications, acceptations
  et preuves.

Décrire chaque scénario avec :

1. un objectif utilisateur ;
2. les prérequis et données ;
3. la commande ou les actions exactes ;
4. le résultat observable attendu ;
5. les identifiants de spécification et d’acceptation.

## Marquer la traçabilité

Ajouter sur les éléments concernés :

```html
<article
  class="scenario"
  data-spec="EF-002 ACC-003"
  data-status="implemented">
```

Utiliser `data-status="implemented"` uniquement si tous les identifiants sont
présents dans une tranche `Vérifiée`. Utiliser `planned` pour expliquer une
limite future, sans la mélanger aux instructions de lancement.

## Produire un HTML autonome et accessible

- Utiliser HTML5 sémantique, `lang`, un titre unique, un seul `h1`, `nav` et
  `main`.
- Fournir un lien d’évitement vers `#main-content`.
- Rendre la page lisible à 390 px, 1440 px et à l’impression.
- Utiliser des couleurs contrastées et ne jamais coder un état par la couleur
  seule.
- Conserver les commandes en texte sélectionnable dans `pre > code`.
- Éviter toute dépendance réseau, police distante, CDN ou image non nécessaire.
- Ajouter du JavaScript uniquement en amélioration progressive.
- Ne jamais inclure de secret, jeton, mot de passe réel ou chemin personnel.

## Valider

Exécuter :

```powershell
python scripts/validate_html_doc.py `
  <documentation.html> `
  --spec <SPECIFICATIONS.md> `
  --status <IMPLEMENTATION_STATUS.md>
```

Le script vérifie la structure, les ancres, les sections obligatoires et les
marqueurs de traçabilité. Corriger toutes les erreurs.

Exécuter ensuite les tests documentaires du dépôt, les commandes présentées dans
le guide et une inspection visuelle locale. Vérifier au minimum une largeur
desktop et une largeur mobile.

## Mettre à jour

À chaque évolution :

1. recalculer les capacités vérifiées ;
2. mettre à jour les scénarios, la configuration et les limites ;
3. supprimer les instructions obsolètes plutôt que les conserver comme
   variantes silencieuses ;
4. relancer le validateur, les tests et l’inspection visuelle ;
5. enregistrer les preuves et la date de vérification dans le dépôt.

