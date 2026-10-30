---
name: generate-python-playwright-code
description: Générer un candidat de test Python pytest-playwright depuis un workflow fonctionnel confirmé, ses champs HTML analysés et un profil de génération borné. Utiliser ce skill pour demander du code de test traçable sans inventer de cible, de donnée, de secret ou de comportement métier.
---

# Générer un test Python Playwright

## Entrées exigées

Refuser la génération si le workflow n’est pas confirmé, si le profil de
génération ou l’accès LLM exact manque, si une cible utilisée n’appartient pas
au catalogue HTML, ou si aucune assertion observable n’est définie.

## Procédure

1. Lire uniquement la définition structurée, le profil effectif et les skills
   déclarés. Ne pas reconstruire le test depuis la conversation.
2. Conserver l’ordre des étapes, l’intention métier et les références de données.
3. Traduire chaque cible avec son localisateur analysé : rôle et nom accessible,
   libellé, attribut de test, puis CSS stable.
4. Produire une assertion Playwright pour chaque contrôle confirmé.
5. Résoudre les secrets uniquement à l’exécution depuis leurs références. Ne
   jamais écrire leur valeur dans le prompt, le code ou les commentaires.
6. Éviter les temporisations arbitraires, le JavaScript libre, les sélecteurs de
   position et toute navigation vers une origine non autorisée.
7. Respecter les motifs de fichiers, la limite de fichiers, la politique de
   preuve et les validations du profil.

## Contrat de sortie

Répondre uniquement avec un objet JSON :

```json
{
  "schema_version": 1,
  "files": [
    {"path": "tests/generated/test_exemple.py", "content": "..."}
  ],
  "assumptions": [],
  "warnings": []
}
```

Chaque chemin doit rester sous la racine configurée. Une ambiguïté devient un
avertissement bloquant ; elle ne doit jamais être transformée en code inventé.

## Vérification

- Vérifier la syntaxe et les imports.
- Vérifier qu’au moins une assertion fonctionnelle est générée.
- Vérifier les origines, les localisateurs et les références de données.
- Rechercher les secrets et valeurs sensibles dans tous les fichiers.
- Ne jamais approuver automatiquement le candidat.
