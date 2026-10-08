# Guide de Déploiement en Production (Pineapple OS)

**Document Ref:** `DEPLOY.md`  
**Target Environment:** Single VPS (Hetzner / OVH EU) | Ubuntu 22.04 / 24.04 LTS  
**Prerequisites:** Docker, Docker Compose v2, Git, Domain Name & DNS records pointing to VPS IP  

---

## 1. Préparation et Sécurisation de l'Hôte

```bash
# 1. Mise à jour du système d'exploitation
sudo apt update && sudo apt upgrade -y

# 2. Sécurisation SSH (Clés SSH uniquement, interdire mot de passe)
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# 3. Configuration du pare-feu UFW (Pare-feu minimal 80/443 + SSH)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 2. Déploiement Initial From Scratch (Gate O-1)

```bash
# 1. Cloner le dépôt officiel sur la machine hôte
git clone https://github.com/aatndongodavid/pineapple.git /opt/pineapple
cd /opt/pineapple

# 2. Créer le fichier de variables d'environnement de production (.env)
cp .env.example .env.production

# Éditer .env.production avec les secrets sécurisés générés :
# JWT_SECRET_KEY=$(openssl rand -hex 32)
# ELECTION_PEPPER_SECRET=$(openssl rand -hex 16)
# POSTGRES_PASSWORD=$(openssl rand -hex 24)

# 3. Exécuter le garde-fou de sécurité 12-Factor (Gate O-10)
python3 -c "
from shared_kernel.config import settings
settings.validate_production_security()
"

# 4. Lancer le déploiement de production
./scripts/deploy.sh
```

---

## 3. Procédure de Retour Arrière en Une Commande (Gate O-2)

En cas d'anomalie détectée après une mise à jour :

```bash
# Exécuter le rollback automatique (Restauration DB -1 step + relance conteneurs)
make rollback
```
