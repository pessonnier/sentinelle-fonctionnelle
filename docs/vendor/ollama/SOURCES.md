# Documentation Ollama conservée localement

Instantané téléchargé le **29 juillet 2026** depuis la documentation officielle
Ollama. Il permet d’auditer la configuration du profil local et d’identifier une
évolution ultérieure du protocole ou du catalogue de modèles.

| Fichier | Source officielle | Usage | SHA-256 |
|---|---|---|---|
| `openai-compatibility.html` | <https://docs.ollama.com/api/openai-compatibility> | endpoint `chat/completions`, format JSON et paramètres compatibles | `1C7E6779F63D7AF2C6E798B7F86DB323093F53A85C9AA33F978598D002A63601` |
| `structured-outputs.html` | <https://docs.ollama.com/capabilities/structured-outputs> | contrainte de réponse structurée | `BEAD27EFC0B9BE8AD187E6C498A95670D54CFAD09C6882592223BA3D190B7D9A` |
| `modelfile.html` | <https://docs.ollama.com/modelfile> | alias local, contexte et température | `117EC405AB9DB5FCDFB93C93BE095C92E5ABFF9541969B93FFACB1228133E639` |
| `qwen3.6-tags.html` | <https://ollama.com/library/qwen3.6/tags> | tag source et quantification du modèle | `C24D5BC2F0DF8E58037A918A8EC8119D8CF89F92DFBDB5A1F00BE8B2CE12FAC1` |

## Règles d’utilisation

- Utiliser [`docs/llm/ollama.md`](../../llm/ollama.md) pour la procédure
  opérationnelle du projet.
- Ne pas injecter ces pages HTML brutes dans un prompt.
- Après actualisation, recalculer les empreintes et vérifier l’adaptateur, le
  Modelfile, le test de connectivité et le profil YAML.
- La présence d’une option dans la documentation ne prouve pas qu’un modèle ou
  le matériel courant la prend effectivement en charge.
