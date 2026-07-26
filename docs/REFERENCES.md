# Références normatives et terminologiques

- **Projet :** SentinelleFonctionnelle
- **Dernière vérification :** 26 juillet 2026
- **Portée :** vocabulaire, processus et documentation du test logiciel

## 1. Objet

Ce document recense les sources de référence utilisées par les spécifications de SentinelleFonctionnelle. Il permet :

- d’employer un vocabulaire stable et reconnu dans le domaine du test logiciel ;
- de distinguer les concepts normatifs des conventions propres au produit ;
- de vérifier la version et le statut des documents utilisés ;
- de retrouver les sources officielles sans reproduire de contenu protégé.

L’emploi de ces références ne constitue pas, à lui seul, une déclaration de conformité de SentinelleFonctionnelle à l’ISO/IEC/IEEE 29119. Une telle déclaration nécessiterait une évaluation séparée des processus, des documents produits et des preuves d’application.

## 2. Normes ISO/IEC/IEEE

### ISO/IEC/IEEE 29119-1:2022 — Concepts généraux

- **Titre officiel :** *Software and systems engineering — Software testing — Part 1: General concepts*
- **Édition :** 2
- **Publication :** janvier 2022
- **Statut retenu :** norme publiée
- **Usage dans le projet :** concepts généraux du test logiciel et cohérence terminologique de la série 29119.
- **Source officielle :** [fiche ISO/IEC/IEEE 29119-1:2022](https://www.iso.org/standard/81291.html)

Cette édition remplace l’ISO/IEC/IEEE 29119-1:2013, retirée. La version 2013 ne doit donc pas être citée comme référence courante.

### ISO/IEC/IEEE 29119-2:2021 — Processus de test

- **Titre officiel :** *Software and systems engineering — Software testing — Part 2: Test processes*
- **Édition :** 2
- **Publication :** octobre 2021
- **Statut retenu :** norme publiée
- **Usage dans le projet :** planification, pilotage, conception, implémentation, exécution et clôture des activités de test.
- **Source officielle :** [fiche ISO/IEC/IEEE 29119-2:2021](https://www.iso.org/standard/79428.html)

### ISO/IEC/IEEE 29119-3:2021 — Documentation de test

- **Titre officiel :** *Software and systems engineering — Software testing — Part 3: Test documentation*
- **Édition :** 2
- **Publication :** octobre 2021
- **Statut retenu :** norme publiée
- **Usage dans le projet :** structure et contenu des plans de test, spécifications de cas de test, procédures, journaux et rapports.
- **Source officielle :** [fiche ISO/IEC/IEEE 29119-3:2021](https://www.iso.org/standard/79429.html)

Les fiches descriptives de l’ISO sont publiques. Le texte intégral des normes reste soumis aux conditions d’accès et de licence de l’ISO ; il n’est pas copié dans ce dépôt.

## 3. Références ISTQB

### Glossaire ISTQB

- **Titre :** *ISTQB Glossary*
- **Statut retenu :** glossaire officiel en ligne
- **Usage dans le projet :** vérification des termes usuels, des synonymes et des relations entre concepts.
- **Source officielle :** [glossaire ISTQB](https://glossary.istqb.org/)

Le glossaire doit être consulté dans sa version courante lors de toute introduction ou modification d’un terme métier.

### ISTQB Certified Tester Foundation Level v4.0.1

- **Titre :** *Certified Tester Foundation Level Syllabus v4.0.1*
- **Version :** 4.0.1
- **Date du syllabus :** 15 septembre 2024
- **Usage dans le projet :** activités de test, produits d’activités, planification, cas de test, procédures, suites et ordonnancement d’exécution.
- **Page officielle :** [ISTQB CTFL v4.0](https://www.istqb.org/certifications/certified-tester-foundation-level-ctfl-v4-0/)
- **Document officiel :** [syllabus ISTQB CTFL v4.0.1 au format PDF](https://www.istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf)

Le syllabus et le glossaire ISTQB complètent les normes ISO/IEC/IEEE pour l’usage professionnel courant. En cas de divergence portant sur une exigence normative, la norme ISO/IEC/IEEE applicable prévaut.

## 4. Correspondance terminologique du projet

| Terme français retenu | Terme anglais de référence | Usage dans SentinelleFonctionnelle |
|---|---|---|
| plan de test | test plan | objectifs, périmètre, approche, ressources, risques et critères ; non exécutable |
| base de test | test basis | sources utilisées pour l’analyse et la conception |
| condition de test | test condition | aspect testable servant de fondement à la conception |
| type de test | test type | objectif ou caractéristique de qualité visés |
| suite de tests | test suite | ensemble de cas de test ou de sous-suites préparé pour une exécution |
| cas de test | test case | préconditions, données d’entrée, actions, résultats attendus et postconditions |
| procédure de test | test procedure | séquence ordonnée nécessaire à l’exécution |
| script de test | test script | instructions manuelles ou automatisées mettant en œuvre le cas ou la procédure |
| données de test | test data | données nécessaires à l’exécution |
| objet de test | test object | composant ou système soumis au test |
| exécution de test | test execution | activité d’exécution d’une suite, d’une procédure ou d’un cas |
| résultat de test | test result | résultat observé et comparé au résultat attendu |

Les termes **jeu de tests** et **test** employé seul pour désigner un cas de test sont interdits dans les spécifications métier. Un **jeu de données de test** reste admis lorsqu’il désigne explicitement un ensemble de données et non une collection de cas de test.

## 5. Règles de maintenance

Toute modification du vocabulaire spécialisé doit :

1. vérifier la définition dans les références officielles ci-dessus ;
2. conserver la distinction entre plan de test, suite de tests, cas de test, script et exécution ;
3. mettre à jour simultanément la présente correspondance et le référentiel terminologique des spécifications ;
4. indiquer une convention propre au produit comme telle lorsqu’aucun terme normatif ne couvre exactement le besoin ;
5. vérifier le statut et la version des références au moins à chaque révision majeure des spécifications.

Les copies locales de normes ou de documents externes ne doivent être ajoutées au dépôt que si leur licence l’autorise explicitement. Les liens doivent toujours pointer vers l’organisme éditeur.
