<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Aboudjem/secure-my-app/main/assets/hero-dark.svg">
    <img src="https://raw.githubusercontent.com/Aboudjem/secure-my-app/main/assets/hero-light.svg" alt="secure-my-app : trouvez ce qu'un inconnu peut prendre dans votre application, puis refermez-le et prouvez que c'est refermé." width="100%">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/Aboudjem/secure-my-app/actions/workflows/validate.yml"><img src="https://github.com/Aboudjem/secure-my-app/actions/workflows/validate.yml/badge.svg" alt="validate"></a> <a href="https://github.com/Aboudjem/secure-my-app/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT license"></a>
</p>

<p align="center">
  <a href="../README.md">English</a> · <a href="zh-CN.md">简体中文</a> · <a href="ja.md">日本語</a> · <a href="es.md">Español</a> · <b>Français</b>
  <br><sub>Cette traduction peut avoir du retard sur l'original en anglais.<!-- may-lag --></sub>
</p>

<p align="center">
  <strong>Trouvez ce qu'un inconnu peut prendre dans votre application. Puis refermez-le et prouvez que c'est refermé.</strong>
</p>

## Ce que ça fait

- Lit toute votre application, pas un diff, et y applique 65 contrôles de sécurité nommés.
- Ne signale une faille qu'avec la commande qui la prouve et la sortie que cette commande a produite.
- Les referme une par une, seulement après votre accord, puis reprouve chaque fermeture.

## Installation

```bash
claude plugin marketplace add Aboudjem/10x
claude plugin install secure-my-app@10x       # Claude Code
npx skills add Aboudjem/secure-my-app         # Cursor, Codex, Copilot, Gemini CLI, 70+ others
```

## Ce que vous obtenez

`.secure-my-app/report.md` s'ouvre sur une ligne de verdict, puis chaque constat porte les mêmes sept champs.

```text
SECURE-MY-APP   gate: DO NOT LAUNCH
coverage 47 checked / 8 unproven / 4 n/a   [static + live: tidemark-preview.vercel.app]
findings: 2 critical  1 high  1 medium  0 low
CRITICAL  R1  Anyone can read every row of bookings
WHAT     Row level security is off on public.bookings, so the publishable key reads it all.
WHERE    supabase/migrations/0002_bookings.sql:11
PROOF    [executed] curl -s "$URL/rest/v1/bookings?select=*" -H "apikey: sb_publishable_7f2a..."
                    -> 200, 1204 rows: id, user_id, email, phone, address_line1, total_cents
IMPACT   Every customer's email, phone, address and what they paid, to anyone with devtools.
FIX      alter table public.bookings enable row level security;
         create policy "own" on public.bookings for select to authenticated
           using ((select auth.uid()) = user_id);
VERIFY   anon curl returns []; user A reads their own row; user B gets empty, not an error.
STATUS   OPEN
```

`PROOF` est une vraie commande et sa vraie sortie, expurgée. `VERIFY` est la commande dont la sortie doit
changer avant qu'une chose soit déclarée corrigée. `.secure-my-app/surface.json` fait du second passage un différentiel.

## Ce qu'il vérifie

65 contrôles en sept groupes, dans l'ordre où un attaquant les essaie ([catalogue complet](https://github.com/Aboudjem/secure-my-app/blob/main/docs/controls.md)).

| Groupe | Couvre |
| --- | --- |
| KEYS (8) | Secrets dans le dépôt, clés exposées, portée des clés, rotation |
| DOOR (9) | Connexion, sessions, cookies, stockage des mots de passe, jetons |
| ROOMS (10) | Sécurité au niveau des lignes, IDOR, isolation entre clients, mass assignment |
| PIPES (13) | Injection, XSS, CSRF, SSRF, CORS, redirections, webhooks, en-têtes |
| VAULT (8) | Chiffrement au repos, forme des réponses, fuites d'erreurs, logs, sauvegardes |
| FLOOR (10) | Limites de débit, bots, uploads, manipulation des prix, fonctions IA |
| SUPPLY (7) | Dépendances, lockfiles, scripts d'installation, permissions CI |

## Comment ça marche

- Rien n'est signalé sans preuve. Ce qui ne peut pas être tranché ici revient en `UNPROVEN`, jamais en réussite.
- Rien ne change dans votre dépôt tant que vous n'avez pas approuvé ce correctif précis. Pas de mode groupé.
- Chaque correctif est prouvé deux fois : la requête de l'attaquant échoue désormais, et votre propre connexion
  fonctionne toujours. Un patch qui renvoie `403` à tout le monde ferme la faille et ferme le produit.
- Il ne réécrit jamais l'historique git et ne fait jamais tourner une clé. Il écrit la marche à suivre, vous l'exécutez.

## Bon à savoir

- Un passage sans constat ne prouve pas que votre application est sûre. Le troisième verdict s'écrit
  `NOTHING CONFIRMED HERE`, jamais sans ses compteurs de couverture : rien n'est monté en CRITICAL ou HIGH dans ce que ce passage a pu vérifier.
- C'est en lecture seule tant que vous n'avez pas approuvé un correctif. Avec votre accord explicite, il envoie
  au plus une trentaine de requêtes inoffensives vers un hôte que vous avez confirmé posséder. Pas de `DELETE`.
- Ce n'est pas un test d'intrusion et personne ne le signe. Le reste est dans [Limites honnêtes](https://github.com/Aboudjem/secure-my-app/blob/main/docs/limits.md).

## Pour aller plus loin

- [Démarrage rapide](https://github.com/Aboudjem/secure-my-app/blob/main/docs/quickstart.md), un premier passage de bout en bout
- [Un rapport complet](https://github.com/Aboudjem/secure-my-app/blob/main/examples/sample-report.md), quatre constats et l'annexe des points non tranchés
- [Limites honnêtes](https://github.com/Aboudjem/secure-my-app/blob/main/docs/limits.md), tout ce que secure-my-app ne promet pas
- [Installer dans votre éditeur](https://github.com/Aboudjem/secure-my-app/blob/main/docs/editors.md) · [FAQ](https://github.com/Aboudjem/secure-my-app/blob/main/docs/faq.md) · [Contribuer](https://github.com/Aboudjem/secure-my-app/blob/main/CONTRIBUTING.md) · [Le skill lui-même](https://github.com/Aboudjem/secure-my-app/blob/main/skills/secure-my-app/SKILL.md)

---

<sub>Créé par <a href="https://github.com/Aboudjem">Adam Boudjemaa</a> · MIT. Vérifié en CI par 162 contrôles, 90 via <code>tests/test_manifests.py</code> et 72 via <code>evals/check_skill.py</code>.
Catalogue de contrôles, matrice de sévérité et sémantique RLS redérivés des documentations primaires PostgreSQL, Supabase et OWASP, 2026. Frère de <a href="https://github.com/Aboudjem/loopify">loopify</a> et de <a href="https://github.com/Aboudjem/goalify">goalify</a>. <a href="https://github.com/Aboudjem/secure-my-app/issues">Une lacune repérée ?</a></sub>

<sub>Traduction assistée par machine, puis relue. La version de référence est le <a href="../README.md">README.md</a> en anglais.</sub>
