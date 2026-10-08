# Incident Response Runbook & Operations Guide (Pineapple OS)

**Document Ref:** `RUNBOOK.md`  
**Escalation Tier:** SRE / DevOps / Lead Backend Engineer  

---

## 1. Fiches Réflexes par Incident

### Incident A : Panne ou plantage du Backend FastAPI (HTTP 502 Bad Gateway)
1. **Symptôme** : Alerte Uptime / NGINX retourne la page `maintenance.html`.
2. **Action immédiate** :
   ```bash
   # Inspecter les logs du conteneur backend
   docker compose -f docker-compose.prod.yml logs --tail=100 backend
   
   # Redémarrer le service backend
   docker compose -f docker-compose.prod.yml restart backend
   ```

### Incident B : Perte de la base de données PostgreSQL
1. **Symptôme** : Erreurs 500 en chaîne avec `asyncpg.exceptions.ConnectionDoesNotExistError`.
2. **Action immédiate** :
   ```bash
   # 1. Vérifier l'état de PostgreSQL
   docker compose -f docker-compose.prod.yml ps db
   
   # 2. Restaurer la dernière sauvegarde chiffrée
   ./scripts/restore.sh /backups/dump_pineapple_prod_latest.sql.enc
   ```

### Incident C : Panne du service Redis (Coupure de Cache / Rate Limiter)
1. **Symptôme** : Log `REDIS_UNAVAILABLE_FAIL_CLOSED` sur les endpoints sensibles (Login, Paiement).
2. **Comportement attendu (Gate O-4)** : Échec fermé immédiat sur les endpoints sensibles (HTTP 503) pour éviter les attaques bruteforce sans rate limiter.
3. **Action immédiate** :
   ```bash
   docker compose -f docker-compose.prod.yml restart redis
   ```

### Incident D : Révocation de jetons en masse (Compromission de clé JWT)
1. **Action immédiate** :
   ```bash
   # 1. Modifier JWT_SECRET_KEY dans .env.production
   # 2. Exécuter la rotation des jetons et le redémarrage backend
   make prod-up
   ```
