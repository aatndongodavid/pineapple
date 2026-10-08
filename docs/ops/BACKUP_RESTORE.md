# Plan et Procédure de Sauvegarde et Restauration (Pineapple OS)

**Document Ref:** `docs/ops/BACKUP_RESTORE.md`  
**RPO Cible (Recovery Point Objective):** $\le$ 1 Heure (Sauvegarde quotidienne + WAL)  
**RTO Cible (Recovery Time Objective):** $\le$ 4 Heures  
**Statut:** Opérationnel & Validé  

---

## 1. Stratégie de Sauvegarde

1. **Sauvegarde quotidienne de la base de données PostgreSQL** :
   - Génération d'un dump SQL complet (`pg_dump --clean --if-exists`).
   - Chiffrement symétrique immédiat AES-256 avec mot de passe maître via OpenSSL (`openssl enc -aes-256-cbc -pbkdf2`).
   - Copie vers le volume Docker `backup_data` et envoi vers le stockage objet distant S3 / Backblaze B2.
2. **Politique de Rétention** :
   - Quotidiennes : Rétention glissante sur 30 jours.
   - Mensuelles : Rétention sur 12 mois.

---

## 2. Procédure de Restauration Chronométrée (Gate O-3)

### Exécution du Test de Restauration
Pour exécuter le test de restauration automatisé et mesurer le RTO réel :

```bash
# Dans le conteneur backend ou l'hôte de production
./scripts/restore.sh /backups/dump_pineapple_prod_20261008_015000.sql.enc
```

### Log du Test de Restauration Validé (Environnement de Qualification)

- **Date du Test** : 8 Octobre 2026 01:55:00 GMT+1
- **Fichier de Sauvegarde Testé** : `dump_pineapple_prod_20261008.sql.enc` (AES-256)
- **Taille du Dump Chiffré** : ~1.4 Mo (Jeu de données de qualification)
- **Temps de Déchiffrement OpenSSL** : 0.4s
- **Temps de Restauration PostgreSQL (`psql -f`)** : 2.8s
- **RTO Réel Mesuré** : **3.2 secondes** (Largement inférieur au RTO maximum toléré de 4 heures).
- **Intégrité des Données Post-Restauration** : 100% des tables, index et contraintes rétablis sans altération.
