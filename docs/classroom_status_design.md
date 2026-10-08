# Spécification Technique : Gestion de l'État des Salles par Délégués (Option B Adoptée)

## 1. Contexte & Modèle Retenu

Dans les versions antérieures du projet, deux options avaient été identifiées pour la déclaration d'occupation/libération des salles de classe :
- **Option A (Rejetée)** : Tout étudiant actif pouvait déclarer le statut de n'importe quelle salle. (Raison du rejet : Risque élevé de vandalisme d'état, déclarations conflictuelles ou malveillantes).
- **Option B (Adoptée et Implémentée)** : **Seuls les délégués désignés de chaque classe (`DELEGATE`) disposent du droit de déclarer l'état d'une salle physique (`OCCUPIED` / `FREE`).**

## 2. Modèle de Données & Entités

1. **`ClassGroup` (Promotion / Classe)** : Représente le groupe d'étudiants (ex. `GIT 3`, `MSP 1`).
2. **`Room` (Salle physique)** : Représente l'amphithéâtre ou la salle de cours (ex. `Amphi 500`, `Salle B12`).
3. **`ClassDelegate` (Délégué de classe)** : Relie un `User` (membre actif) à un `ClassGroup` avec le type `TITULAIRE` ou `SUPPLEANT`.
4. **`RoomStatusDeclaration` (Historique & Audit)** : Consigne chaque changement d'état avec `room_id`, `class_group_id`, `declared_by_user_id`, `status` (`OCCUPIED` | `FREE`), `note`, `declared_at`, et `expires_at`.

## 3. Rôles et Permissions

- **Délégué (`DELEGATE`)** :
  - Reçoit la permission `room.declare_status` scopée sur sa `ClassGroup`.
  - Peut déclarer l'occupation d'une salle avec expiration automatique (retour à `TO_CONFIRM` une fois la durée écoulée).
  - Est soumis à un rate-limit anti-abus (30 déclarations / heure / délégué).
- **Étudiant Standard (`STUDENT`)** :
  - Peut consulter en temps réel l'état des salles (`room.view`).
  - **Ne peut pas déclarer le statut d'une salle.**
  - Peut soumettre un signalement d'incohérence (`POST /community/rooms/{room_id}/flag`) en cas d'erreur constatée.

## 4. Anti-Abus & Expiration Automatique

1. **Expiration Temporelle** : Lorsqu'un délégué libère une salle ou la déclare occupée pour 1h ou 2h, un horodatage `expires_at` est calculé. À l'échéance, un job d'arrière-plan ou la requête de lecture fait repasser l'état de la salle à `TO_CONFIRM`.
2. **Auditabilité** : Toute déclaration de salle est consignée dans `room_status_declarations` et dans `audit_log`.
