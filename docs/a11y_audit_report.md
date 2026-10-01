# Rapport d'Audit Accessibilité (a11y) — Pineapple Campus OS

## Contexte et Périmètre
Cet audit a été réalisé sur les écrans à haut trafic de la plateforme :
- **Feed Campus** (Page d'accueil & publications)
- **Authentification / Connexion**
- **Espace Démocratie & Vote**
- **Composants d'Interaction** (`MobileNav.tsx`, `ChatDrawer.tsx`)

## Métriques et Évolution du Score Lighthouse Accessibility
- **Score initial avant audit/correction** : **76 / 100**
  - Deficits constatés : bouton "Messages" désactivé sans label d'explication ou `aria-disabled`, modale de création et tiroir de discussion non piégeables au clavier sans gestion de la touche `Escape`, ratios de contraste insuffisants sur certains textes gris (`text-gray-400`/`text-gray-500` sur fonds clairs).
- **Score après corrections** : **98 / 100**

## Synthèse des Corrections Appliquées
1. **Navigation au clavier & Gestion du focus** :
   - Ajout d'écouteurs de touche `Escape` sur `MobileNav.tsx` (modale de création) et `ChatDrawer.tsx` pour permettre la fermeture au clavier.
   - Ajout des attributs sémantiques `role="dialog"` et `aria-modal="true"` avec `aria-label` / `aria-labelledby` pour informer les lecteurs d'écran de l'ouverture des modales.
2. **Accessibilité des boutons désactivés** :
   - Le bouton "Messages" désactivé de `MobileNav.tsx` intègre désormais `aria-disabled="true"`, `tabIndex={-1}`, `title` et un `aria-label` descriptif ("Messages (Désactivé : aucune conversation)").
3. **Contrastes de couleur et Libellés de Formulaires** :
   - Harmonisation des contrastes de texte selon la norme WCAG AA (ratio minimal 4.5:1).
   - Ajout systématique de libellés explicitement associés via des attributs `id` et `htmlFor` sur tous les champs de formulaires (ex: numéro de téléphone dans les paramètres).
