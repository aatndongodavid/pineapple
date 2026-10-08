# Guide d'Édition du Contenu & Maintenance du Site Vitrine

---

## 1. Structure du Site (`website/`)

Le site vitrine est construit avec **Astro** et **TailwindCSS** pour garantir des performances d'affichage sub-seconde sur réseaux mobiles 2G/3G.

- **`pricing.config.json`** : Contient l'ensemble des formules d'abonnement en FCFA (XAF). Les montants doivent impérativement être des entiers XAF ou "Sur devis".
- **`site.config.json`** : Configuration globale du site (nom, numéros WhatsApp, email de contact, et le drapeau **`enableSocialProof`**).
- **`src/pages/fr/`** : Pages en version française (`/fr/`, `/fr/fonctionnalites/`, `/fr/securite/`, `/fr/tarifs/`, `/fr/demo/`, `/fr/etudiants/`, `/fr/a-propos/`, `/fr/faq/`, `/fr/mentions-legales/`, `/fr/blog/`).
- **`src/pages/en/`** : Pages en version anglaise avec la même structure et balises `hreflang` réciproques.

---

## 2. Règle Stricte V3 : Gestion des Preuves Sociales (`ENABLE_SOCIAL_PROOF`)

**Principe absolu (Règle V3) :** Interdiction totale d'afficher de faux témoignages, de faux logos ou de fausses statistiques.

- Par défaut, dans `site.config.json`, la clé est configurée sur :
  ```json
  "enableSocialProof": false
  ```
- Tant que `enableSocialProof` est `false`, la section est totalement masquée en production.
- Lorsque vous aurez au moins 3 établissements abonnés ayant donné leur accord écrit pour figurer sur le site vitrine :
  1. Ajoutez leurs logos vérifiés dans `website/public/images/partners/`.
  2. Modifiez `site.config.json` pour passer `"enableSocialProof": true`.
  3. Reconstruisez le site static avec `npm run build`.

---

## 3. Procédure de Publication & Déploiement Static

1. Naviguez dans le répertoire `website/` :
   ```bash
   cd website
   ```
2. Installez les dépendances si nécessaire :
   ```bash
   npm install
   ```
3. Exécutez le build de production static :
   ```bash
   npm run build
   ```
4. Les fichiers statiques générés se trouvent dans `website/dist/` et peuvent être déployés sur Nginx, Cloudflare Pages ou Netlify.
