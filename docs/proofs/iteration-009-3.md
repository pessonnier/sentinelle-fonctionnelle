# Preuve — itération 009.3

Date : **29 juillet 2026**

## Périmètre

Spécifications : `EF-003`, `EF-003.1`, `EF-003.2`, `EF-004`, `GEN-002.1`  
Acceptation : contribution à `ACC-057` et `ACC-059`, sans les déclarer vérifiés

## Fichiers principaux

- `src/sentinelle_fonctionnelle/adapters/design_llm.py`
- `src/sentinelle_fonctionnelle/application/design_assistant.py`
- `src/sentinelle_fonctionnelle/web/app.py`
- `src/sentinelle_fonctionnelle/web/static/generation-configuration.js`
- `src/sentinelle_fonctionnelle/web/static/case-editor.js`
- `src/sentinelle_fonctionnelle/web/templates/generation_configuration.html`
- `src/sentinelle_fonctionnelle/web/templates/case_guided.html`
- `config/ollama/qwen3.6-35b-a3b-q4_K_M_128k.Modelfile`
- `config/ollama/connectivity-request.json`
- `config/ollama/connectivity-reduced-context-request.json`
- `docs/llm/ollama.md`

## Test RED

Avant installation, `GET http://127.0.0.1:11434/api/version` échouait par
connexion refusée. Après installation et création du modèle, l’appel
`POST /v1/chat/completions` au profil 128K exact a expiré après 600,002 secondes
sans recevoir d’octet. Le journal Ollama indique un abandon avant la fin du
chargement et `timed out waiting for llama-server to start`.

## Test GREEN partiel

- Ollama installé : version `0.32.5` ;
- port par défaut joignable sur `127.0.0.1:11434` ;
- modèle source `qwen3.6:35b-a3b-q4_K_M` téléchargé, environ 24 Go ;
- digest du manifeste :
  `07d35212591fc27746f0a317c975a6d68754fb38e9053d82e25f06057af28522` ;
- alias demandé créé et `num_ctx 131072` vérifié ;
- diagnostic natif avec le même alias et `num_ctx 4096` réussi :
  JSON conforme, 112,304 s au total, dont 79,547 s de chargement.
- développement réel d’un cas de connexion à partir de quatre champs HTML :
  quatre opérations canoniques, aucune question résiduelle, résultat obtenu en
  67,481 s et conservé dans
  [`ollama-design-case-response.json`](ollama-design-case-response.json).

Le succès réduit prouve le fonctionnement du modèle et de la sortie structurée,
mais pas sa capacité 128K. Le profil applicatif est donc conservé désactivé.

## Contrôles automatisés

```text
Test ciblé : 7 tests, OK
Test de l’instantané Ollama : 1 test, OK
Test de la réponse réelle Qwen : 1 test, OK
Suite complète : Ran 51 tests, OK
Compilation Python : compileall, OK
Syntaxe JavaScript : node --check, OK
Point d’entrée CLI : /health et /configuration/generation, HTTP 200
Contenu réel : modèle exact, bouton de sonde et état désactivé visibles
Navigateur : bloqué par ERR_BLOCKED_BY_CLIENT sur les URL locales
```

## Revue sécurité

- aucune clé requise ou persistée pour la boucle locale ;
- la sonde n’envoie aucun contenu métier ;
- l’adaptateur borne la sortie, n’enregistre pas le raisonnement et limite la
  réponse brute à 2 Mio ;
- le profil peut être testé avant activation ;
- l’origine reste `127.0.0.1`, sans exposition distante implicite.

## Limites externes

Le matériel courant (environ 32 Go de RAM et RTX 3070 Laptop) n’a pas chargé le
profil 128K dans le délai maximal. `ACC-057` reste non vérifié : l’activation
automatique après contrôle, le diagnostic séparé des capacités et la réussite
128K doivent encore être couverts.
