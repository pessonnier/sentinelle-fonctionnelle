# Avancement de l'implémentation

Ce document est le tableau de bord durable de SentinelleFonctionnelle. Il est mis à
jour après chaque tranche verticale et complète les spécifications sans en
modifier les identifiants.

## Règles de suivi

Les états signifient :

- `À faire` : aucun test d'acceptation écrit ;
- `RED` : test écrit et observé en échec pour la raison attendue ;
- `En cours` : implémentation engagée ;
- `Implémentée` : test ciblé réussi ;
- `Vérifiée` : test ciblé, suite complète et véritable point d'entrée réussis ;
- `Bloquée` : dépendance ou décision manquante explicitée.

Une fonctionnalité n'est jamais déclarée `Vérifiée` sur la seule présence de
code ou de documentation.

## Tableau de bord MVP

| Indicateur | Avancement |
|---|---:|
| Capacités de la tranche A vérifiées | 5 / 25 |
| Capacités de la tranche B vérifiées | 0 / 15 |
| Critères d'acceptation vérifiés | 19 / 72 |

## Tranches verticales

| Tranche | Spécifications | Acceptation | État | Preuve |
|---|---|---|---|---|
| 001 — Projet et arborescence initiale | `EF-001`, `EF-002`, `EF-007` | `ACC-002`, `ACC-003` | Vérifiée | [`proofs/iteration-001.md`](proofs/iteration-001.md) |
| 002 — Modes local/en ligne et isolation | `EF-001.1`, `ENF-008`, `ENF-013` | `ACC-051`, `ACC-052` | Vérifiée | [`proofs/iteration-002.md`](proofs/iteration-002.md) |
| 003 — Persistance SQLite locale | `EF-001`, `EF-002`, `ENF-001`, `ENF-013` | `ACC-053` | Vérifiée | [`proofs/iteration-003.md`](proofs/iteration-003.md) |
| 004 — Tutoriel HTML local | `DOC-001` à `DOC-006` | `ACC-054` | Vérifiée | [`proofs/iteration-004.md`](proofs/iteration-004.md) |
| 005 — Interface web locale persistante | `EF-001.2`, `EF-002`, `EF-002.1`, `ENF-013` | `ACC-060`, `ACC-061`, `ACC-062`, `ACC-069`, `ACC-070`, `ACC-071`, `ACC-072` | Vérifiée | [`proofs/iteration-005.md`](proofs/iteration-005.md) |
| 006 — Spécifications multi-formats et vues | `EF-007`, `EF-007.4` | `ACC-063`, `ACC-064`, `ACC-065` | Vérifiée | [`proofs/iteration-006.md`](proofs/iteration-006.md) |
| 007 — Données CSV/XLSX et stratégies | `EF-007.2`, `EF-007.5` | `ACC-066`, `ACC-067`, `ACC-068` | Vérifiée | [`proofs/iteration-007.md`](proofs/iteration-007.md) |
| 008 — Dialogue, description et catalogues | `EF-004`, `EF-005`, `EF-017` | `ACC-007` à `ACC-009`, `ACC-032` | À faire | — |
| 009 — Préconditions, données et contrôles | `EF-007.1`, `EF-007.2`, `ENF-012` | `ACC-033`, `ACC-034` | À faire | — |
| 010 — Validation individuelle et empreinte | `EF-008`, `EF-009` | `ACC-010` à `ACC-014` | À faire | — |
| 011 — Modèle intermédiaire et génération | `GEN-001` à `GEN-006` | `ACC-041`, `ACC-042` | À faire | — |
| 012 — Bundle, personnalisation et contrôles | `GEN-007` à `GEN-014` | `ACC-016`, `ACC-028`, `ACC-043` | À faire | — |
| 013 — Runner et rapports | `EF-012` à `EF-015`, `ENF-005` | `ACC-017` à `ACC-025` | À faire | — |
| 014 — Définition des profils de charge | `LOAD-001` à `LOAD-006` | `ACC-044`, `ACC-045` | À faire | — |
| 015 — Export de charge sécurisé | `LOAD-007` à `LOAD-011` | `ACC-046` | À faire | — |
| 016 — Export, CI et publication | `EF-016`, `ENF-011` | `ACC-026`, `ACC-027`, `ACC-047` à `ACC-050` | À faire | — |


## Contrat de preuve

Chaque fichier de preuve enregistre :

```text
Spécifications :
Acceptation :
Fichiers modifiés :
Test RED :
Test GREEN :
Suite complète :
Point d'entrée réel :
Limites externes :
Revue sécurité :
```
