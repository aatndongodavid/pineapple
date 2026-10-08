# Architecture Document — AdTech Platform for Visitors

**Pineapple OS — Pacing, Delivery, Tracking & Wallet Engine**  
**Version**: 1.0  

---

## 1. High-Level Architecture

```
                                [Visitor HTTP Request GET /api/v1/ads/feed]
                                                    │
                                                    ▼
                             [Server-Side Membership Check]
                                                    │
                         ┌──────────────────────────┴──────────────────────────┐
                         ▼                                                     ▼
              (Has Active School Membership)                           (Is Visitor)
                         │                                                     │
                         ▼                                                     ▼
           [Return Empty Feed / Institutional Only]              [Ad Delivery Engine]
                                                                               │
                                                       ┌───────────────────────┴───────────────────────┐
                                                       ▼                                               ▼
                                            [Cache Lookup (Redis)]                       [DB Fallback Queries]
                                                       │
                                                       ▼
                                       [Targeting & Pacing Filter]
                                                       │
                                                       ▼
                                       [Frequency Cap & Prio Weighted]
                                                       │
                                                       ▼
                                       [Generate Signed Impression Token]
                                                       │
                                                       ▼
                                       [Return JSON Ad Cards to Visitor]
```

---

## 2. Wallet Engine & Transaction Journal
- **Prepaid Model**: Advertisers deposit funds in XAF integers via the `PaymentProvider` interface.
- **Immutable Journal**: `ad_wallets` table stores current `balance_xaf`. `wallet_transactions` records every deposit, delivery debit, refund, or adjustment.
- **Atomic Balance Updates**: Solde updates use atomic SQL expressions (`balance_xaf = balance_xaf - amount_xaf WHERE balance_xaf >= amount_xaf`). Balance can **never** become negative.

---

## 3. Pacing & Budget Control
- **Daily Budget Pacing**: `hourly_budget = daily_budget_xaf / 24`. The engine calculates the current hour's allowance. If spending in the current hour exceeds `hourly_budget`, campaign priority is temporarily lowered to spread expenditure evenly across 24 hours.
- **Auto-Stop at Zero Balance**: When campaign budget or wallet balance reaches 0 XAF, campaign status transitions to `PAUSED` or `ENDED` immediately.

---

## 4. Anti-Fraud & Tracking Protection
- **Signed Tokens**: Impression tokens are HMAC-SHA256 signed JWTs with a short TTL (15 minutes), single-use tracking, and bound session IDs.
- **IntersectionObserver**: Impression counts only trigger when element is >= 50% visible for >= 1 second.
- **Redirect Protection**: Clicks pass through `GET /api/v1/ads/click/{token}`. Target URLs are strictly validated against allowed protocols (`http://`, `https://`) and checked against an allowed host whitelist to prevent open redirect vulnerabilities.
