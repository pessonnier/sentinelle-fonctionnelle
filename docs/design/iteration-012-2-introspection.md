# Introspection — de la démonstration RH à une chaîne auditable

## Question examinée

La cible RH prouve-t-elle seulement que Playwright sait remplir un formulaire,
ou permet-elle réellement d’évaluer les choix structurants de Sentinelle
Fonctionnelle ?

La première version était utile, mais sa preuve restait partielle :

- un workflow JSON produisait un script lisible ;
- deux classeurs fournissaient les valeurs ;
- un parcours Chromium réussissait ;
- les champs statiques, JavaScript et conditionnels étaient exercés.

Le générateur chargeait toutefois la première ligne de chaque classeur et
fusionnait les colonnes sans conserver leur provenance. Cette convention
silencieuse était le principal risque de conception.

## Ce que la cible RH est réellement utile pour évaluer

### Analyse des pages

Le HTML volontairement hétérogène distingue trois capacités :

1. le parseur statique découvre les éléments présents dans la réponse HTML ;
2. un futur explorateur authentifié devra découvrir les éléments dépendant
   d’une session ;
3. l’exécution Playwright découvre et manipule les composants JavaScript.

La cible ne doit pas masquer ces différences. Cataloguer manuellement un champ
JavaScript dans le workflow est acceptable pour tester le générateur, mais ne
constitue pas une réussite de l’analyse dynamique.

### Données de test

Les classeurs permettent de vérifier le refus des formules actives, la
conservation des types simples, l’usage de clés métier stables, la séparation
entre données et code et la répétition du même comportement avec plusieurs
collaborateurs.

Ils deviennent réellement utiles lorsque le rapport peut dire quelles lignes
ont été exécutées. « Première ligne » n’est pas une identité exploitable.

### Génération

La génération est utile si elle est déterministe, explicable et reproductible.
La qualité du code ne suffit pas. Il faut pouvoir relier la structure confirmée,
les sources de données, le code produit et l’exécution observée.

### Exécution

Une validation locale apporte un retour rapide au concepteur. Elle ne doit pas
être confondue avec l’exécution CI isolée. La preuve locale répond à la question
« ce candidat fonctionne-t-il sur cette cible locale ? », pas à la question
« ce bundle respecte-t-il toutes les garanties réseau et conteneur de
production ? ».

## Alternatives étudiées

### Fusionner implicitement les premières lignes

Avantage : très peu de configuration.

Refusé comme modèle durable parce que deux fichiers peuvent contenir la même
colonne, que l’ordre des lignes devient une règle cachée et que le résultat ne
désigne pas les données exécutées.

### Produire le produit cartésien des classeurs

Avantage : couverture maximale apparente.

Refusé parce que le nombre de cas explose et que la majorité des associations
peuvent être fonctionnellement incohérentes. Deux sources de trois lignes
produiraient neuf cas sans confirmation de ces neuf combinaisons.

### Déduire automatiquement une jointure

Avantage : moins de saisie.

Refusé parce qu’un nom de colonne commun ne prouve pas une relation métier.
Une jointure doit être explicite et contrôlable.

### Copier les valeurs XLSX dans le code généré

Avantage : script autonome.

Refusé parce que les données seraient dupliquées, les changements difficiles à
auditer et le code ne testerait plus l’intégration tabulaire.

### Faire exécuter le test par le processus web

Avantage : bouton d’exécution très simple.

Refusé parce que le code généré est non fiable. La spécification impose une
frontière avec le service de conception. La verticale courante utilise donc une
commande CLI non interactive ; le runner OCI restera un incrément distinct.

### Utiliser le LLM pour écrire directement le fichier final

Avantage : flexibilité.

Refusé pour le chemin nominal. Le LLM aide à compléter le modèle structuré,
mais le fichier est reconstruit de manière déterministe. Une même entrée produit
ainsi la même empreinte.

## Choix retenu : matrice explicite

Le document de génération possède maintenant :

```json
{
  "data_sources": [
    {
      "id": "login",
      "path": "outputs/hr-demo/connexion-rh.xlsx",
      "key_column": "case_id"
    }
  ],
  "data_cases": [
    {
      "id": "manager-zoe-nebuleuse",
      "rows": {
        "login": "LOGIN-MANAGER-OK",
        "employee": "EMPLOYEE-MANAGER-01"
      }
    }
  ]
}
```

Chaque cas sélectionne exactement une ligne de chaque source. Une association
incomplète, une source inconnue ou un identifiant dupliqué est refusé avant la
génération.

Les jetons sont qualifiés :

```text
{{data.login.email}}
{{data.employee.first_name}}
```

Ce nommage évite les collisions et rend la provenance visible.

## Choix retenu : manifeste reproductible

La génération produit à côté du script un manifeste JSON contenant :

- la version du générateur ;
- l’empreinte canonique du document de génération ;
- l’empreinte du code Python ;
- l’identité et l’empreinte de chaque classeur ;
- le nombre de cas paramétrés.

Aucun horodatage n’est ajouté au manifeste : à entrées identiques, son contenu
reste identique. L’horodatage appartient au rapport d’exécution.

Le code vérifie également les empreintes XLSX lors de sa collecte. Modifier un
classeur après génération provoque un échec explicite avant la navigation.

## Choix retenu : validation locale bornée

La commande `run-playwright` :

- accepte uniquement un fichier sous `tests/generated` ;
- exige son manifeste ;
- refuse un code dont l’empreinte a changé ;
- limite cette première verticale à une cible HTTP de boucle locale ;
- lance pytest sans shell ;
- applique un délai global ;
- produit `junit.xml`, `stdout.log`, `stderr.log` et `execution.json` ;
- rattache le rapport aux empreintes du test et du manifeste.

Cette commande est adaptée à la validation individuelle d’un candidat. Elle ne
revendique ni l’isolation OCI, ni le filtrage réseau général, ni la sélection de
suites et de tags.

## Résultat de l’expérience

Le 30 juillet 2026, Chromium a exécuté :

- `manager-zoe-nebuleuse` ;
- `manager-iris-comete`.

JUnit rapporte deux tests, zéro échec, en 3,86 secondes. Le rapport structuré
porte le statut `passed`, le code de sortie `0` et les empreintes exécutées.

## Ce que cette phase ne prouve toujours pas

- la découverte automatique des champs JavaScript ;
- l’exploration authentifiée contrôlée ;
- l’isolation du runner dans un conteneur ;
- la restriction réseau à une liste d’origines ;
- la sélection de suites, tags ou déclarations CI ;
- la conservation de personnalisations manuelles lors d’une régénération ;
- le masquage de données sensibles dans des traces Playwright ou HAR ;
- l’exécution multi-navigateurs.

## Prochains choix recommandés

1. Ajouter un explorateur Playwright authentifié qui transforme le DOM rendu en
   catalogue stable, sans recopier les identifiants temporaires du navigateur.
2. Séparer le runner dans son propre paquet et son image OCI avant toute cible
   distante.
3. Présenter la matrice de données dans l’interface avec aperçu des associations
   et estimation du nombre de cas.
4. Ajouter le cycle candidat, exécution réussie, approbation de l’empreinte puis
   invalidation à la moindre modification.
5. Introduire les traces seulement après la politique de masquage et
   d’expiration, car une trace DOM peut contenir davantage de données que le
   rapport synthétique.
