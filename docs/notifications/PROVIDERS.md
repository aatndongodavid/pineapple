# Évaluation des Prestataires et Adaptateurs pour Notifications Multicanal

**Établissement & Contexte** : Pineapple OS / Campus Infrastructure  
**Région / Pays** : Cameroun (Afrique Centrale) — Indicatif `+237`  
**Fuseau Horaire** : `Africa/Douala` (WAT - UTC+1)  
**Devise** : XAF (FCFA)  

---

## 1. SMS Gateway (Cameroun & Afrique Centrale)

### 1.1 Prestataires Analysés

| Prestataire | Couverture | Modèle Tarifaire | Authentification | Contraintes & Réglementation | Adaptateur In-App |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Orange Cameroon SMS API** | Orange CM (`+237 69x...`) | ~10–15 XAF / SMS | OAuth2 (Client Credentials) | Enregistrement de Sender ID obligatoire auprès de l'ART / Orange | `OrangeSmsAdapter` |
| **MTN Cameroon SMS API** | MTN CM (`+237 67x/68x...`) | ~10–15 XAF / SMS | API Key / Basic Auth | Sender ID validé | `MtnSmsAdapter` |
| **Twilio SMS Gateway** | International & CM | ~$0.05–0.08 / SMS (~30–50 XAF) | Account SID + Auth Token | Plus coûteux au Cameroun, idéal en fallback international | `TwilioSmsAdapter` |
| **Simulated Console Gateway** | Dev / Tests local | 0 XAF | Aucun | Mode par défaut sans coût | `SimulatedSmsAdapter` |

### 1.2 Règles et Quotas Établissement
- **Consommation Payante** : Le SMS est facturé par SMS envoyé. En raison des coûts, les SMS sont réservés exclusivement aux notifications de criticité **`CRITICAL`** (sécurité du compte, annulation de cours le jour même, impayé avant suspension).
- **Consommation Plafonnée** : Chaque établissement (`tenant`) dispose d'un quota mensuel (`channel_quotas`).
- **Consentement Légal (Opt-In)** : Un consentement explicite (`sms_consent=True`) est requis selon la réglementation camerounaise de protection des données (ART).
- **Format** : Longueur maximale de 160 caractères GSM 7-bit par SMS.

---

## 2. WhatsApp Business API (Optionnel)

### 2.1 Prestataires Analysés

| Prestataire | Type | Modèle Tarifaire | Modèles de Message | Adaptateur |
| :--- | :--- | :--- | :--- | :--- |
| **Meta WhatsApp Cloud API** | API Directe Cloud | Facturation par conversation (Utility/Authentication) | **Modèles pré-approuvés (HSM)** obligatoires pour initier la conversation | `WhatsAppCloudApiAdapter` |
| **Twilio for WhatsApp** | API Tierce | Coût Meta + Marge Twilio | Modèles enregistrés dans Twilio Console | `TwilioWhatsAppAdapter` |
| **Simulated Adapter** | Dev / Mock | 0 XAF | Libres | `SimulatedWhatsAppAdapter` |

### 2.2 Exigences Métier & Sécurité WhatsApp
- Les messages initiés par l'établissement nécessitent un **Template pré-approuvé par Meta**.
- **Opt-in explicite** dédié requis.
- Les données sensibles (mots de passe, codes confidentiels) sont strictement interdites dans les messages marketing/info.

---

## 3. Web Push (VAPID / Service Worker)

- **Standard** : VAPID (Voluntary Application Server Identification for RFC 8292 / 8291).
- **Gestion des Expirations** : Interception automatique des réponses HTTP `410 Gone` / `404 Not Found` pour révoquer automatiquement l'abonnement expiré (`push_subscriptions.is_active = False`).
- **Dégradation** : Android Chrome / Edge support complet ; iOS Safari via PWA installée (Web Push API sur iOS 16.4+).

---

## 4. Matrice des Adaptateurs et Fallbacks

```mermaid
graph TD
    A["Événement Métier (Outbox)"] --> B["Preference & Quota Engine"]
    B -->|Canal In-App| C["InAppChannel Adapter (DB + WebSocket)"]
    B -->|Canal Web Push| D["WebPushChannel Adapter (VAPID)"]
    B -->|Canal E-mail| E["EmailGateway (MailHog / SMTP / SendGrid)"]
    B -->|Canal SMS (CRITICAL + Quota)| F["SmsGateway (Orange/MTN/Twilio/Simulated)"]
    B -->|Canal WhatsApp (Optionnel)| G["WhatsAppChannel (Simulated / Meta Cloud API)"]

    D -->|410 Expired| D1["Revoke Push Subscription"]
    F -->|Failed or Quota Exceeded| E
```

---

## 5. Liste des TODO(externe)

- `TODO(externe)` : Enregistrer les identifiants de production Orange SMS API (`ORANGE_SMS_CLIENT_ID`, `ORANGE_SMS_CLIENT_SECRET`, `SENDER_ID`).
- `TODO(externe)` : Déposer les modèles de messages WhatsApp Business sur Meta Business Manager pour validation HSM.
- `TODO(externe)` : Générer les clés VAPID publiques/privées pour le serveur Web Push en production (`VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_CLAIM_EMAIL`).
