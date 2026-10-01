# Document de Conception : Déclaration de Statut des Salles (Option A)

## Contexte
Le module Community permet aux étudiants de visualiser et de déclarer la disponibilité des salles d'étude et d'amphithéâtres sur leur campus.

## Décision d'Architecture & Modélisation
Deux options ont été analysées :
- **Option A (Retenue)** : Conserver le droit de déclaration ouvert à tout étudiant de l'établissement disposant d'un compte validé (`status: ACTIVE`).
- **Option B (Rejetée pour l'étape actuelle)** : Introduire une table de correspondance `class_delegates` et une gestion de rôles complexes restreignant la déclaration aux seuls délégués de filières.

## Justification de l'Option A
1. **Fluidité et Responsabilisation Communautaire** : Permettre à n'importe quel étudiant présent dans une salle d'en mettre à jour le statut immédiatement garantit la réactivité de l'information.
2. **Auto-Modération et Expiration** : Les déclarations de statut disposent d'un mécanisme d'expiration automatique (`expires_at`), remettant la salle en état `TO_CONFIRM` si aucune nouvelle mise à jour n'est enregistrée.
3. **Piste d'Audit** : Chaque déclaration est liée à `declared_by_user_id`, permettant de tracer les abus éventuels via la modération `trust_safety_context`.
