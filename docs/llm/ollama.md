# Configurer et tester Ollama

Cette procédure décrit la configuration locale réellement utilisée par
SentinelleFonctionnelle le **29 juillet 2026**. Elle sépare volontairement trois
contrôles : l’accès au service Ollama, la présence du modèle et sa capacité à
produire le JSON structuré attendu. Le troisième contrôle est le seul qui valide
le profil pour le dialogue de conception.

## Configuration retenue

| Paramètre | Valeur |
|---|---|
| Fournisseur | `ollama` |
| API applicative | compatible OpenAI |
| URLs préconfigurées | `http://127.0.0.1:11436/v1` et `http://127.0.0.1:11434/v1` |
| Modèle | `qwen3.6-35b-a3b-q4_K_M_128k:latest` |
| Modèle Ollama source | `qwen3.6:35b-a3b-q4_K_M` |
| Contexte demandé | 131 072 jetons |
| Température | `0.1` |
| Délai | 600 secondes |
| Nouvelles tentatives | `0` |
| Authentification | aucune sur la boucle locale |

Le nom demandé n’est pas un tag public Ollama. Il est créé localement comme un
alias reproductible à partir du tag officiel et du
[`Modelfile`](../../config/ollama/qwen3.6-35b-a3b-q4_K_M_128k.Modelfile).
Ne remplacez pas ce fichier par une option passée seulement au moment de
l’appel : la configuration effective doit rester vérifiable.

## 1. Installer et démarrer Ollama sous Windows

Installation avec le gestionnaire de paquets Windows :

```powershell
winget install --exact --id Ollama.Ollama `
  --accept-package-agreements `
  --accept-source-agreements
```

Ollama démarre normalement comme application utilisateur et écoute par défaut
sur le port `11434`. Vérifiez d’abord le service, sans charger de modèle :

```powershell
Invoke-RestMethod `
  -Uri 'http://127.0.0.1:11434/api/version' `
  -TimeoutSec 5
```

Résultat observé sur la machine testée :

```json
{"version":"0.32.5"}
```

Une erreur « connexion refusée » signifie que l’application Ollama n’est pas
démarrée, que le port a été changé ou que la requête n’atteint pas la même
machine. Ce contrôle ne prouve encore ni la présence du modèle, ni sa capacité
d’inférence.

## 2. Télécharger le modèle et créer l’alias 128K

Le tag officiel correspondant à la quantification demandée est :

```powershell
ollama pull qwen3.6:35b-a3b-q4_K_M
```

Le téléchargement observé représente environ **24 Go** et son manifeste
référence le digest :

```text
07d35212591fc27746f0a317c975a6d68754fb38e9053d82e25f06057af28522
```

Créez ensuite l’identifiant exact utilisé par le profil :

```powershell
ollama create qwen3.6-35b-a3b-q4_K_M_128k:latest `
  -f .\config\ollama\qwen3.6-35b-a3b-q4_K_M_128k.Modelfile
```

Contrôlez la présence et la configuration :

```powershell
ollama list
ollama show qwen3.6-35b-a3b-q4_K_M_128k:latest --modelfile
```

La seconde commande doit notamment afficher `PARAMETER num_ctx 131072` et
`PARAMETER temperature 0.1`.

## 3. Configurer SentinelleFonctionnelle

Deux connexions sont préconfigurées dans
**[Accès aux LLM](/configuration/llm-access)**. Le profil de génération associé
se consulte dans **[Génération de code](/configuration/code-generation)** :

| Profil | URL | Profil de génération associé |
|---|---|---|
| `ollama-qwen36-128k-11436@1` | `http://127.0.0.1:11436/v1` | `python-playwright-qwen36-11436@1` |
| `ollama-qwen36-128k@1` | `http://127.0.0.1:11434/v1` | `python-playwright-qwen36@1` |

Les deux utilisent la configuration suivante, avec le port correspondant :

```yaml
id: ollama-qwen36-128k
version: 1
name: Ollama local 11434 — Qwen3.6 35B 128K
provider: ollama
base_url: http://127.0.0.1:11434/v1
model: qwen3.6-35b-a3b-q4_K_M_128k:latest
api_key_environment: ''
organization_environment: ''
request_timeout_seconds: 600
max_retries: 0
enabled: true
```

Les profils locaux actifs sont conservés dans
[`data/generation-profiles.yaml`](../../data/generation-profiles.yaml) et dans
les valeurs par défaut embarquées. Le test de connexion confirme l’accès à
l’API et au modèle ; un essai d’inférence représentatif reste nécessaire pour
qualifier les performances et la capacité de contexte de chaque instance.

L’URL applicative se termine par `/v1`, car l’adaptateur utilise
`POST /v1/chat/completions`. Les contrôles d’administration Ollama, tels que
`/api/version` et `/api/tags`, utilisent l’origine sans `/v1`.

Dans **Accès aux LLM**, le bouton ↻ du champ **Modèle** utilise cette même URL
pour appeler `GET /api/tags`, dédupliquer les propriétés `name` et `model`, puis
alimenter la liste déroulante sans enregistrer le profil.

## 4. Tester depuis l’application

Dans la carte du profil, deux contrôles indépendants sont disponibles :

1. **Vérifier le serveur et le modèle** interroge `/api/version` et `/api/tags`
   sans charger le modèle en mémoire ;
2. **Tester l’inférence JSON** charge le modèle, appelle
   `/v1/chat/completions` et vérifie le contrat structuré ci-dessous.

Le second contrôle envoie un message synthétique sans donnée métier et exige :

```json
{
  "schema_version": 1,
  "questions": [],
  "operations": []
}
```

Les deux contrôles valident ensemble :

1. l’accès HTTP au fournisseur ;
2. la résolution du nom exact du modèle ;
3. la compatibilité de l’endpoint `chat/completions` ;
4. la sortie JSON ;
5. le contrat de dialogue de conception.

La sonde limite la réponse à 256 jetons et désactive l’effort de raisonnement
Ollama. Un dialogue réel est limité à 4 096 jetons de sortie. Les traces de
raisonnement ne sont ni demandées ni enregistrées.

Un succès affiche la version du moteur, la présence du modèle ou la mention
« JSON structuré accepté ». Un échec laisse le profil inchangé et affiche le
diagnostic retourné par le fournisseur, notamment une éventuelle erreur
d’allocation mémoire lors du chargement du modèle.

Le champ **Interagir avec le LLM** permet également d’envoyer un message libre
de 4 000 caractères au maximum et d’afficher sa réponse. Ce message n’est pas
enregistré dans le catalogue. Aucun secret n’est envoyé par les sondes.

## 5. Résultats réels du 29 juillet 2026

| Contrôle | Résultat |
|---|---|
| Port `127.0.0.1:11434` avant installation | échec attendu, connexion refusée |
| Installation Ollama | réussie |
| `GET /api/version` | réussi, version `0.32.5` |
| Présence du tag officiel | réussie |
| Création de l’alias 128K exact | réussie |
| Vérification du `Modelfile` | réussie, `num_ctx 131072` |
| Appel OpenAI compatible avec le profil 128K | échec après 600 s, aucun octet reçu |
| Diagnostic natif avec contexte 4 096 | réussi en 112,3 s, JSON conforme |

Le journal Ollama indique que le client a fermé la connexion avant la fin du
chargement, puis : `timed out waiting for llama-server to start`. La machine de
test dispose d’environ 32 Go de RAM et d’un GPU portable RTX 3070. Un modèle
quantifié d’environ 24 Go auquel s’ajoutent le cache de contexte 128K et les
buffers d’exécution laisse une marge insuffisante ou très faible. Le service et
le modèle sont donc installés, mais **l’inférence 128K n’est pas validée** sur ce
matériel. Les profils sont désormais préconfigurés comme actifs pour permettre
leur sélection ; cette activation ne constitue pas une qualification 128K et
`ACC-057` n’est pas déclaré vérifié sur la base de cet essai.

Le fichier
[`connectivity-reduced-context-request.json`](../../config/ollama/connectivity-reduced-context-request.json)
permet un diagnostic séparé à 4 096 jetons, sans modifier l’alias ni le profil
128K :

```powershell
curl.exe --max-time 600 `
  --header 'Content-Type: application/json' `
  --data-binary '@config/ollama/connectivity-reduced-context-request.json' `
  http://127.0.0.1:11434/api/chat
```

Le diagnostic observé a réussi avec 43 jetons d’entrée et 13 jetons de sortie :
79,5 s de chargement, 27,5 s d’évaluation du prompt et 5,2 s de génération,
soit 112,3 s au total. Ce succès prouve que les poids peuvent être chargés et
que le modèle respecte le petit contrat JSON, mais il ne valide pas la capacité
128K. Il ne justifie donc pas l’activation du profil.

### Vérification du profil 11436 le 2 août 2026

Le profil `ollama-qwen36-128k-11436@1` a été vérifié depuis Sentinelle :

| Contrôle | Résultat |
|---|---|
| `GET /api/version` et `GET /api/tags` | `ok`, Ollama `0.32.3`, modèle exact présent, 177 ms |
| **Tester l’inférence JSON** | JSON structuré conforme, 14,062 s |
| Dialogue du cas RH nominal | 23 étapes et catalogues relus, réponse en 33,5 s |
| Décision humaine | deux propositions laissées en attente, aucune application automatique |

Cet essai valide la connexion, le chargement du modèle, l’API compatible OpenAI
et le contrat de dialogue sur le brouillon RH réel. Il ne mesure toujours pas
une fenêtre d’entrée remplie à 128K jetons.

## 6. Produire un cas développé avec le LLM

Une fois le test complet réussi et le profil activé :

1. sélectionnez `python-playwright-qwen36-11436@1` ou
   `python-playwright-qwen36@1`, selon l’instance Ollama à utiliser ;
2. choisissez une intention fonctionnelle unique ;
3. renseignez l’objectif, l’acteur, la préparation, les références de fixtures
   et de secrets, sans aucune valeur secrète ;
4. analysez chaque page HTML autorisée ;
5. utilisez les références proposées pour les cibles d’action et de validation ;
6. lancez **Analyser les informations manquantes** ;
7. dans le dialogue, choisissez **Développer le cas complet** pour demander une
   revue de toutes les rubriques, **Exploiter les champs HTML** pour construire
   le parcours à partir des éléments réellement analysés, ou **Renforcer les
   validations** pour obtenir des preuves observables ;
8. répondez aux questions du modèle au lieu de lui laisser inventer un fait ;
9. relisez chaque opération et sa justification, puis acceptez uniquement les
   modifications correctes ;
10. vérifiez la structure JSON avant de confirmer le cas.

Le modèle reçoit le brouillon structuré, l’intention, les informations
manquantes, un inventaire borné des champs HTML et les huit derniers messages.
Il ne reçoit ni HTML brut, ni secret, ni droit de confirmer le workflow. Sa
réponse peut poser au plus huit questions et proposer au plus douze opérations
sur une liste fermée de champs. Cette structure est ensuite l’entrée du futur
workflow de génération Playwright ; la matérialisation du code reste une
tranche distincte.

Un exemple réel a été produit avec le même modèle à contexte réduit : quatre
étapes canoniques pour saisir l’e-mail par fixture, saisir le mot de passe par
référence de secret, cliquer sur le bouton analysé et valider le titre visible
de l’espace personnel. La réponse a pris 67,5 secondes et passe le parseur
strict de l’application. Elle est conservée dans
[`docs/proofs/ollama-design-case-response.json`](../proofs/ollama-design-case-response.json).

## 7. Dépannage

- **Connexion refusée** : démarrer Ollama et contrôler `/api/version`.
- **Modèle inconnu** : comparer exactement le nom du profil avec `ollama list`.
- **Délai pendant le chargement** : consulter
  `%LOCALAPPDATA%\Ollama\server.log`, la RAM, la VRAM et le contexte effectif.
- **JSON invalide** : vérifier que l’endpoint contient `/v1`, que la sortie
  structurée est prise en charge et que le raisonnement est désactivé.
- **Réponse trop lente** : tester séparément un contexte réduit, puis choisir du
  matériel adapté ou un modèle plus petit. Ne déclarer 128K validé qu’après un
  test 128K réussi.
- **Exposition réseau** : conserver `127.0.0.1` pour un usage monoposte. Une
  écoute distante exige une politique réseau, TLS et éventuellement un proxy
  authentifié ; l’absence de clé n’est acceptable que sur une origine locale ou
  explicitement approuvée.

## Documentation officielle vérifiée

Liens consultés le **29 juillet 2026** :

- [Ollama sous Windows](https://docs.ollama.com/windows)
- [Introduction à l’API Ollama](https://docs.ollama.com/api/introduction)
- [Compatibilité OpenAI](https://docs.ollama.com/api/openai-compatibility)
- [API native de conversation](https://docs.ollama.com/api/chat)
- [Référence des Modelfiles](https://docs.ollama.com/modelfile)
- [Sorties structurées](https://docs.ollama.com/capabilities/structured-outputs)
- [Modèle Qwen3.6](https://ollama.com/library/qwen3.6)
- [Tags Qwen3.6](https://ollama.com/library/qwen3.6/tags)

Les instantanés des quatre pages indispensables au fonctionnement sont
inventoriés avec leurs empreintes dans
[`docs/vendor/ollama/SOURCES.md`](../vendor/ollama/SOURCES.md).
