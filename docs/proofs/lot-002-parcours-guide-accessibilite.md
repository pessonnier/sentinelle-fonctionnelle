# Preuve — lot 2 : parcours guidé et accessibilité

Date : **7 septembre 2026**

## Objectif

Permettre à une personne qui découvre le produit de créer puis confirmer son
premier cas sans connaître l’arborescence interne, éditer du JSON ou ouvrir la
documentation.

## Parcours obtenu

- l’accueil affiche immédiatement **Créer mon premier projet** ;
- la cible `http://127.0.0.1:8000/demo/hr` et la politique
  `demo-only same-origin local-loopback` proposent un démarrage local sûr ;
- les trois écrans techniques sont regroupés sous **Administration** ;
- un repère **Projet → Plan → Cas → Validation** est présent sur chaque étape ;
- la création d’un plan ouvre directement sa page, également accessible par son
  nom depuis l’arborescence du projet ;
- **Créer mon premier cas** crée la suite racine **Parcours principal** puis ouvre
  l’éditeur guidé ; dossiers, suites et réorganisation restent disponibles pour
  les usages avancés ;
- le workflow JSON demeure un champ technique masqué et est construit par
  l’interface.

Le parcours navigateur a créé un projet, un plan et le premier cas, puis a
enregistré ce cas avec le statut **Défini**, la **Version 1** et la confirmation
active, sans ouvrir la documentation ni manipuler de JSON.

## Accessibilité et erreurs

L’aide de champ n’est plus un `<details>` interactif inclus dans un `<label>`.
Chaque champ reçoit un identifiant unique ; son libellé utilise `for` et la
description est reliée par `aria-describedby`. Les noms accessibles observés ne
reprennent pas le texte de l’aide.

Le formulaire de projet renvoie une page HTML `422` en cas d’erreur. Il conserve
les valeurs valides, ouvre le panneau, marque le champ avec `aria-invalid`, relie
le message en ligne et place le focus sur la première erreur. La touche Échap
referme un panneau de création et rend le focus à son bouton.

## Vérification navigateur

Contrôles réalisés avec l’application locale réelle :

- bureau 1280 × 720 : aucun débordement horizontal, menu Administration
  utilisable, quatre champs initiaux correctement libellés et décrits ;
- mobile 390 × 844 : aucun débordement horizontal sur l’accueil et le cas
  confirmé ; progression, onglets, état et formulaire restent lisibles ;
- aucune aide interactive imbriquée dans un libellé ;
- aucune erreur ni alerte dans la console ;
- erreur d’URL affichée en ligne, focus et valeur du nom conservés.

## Vérification automatisée

Commande finale exécutée dans l’environnement Python 3.12 contraint :

```powershell
python tools/check_quality.py
```

Résultat :

```text
versions contraintes : conformes
Ruff erreurs critiques : conforme
Ruff format : 18 fichiers conformes
Mypy : 15 modules conformes
liens documentaires locaux : conformes
pytest : 100 tests et 40 sous-tests réussis en 9,33 s
```

Les quatre nouveaux tests d’acceptation couvrent les valeurs par défaut et la
navigation, les erreurs en ligne, le raccourci de premier cas et le contrat
d’accessibilité des aides.

## Limites assumées

- les libellés et descriptions sont finalisés côté navigateur ; sans JavaScript,
  le libellé implicite reste lisible mais `aria-describedby` n’est pas enrichi ;
- la création accélérée ajoute une suite racine déterministe, sans choisir une
  stratégie d’organisation à la place de l’utilisateur ;
- le lot ne change ni le cycle de vie du candidat généré ni son exécution : ces
  travaux restent la sortie attendue du lot 3.
