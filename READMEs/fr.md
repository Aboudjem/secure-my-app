<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Aboudjem/lockpatch/main/assets/hero-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/Aboudjem/lockpatch/main/assets/hero-light.svg">
    <img src="https://raw.githubusercontent.com/Aboudjem/lockpatch/main/assets/hero-dark.svg" alt="lockpatch : trouvez ce qu'un inconnu peut prendre dans votre application, puis refermez-le et prouvez que c'est refermé." width="100%">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/Aboudjem/lockpatch/actions/workflows/validate.yml"><img src="https://github.com/Aboudjem/lockpatch/actions/workflows/validate.yml/badge.svg" alt="validate"></a>
  <a href="https://github.com/Aboudjem/lockpatch/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT license"></a>
  <a href="https://github.com/Aboudjem/lockpatch/stargazers"><img src="https://img.shields.io/github/stars/Aboudjem/lockpatch?color=2BE8C8&labelColor=0A0F1C" alt="stars"></a>
</p>

<p align="center">
  <a href="../README.md">English</a> · <a href="zh-CN.md">简体中文</a> · <a href="ja.md">日本語</a> · <a href="es.md">Español</a> · <b>Français</b>
</p>

<p align="center">
  <strong>Trouvez ce qu'un inconnu peut prendre dans votre application. Puis refermez-le et prouvez que c'est refermé.</strong>
</p>

<p align="center">
  <a href="#ce-que-ça-fait">Ce que ça fait</a> · <a href="#installation">Installation</a> · <a href="#utilisation">Utilisation</a> · <a href="#comment-ça-marche">Comment ça marche</a> · <a href="#dans-votre-éditeur">Dans votre éditeur</a> · <a href="https://github.com/Aboudjem/lockpatch/blob/main/docs/limits.md">Limites honnêtes</a> · <a href="#pour-aller-plus-loin">Pour aller plus loin</a>
</p>

<p align="center"><sub>Cette traduction peut avoir du retard sur l'original en anglais.<!-- may-lag --></sub></p>

```bash
claude plugin marketplace add Aboudjem/10x
claude plugin install lockpatch@10x        # Claude Code
npx skills add Aboudjem/lockpatch          # Cursor, Codex, Copilot, Gemini CLI, and 70+ others
```

## Ce que ça fait

Claude Code propose déjà `/security-review`, et cette commande fait bien son travail : elle lit un
diff et trouve la faille dans le code qui est là. Mais personne n'a oublié d'écrire la politique de
sécurité au niveau des lignes sur votre table `profiles` dans un diff que vous pourriez relire, parce
que l'absence de cette politique n'apparaît dans aucun diff. C'est la forme de ce que vous avez livré.
**`/security-review` trouve un bug dans du code que vous avez écrit. lockpatch trouve la défense que
vous n'avez jamais écrite.**

Il lit donc toute l'application au lieu d'un changement, exécute 65 contrôles nommés, et écrit deux
fichiers dans votre projet.

- **`.lockpatch/report.md`, le rapport.** Chaque constat comporte les mêmes sept champs dans le même
  ordre : quoi, où, preuve, impact, correctif, vérification, statut. `PROOF` est une commande réelle
  et sa sortie réelle, secrets caviardés. `VERIFY` est la commande dont la sortie doit changer avant
  que quoi que ce soit soit déclaré corrigé.
- **`.lockpatch/surface.json`, l'inventaire.** Vos routes, tables, politiques et constats sous forme
  de données, pour qu'une deuxième exécution dise « 3 corrigés, 1 régressé, 1 nouveau » au lieu de
  vous rendre un nouveau mur de texte.

<p align="center">
  <img src="https://raw.githubusercontent.com/Aboudjem/lockpatch/main/assets/hero.svg" alt="lockpatch en quatre étapes : cartographier la surface, exécuter les contrôles, gravir l'échelle jusqu'au constat, puis corriger et re-prouver." width="100%">
</p>

Tout repose sur une seule règle : **pas de preuve, pas de constat ; pas de nouvelle preuve, pas de
correctif.** Un constat que vous ne pouvez pas démontrer est une supposition, et une supposition
envoyée à quelqu'un qui vous fait confiance est pire que le silence.

## Installation

Les deux commandes Claude Code en haut ajoutent la marketplace 10x et installent le plugin. Tout
autre agent installe le même répertoire de skill en une ligne, via le
[CLI skills](https://github.com/vercel-labs/skills) :

```bash
npx skills add Aboudjem/lockpatch
```

Rien d'autre à installer : aucune dépendance, aucun serveur, aucun compte. Si `gitleaks`,
`trufflehog`, `semgrep` ou `osv-scanner` sont déjà sur votre machine, ils sont utilisés et l'en-tête
du rapport le dit ; sinon, les solutions de repli documentées sont exécutées et le rapport le dit
aussi.

## Utilisation

### 1. Pointez-le sur l'application

```text
/lockpatch
```

Il lit vos manifestes, affiche une fiche de stack tenant sur un écran, et pose exactement trois
questions, parce que ces trois-là changent ce qui sera exécuté ensuite et rien d'autre : l'application
est-elle en ligne et accessible à des inconnus en ce moment, le dépôt est-il public ou l'a-t-il déjà
été, et plusieurs clients partagent-ils cette base de données. Donner une URL est facultatif, et c'est
la plus grande différence entre un rapport solide et un rapport faible.

### 2. Lisez la ligne de verdict

```text
LOCKPATCH   gate: DO NOT LAUNCH
coverage 47 checked / 8 unproven / 4 n/a   [static + live: tidemark-preview.vercel.app]
scan: gitleaks yes, osv yes, semgrep no, trufflehog no
findings: 2 critical  1 high  1 medium  0 low
```

Puis il s'arrête et demande. Un rapport dont vous n'avez pas demandé qu'on agisse dessus est une
livraison complète.

### 3. Corrigez un constat à la fois

```text
fix R1
```

Chaque correctif est proposé avec son diff, approuvé par vous pour ce correctif précisément, appliqué
après un commit de sauvegarde, puis re-prouvé dans les deux sens. Il n'existe aucun mode groupé où
vous approuvez tout d'un coup, et aucun correctif n'est marqué clos à partir d'un diff seul.

## Comment ça marche

**L'échelle.** Chaque candidat gravit quatre barreaux avant de pouvoir devenir un constat, ce qui
empêche le rapport de devenir quarante lignes que personne ne lit.

```
Rung 4  IMPACT    Name the asset in plain words
Rung 3  CONTROL   Show that nothing stops it, through the actual calling role
Rung 2  REACH     Show who can get there: unauthenticated, any account, another tenant
Rung 1  EXISTS    file:line
Rung 0  ABSTAIN   UNPROVEN, with the reason and the command that would settle it
```

Le barreau 0 est un résultat à part entière. Un constat faux mais affirmé est la pire chose que ce
skill puisse produire, parce qu'il envoie quelqu'un « réparer » une authentification qui fonctionne, à
minuit, la veille d'un lancement.

**Trois issues, jamais deux.** Chaque contrôle se termine par `PASS`, `FAIL`, `UNPROVEN` ou `N/A`. Un
grep vide n'est pas la preuve qu'un contrôle existe, il ne devient donc jamais un `PASS`.

**Les preuves ont des niveaux, et chaque ligne de preuve est étiquetée.** `static` a été lu dans le
dépôt. `executed` a été exécuté ici et voici sa sortie. `recipe` est une commande écrite pour vous,
que personne n'a lancée, et c'est pourquoi elle ne peut jamais soutenir un `PASS` ni clore un constat.

**Le test apparié.** Chaque correctif est prouvé deux fois, dans des directions opposées. C'est la
règle que la plupart des outils de sécurité sautent.

```
Before   attacker's request succeeds      legitimate user's request succeeds
Fix      the control is added
After    attacker's request FAILS         legitimate user's request STILL SUCCEEDS
```

Un patch qui renvoie `403` à tout le monde ferme la faille et ferme le produit. Et « échoue » veut
dire refusé, précisément : un timeout, une 500 ou un résultat vide parce que la ligne de test
n'existait pas ressemblent à un échec et ne prouvent rien.

**Le verdict, toujours avec sa couverture.** Il n'y a pas de note sur 100, parce qu'un nombre invite à
dire « on est passé de 62 à 78 », et parce que toute somme pondérée se truque en ajoutant des
contrôles qui passent. Ce qui est livré, c'est un décompte et trois libellés calculés par règle,
et aucun libellé n'est jamais affiché sans ses compteurs de couverture sur la même ligne :

```text
GATE: NOTHING CONFIRMED HERE   coverage 41 checked / 9 unproven / 6 n/a   [static only, no live probes]
```

Ces compteurs ne sont pas décoratifs. Sans eux, une exécution approfondie et une exécution qui n'a
presque rien pu vérifier affichent le même libellé. Et le troisième libellé est délibérément la
formule `NOTHING CONFIRMED HERE`, ni « sécurisé » ni « réussi », parce que tout ce qu'il affirme,
c'est que rien n'est monté en CRITICAL ou HIGH parmi ce que cette exécution a pu vérifier.

<p align="center">
  <img src="https://raw.githubusercontent.com/Aboudjem/lockpatch/main/assets/how-it-works.svg" alt="Le pipeline lockpatch : cadrage, cartographie de la surface, contrôles, sondes en direct, rapport, puis correction sur approbation." width="100%">
</p>

## Ce qui est vérifié

65 contrôles en sept groupes, ordonnés selon ce qu'un attaquant essaie en premier. Le catalogue
complet, avec une commande `DETECT` et une commande `VERIFY` par contrôle, est dans
[skills/lockpatch/references/controls.md](https://github.com/Aboudjem/lockpatch/blob/main/skills/lockpatch/references/controls.md) ;
l'index lisible est [docs/controls.md](https://github.com/Aboudjem/lockpatch/blob/main/docs/controls.md).

| Groupe | Couvre | Pourquoi il est là |
| --- | --- | --- |
| **KEYS** (8) | Secrets, exposition et portée des clés, rotation | En premier, parce que si une clé a fuité les dégâts sont peut-être déjà faits et le chronomètre tourne |
| **DOOR** (9) | Authentification | Sessions, cookies, stockage des mots de passe, jetons, limitation du login |
| **ROOMS** (10) | Autorisation | Sécurité au niveau des lignes, IDOR, isolation des locataires, affectation de masse, champs privilégiés |
| **PIPES** (12) | La frontière et le fil | Injection, XSS, CSRF, SSRF, CORS, redirections, webhooks, en-têtes, HTTPS |
| **VAULT** (8) | Données au repos, et données qui sortent | Chiffrement, forme des réponses, fuites par erreur, journaux, sauvegardes, exports |
| **FLOOR** (10) | Abus et logique métier | Limites de débit, bots, uploads, falsification de prix, machines à états, fonctions IA |
| **SUPPLY** (7) | Ce sur quoi vous construisez | Dépendances, lockfiles, scripts d'installation, permissions CI, environnements de préversion |

ROOMS est le groupe où vivent les brèches coûteuses et celui où le code écrit par un agent est le plus
faible, parce qu'un contrôle d'autorisation manquant ressemble exactement à du code qui marche dans
tous les tests qu'un développeur écrit pour lui-même.

## Dans votre éditeur

Fonctionne dans Claude Code, Cursor, Codex, Copilot, Gemini CLI, et plus de 70 autres agents via
`npx skills add`.

| Où | Comment |
| --- | --- |
| Claude Code | `claude plugin install lockpatch@10x` |
| Cursor, Codex, Gemini CLI, OpenCode, Windsurf, Zed, Continue.dev | `npx skills add Aboudjem/lockpatch -a <agent>` |
| VS Code et GitHub Copilot | `npx skills add Aboudjem/lockpatch -a github-copilot` |
| Tout le reste | copiez `skills/lockpatch/` dans le répertoire de skills de votre agent |

Le skill est du Markdown, il voyage donc. Ce qui change d'un harnais à l'autre, c'est l'outillage
en dessous, et lockpatch se dégrade honnêtement plutôt que silencieusement : un agent sans shell ne
peut pas exécuter les commandes `DETECT`, ces contrôles reviennent donc en `UNPROVEN` avec la commande
écrite pour vous, et un agent sans réseau met `static only` dans l'en-tête du rapport. Ce sont deux
exécutions utiles. Aucune n'a le droit d'annoncer un `PASS` qu'elle n'a pas mérité. Le code `-a` par
agent est dans [docs/editors.md](https://github.com/Aboudjem/lockpatch/blob/main/docs/editors.md).

## Bon à savoir

> [!IMPORTANT]
> Une exécution propre ne veut pas dire que votre application est sûre. Le troisième libellé de
> verdict est la formule `NOTHING CONFIRMED HERE`, pas « sécurisé » ni « réussi », parce que tout ce
> qu'elle dit c'est que dans les contrôles que cette exécution a pu réellement vérifier, rien n'est
> monté en CRITICAL ou HIGH. Lisez les compteurs de couverture sur la même ligne, puis lisez
> [Limites honnêtes](https://github.com/Aboudjem/lockpatch/blob/main/docs/limits.md) avant de dire à
> qui que ce soit que l'application est passée.

- **Lecture seule tant que vous n'approuvez pas un correctif.** Les phases 0 à 4 lisent des fichiers,
  exécutent des commandes et, avec votre accord explicite, envoient au plus une trentaine de requêtes
  bénignes vers un seul hôte dont vous avez confirmé être propriétaire. Aucun `DELETE`, aucune requête
  qui modifie des données, aucun test de charge.
- **Il ne fait jamais tourner une clé et ne réécrit jamais l'historique git.** Il écrit le runbook de
  rotation et c'est vous qui l'exécutez. Faites la rotation d'abord, le nettoyage de l'historique
  ensuite, parce qu'une clé restée publique cinq minutes est compromise pour toujours.
- **Aucune valeur de secret n'atteint le rapport.** Tout est caviardé au préfixe du fournisseur plus
  quatre caractères, comme `sk_live_51Nq...`.
- **Ce n'est ni un test d'intrusion ni un audit de conformité.** Personne ne le signe. Faites faire une
  vraie évaluation si votre application traite des paiements, des données de santé, ou des
  identifiants vers les systèmes d'autres personnes.
- **La notation est déterministe, le scan ne l'est pas.** La découverte et la classification sont des
  jugements, donc deux exécutions peuvent trouver des choses différentes, et c'est pour cela que
  `surface.json` existe.

## Pour aller plus loin

- [Guide de démarrage](https://github.com/Aboudjem/lockpatch/blob/main/docs/quickstart.md), une
  première exécution de bout en bout, avec la sortie que vous voyez vraiment
- [Installer dans votre éditeur](https://github.com/Aboudjem/lockpatch/blob/main/docs/editors.md), le
  code `-a` et les deux chemins du CLI skills
- [Un rapport complet](https://github.com/Aboudjem/lockpatch/blob/main/examples/sample-report.md), un
  `.lockpatch/report.md` entier avec quatre constats, l'annexe des non prouvés et la section « ce qui
  n'a pas été vérifié, et pourquoi »
- [Limites honnêtes](https://github.com/Aboudjem/lockpatch/blob/main/docs/limits.md), tout ce que
  lockpatch ne promet pas, en détail
- [Le catalogue de contrôles](https://github.com/Aboudjem/lockpatch/blob/main/docs/controls.md), les
  65 contrôles en sept groupes
- [FAQ](https://github.com/Aboudjem/lockpatch/blob/main/docs/faq.md) · [Changelog](https://github.com/Aboudjem/lockpatch/blob/main/CHANGELOG.md) · [Contribuer](https://github.com/Aboudjem/lockpatch/blob/main/CONTRIBUTING.md) · [Politique de sécurité](https://github.com/Aboudjem/lockpatch/blob/main/SECURITY.md) · [Le skill lui-même](https://github.com/Aboudjem/lockpatch/blob/main/skills/lockpatch/SKILL.md)

Vérifié en CI par 162 contrôles : 90 via `python3 tests/test_manifests.py` et
72 via `python3 evals/check_skill.py skills/lockpatch/SKILL.md`.

---

<sub>Créé par <a href="https://github.com/Aboudjem">Adam Boudjemaa</a> · MIT. Catalogue de contrôles,
matrice de sévérité et sémantique RLS redérivés des documentations primaires PostgreSQL, Supabase et
OWASP, 2026. Frère de <a href="https://github.com/Aboudjem/loopify">loopify</a> et de
<a href="https://github.com/Aboudjem/goalify">goalify</a>.
<a href="https://github.com/Aboudjem/lockpatch/issues">Une lacune repérée ?</a></sub>

<sub>Traduction assistée par machine, puis relue. La version de référence est le <a href="../README.md">README.md</a> en anglais.</sub>
