# Documentation Playwright conservée localement

Instantané téléchargé le **27 juillet 2026** depuis la documentation officielle
Playwright Python. Ces fichiers servent de référence de conception au modèle
intermédiaire et au futur générateur ; ils ne remplacent pas le verrouillage des
versions de dépendances du runner.

| Fichier | Source officielle | Usage | SHA-256 |
|---|---|---|---|
| `locators.html` | <https://playwright.dev/python/docs/locators> | ordre de préférence, unicité et stabilité des localisateurs | `3DD3A7592A1DEEF3414F325788D75417E380BBFE189872FA0A70E1C1B1A51152` |
| `assertions.html` | <https://playwright.dev/python/docs/test-assertions> | correspondance entre validations structurées et assertions web-first | `602FE1B5C12A3326C50D7F8DCE6BE36A6B39FED47C6BC702604F328C8D80D322` |
| `pytest-plugin.html` | <https://playwright.dev/python/docs/test-runners> | fixtures pytest, options de navigateur et exécution | `010D67144C1BE072362B4D232FB51666BB21F58D0CF5CDA022D9A877945131E8` |
| `authentication.html` | <https://playwright.dev/python/docs/auth> | profils d’acteur et réutilisation contrôlée d’état d’authentification | `1B5AC6D627E7D3B955762AF301309C7D0A581BA3885253A34A0AED77B35D533F` |
| `api-testing.html` | <https://playwright.dev/python/docs/api-testing> | préparation, vérification de postconditions et nettoyage par API | `E9B3BA978656B6216D94914FF7B9D9CE6EDE77A712D0FDCAA264DEB08D5A88ED` |

## Règles d’utilisation

- Ne jamais injecter une page HTML complète dans un prompt.
- Extraire uniquement les règles nécessaires dans une configuration ou un
  schéma versionné et en conserver la provenance.
- Faire correspondre l’instantané à la version Playwright verrouillée par le
  runner avant de générer un artefact candidat.
- Après chaque actualisation, recalculer les empreintes, relire les changements
  affectant les localisateurs, assertions, fixtures ou états
  d’authentification et mettre à jour les tests concernés.
- Les exemples de la documentation ne constituent ni une fixture applicative,
  ni une politique de sécurité, ni une preuve d’exécution.
