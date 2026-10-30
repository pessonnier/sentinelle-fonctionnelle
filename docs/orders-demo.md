# Démonstrateur de commandes multi-écrans

Le **Comptoir des commandes** est une cible locale destinée à concevoir et à
exécuter des tests fonctionnels traversant plusieurs pages.

## Parcours couvert

1. `/demo/commandes/client` saisit l'identité, le type de client, une date, une
   priorité et des notes.
2. `/demo/commandes/articles/{id}` présente un tableau de produits, des
   quantités, une liste de livraison, un code de remise et une case à cocher.
3. `/demo/commandes/recapitulatif/{id}` restitue les valeurs et calcule la
   remise, les frais, la TVA et le total.
4. `/demo/commandes/suivi/{id}` expose le statut et les articles dans des
   tableaux en lecture seule.

Le jeu nominal sélectionne deux claviers et une station USB-C, applique
`DEMO10`, ajoute un emballage et obtient un total de **287,12 €**.

## Charger le projet de conception

Après avoir lancé l'application, créer le projet d'exemple dans la base locale :

```powershell
.\.venv\Scripts\python.exe -m sentinelle_fonctionnelle.cli seed-orders-demo-project
```

Le catalogue affiche alors **Exemple — Comptoir des commandes**, avec un
workflow confirmé de quatre pages et dix-huit étapes prêt à être régénéré.

## Personnaliser le code généré

Chaque candidat déterministe contient une zone de cette forme :

```python
# sentinelle:custom:start after_workflow contract=python-playwright-page-data-v1
pass
# sentinelle:custom:end after_workflow
```

Télécharger le fichier depuis le cas, modifier uniquement le contenu entre ces
deux marqueurs, puis utiliser **Créer le candidat personnalisé**. Le serveur
refuse une modification extérieure ou un fichier Python invalide.

Le bouton **Régénérer en conservant ces personnalisations** fusionne la zone
dans la nouvelle génération si son contrat est toujours compatible. Un conflit
est affiché explicitement et bloque l'exécution jusqu'à sa résolution.
