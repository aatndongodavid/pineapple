# Décision Technique — Agrégateur de Paiement Mobile Money (Cameroun)

**Date** : 7 Octobre 2026  
**Auteur** : Ingénieur Backend / Fintech Senior — Pineapple OS  
**Contexte** : Encaissement des abonnements d'établissements scolaires au Cameroun (Zone CEMAC, XAF FCFA).  

---

## 1. Étude Comparative des Agrégateurs

Une étude des solutions de paiement couvrant le marché camerounais (Orange Money & MTN Mobile Money) a été menée sur 4 acteurs majeurs :

| Critère | **Campay** (Sélectionné) | **Notch Pay** | **CinetPay** | **Flutterwave** |
|---|---|---|---|---|
| **Origine / Ancrage** | Cameroun (Douala/Yaoundé) | Cameroun / Afrique | Côte d'Ivoire / Régional | Nigéria / Pan-Africain |
| **Couverture CM** | MTN MoMo & Orange Money 100% | MTN MoMo & Orange Money | MTN MoMo & Orange Money | MTN MoMo & Orange Money |
| **Expérience Utilisateur** | Push USSD direct sur mobile (`+237`) | SDK Modal / Redirection / API | Redirection / Web SDK | Redirection / API |
| **Frais de Transaction** | ~ 2,0% à 2,5% | ~ 2,2% à 2,5% | ~ 2,5% à 3,0% | ~ 3,5% + frais fixes |
| **Sandbox & DX** | API REST simple, Token JWT, Webhooks | API REST GraphQL/REST moderne | API REST v2 | API REST v3 |
| **Signature Webhook** | Signature HMAC-SHA256 | Signature HMAC-SHA512 | Token secret d'en-tête | Hash secret |
| **Agrément / Conformité** | Partenaire Banques & Telcos CM | Agrégateur sous-licencié | Établissement de paiement | Établissement de paiement |

---

## 2. Décision & Justification

La solution **Campay** (avec bascule automatique vers **FakeProvider** en mode dev/test et support d'adaptateur secondaire **Notch Pay**) est sélectionnée comme agrégateur Mobile Money principal pour Pineapple OS.

### Rationale :
1. **Intégration Native Push USSD** : L'administrateur saisit son numéro MTN ou Orange Money (`+237 6xxxxxxxx`), et reçoit directement l'invite de validation sur son écran de téléphone sans être redirigé hors de l'application.
2. **Excellente Fiabilité Locale** : Directement connecté aux passerelles USSD de MTN Cameroun et Orange Cameroun.
3. **Simplicité & Sécurité de l'API** : Authentification par jeton Bearer, demande de débit via `POST /api/collect/`, interrogation de statut via `GET /api/transaction/{reference}/`, et notification asynchrone par Webhook signé HMAC-SHA256.
4. **Idempotence & Anti-Rejeu** : Chaque transaction possède une référence unique attribuée par Pineapple (`reference = TX-FAC-2027-ENSPD-0001-XXXX`) et un identifiant unique Campay (`operator_reference`), garantissant l'enregistrement sans doublon dans `payment_events`.

---

## 3. Architecture Hexagonale des Paiements

Le port `PaymentProviderPort` dans `monetization_context/domain/ports.py` abstrait le fournisseur de paiement :

```
                        [ Monetization Use Cases ]
                                     |
                         [ PaymentProviderPort ]
                                  /  \
                                 /    \
            [ CampayProviderAdapter ]  [ FakePaymentProvider ]
                   (Production/Sandbox)        (Tests/Démo)
```

En développement et pour la suite de tests automatisés, `FakePaymentProvider` simule instantanément les paiements et les callbacks webhooks sans appel réseau. En environnement Sandbox/Production, `CampayProviderAdapter` gère les appels à l'API Campay.
