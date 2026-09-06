<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Aboudjem/lockpatch/main/assets/hero-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/Aboudjem/lockpatch/main/assets/hero-light.svg">
    <img src="https://raw.githubusercontent.com/Aboudjem/lockpatch/main/assets/hero-dark.svg" alt="lockpatch: descubre qué puede llevarse un desconocido de tu aplicación, después ciérralo y demuestra que está cerrado." width="100%">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/Aboudjem/lockpatch/actions/workflows/validate.yml"><img src="https://github.com/Aboudjem/lockpatch/actions/workflows/validate.yml/badge.svg" alt="validate"></a>
  <a href="https://github.com/Aboudjem/lockpatch/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT license"></a>
  <a href="https://github.com/Aboudjem/lockpatch/stargazers"><img src="https://img.shields.io/github/stars/Aboudjem/lockpatch?color=2BE8C8&labelColor=0A0F1C" alt="stars"></a>
</p>

<p align="center">
  <a href="../README.md">English</a> · <a href="zh-CN.md">简体中文</a> · <a href="ja.md">日本語</a> · <b>Español</b> · <a href="fr.md">Français</a>
</p>

<p align="center">
  <strong>Descubre qué puede llevarse un desconocido de tu aplicación. Después ciérralo y demuestra que está cerrado.</strong>
</p>

<p align="center">
  <a href="#qué-hace">Qué hace</a> · <a href="#instalación">Instalación</a> · <a href="#cómo-se-usa">Cómo se usa</a> · <a href="#cómo-funciona">Cómo funciona</a> · <a href="#en-tu-editor">En tu editor</a> · <a href="https://github.com/Aboudjem/lockpatch/blob/main/docs/limits.md">Límites honestos</a> · <a href="#más-información">Más información</a>
</p>

<p align="center"><sub>Esta traducción puede ir por detrás del original en inglés.<!-- may-lag --></sub></p>

```bash
claude plugin marketplace add Aboudjem/10x
claude plugin install lockpatch@10x        # Claude Code
npx skills add Aboudjem/lockpatch          # Cursor, Codex, Copilot, Gemini CLI, and 70+ others
```

## Qué hace

Claude Code ya incluye `/security-review`, y hace bien su trabajo: lee un diff y encuentra el fallo
en el código que está ahí. Pero nadie se olvidó de escribir la política de seguridad a nivel de fila
sobre tu tabla `profiles` dentro de un diff que puedas revisar, porque la ausencia de esa política no
aparece en ningún diff. Es la forma de lo que has desplegado. **`/security-review` encuentra un error
en el código que escribiste. lockpatch encuentra la defensa que nunca escribiste.**

Así que lee la aplicación entera en lugar de un cambio, ejecuta 65 controles con nombre propio y
escribe dos archivos en tu proyecto.

- **`.lockpatch/report.md`, el informe.** Cada hallazgo tiene los mismos siete campos en el mismo
  orden: qué, dónde, prueba, impacto, arreglo, verificación, estado. `PROOF` es un comando real y su
  salida real, con los secretos censurados. `VERIFY` es el comando cuya salida tiene que cambiar antes
  de que nada se dé por arreglado.
- **`.lockpatch/surface.json`, el inventario.** Tus rutas, tablas, políticas y hallazgos como datos,
  para que una segunda ejecución diga «3 arreglados, 1 con regresión, 1 nuevo» en lugar de entregarte
  otro muro de texto.

<p align="center">
  <img src="https://raw.githubusercontent.com/Aboudjem/lockpatch/main/assets/hero.svg" alt="lockpatch en cuatro pasos: mapear la superficie, ejecutar los controles, subir la escalera hasta el hallazgo, y después arreglar y volver a demostrarlo." width="100%">
</p>

Todo se apoya en una sola regla: **sin prueba no hay hallazgo; sin nueva prueba no hay arreglo.** Un
hallazgo que no puedes demostrar es una suposición, y las suposiciones enviadas a alguien que confía
en ti son peores que el silencio.

## Instalación

Los dos comandos de Claude Code de arriba añaden el marketplace 10x e instalan el plugin. Cualquier
otro agente instala el mismo directorio de skill en una línea, mediante el
[CLI de skills](https://github.com/vercel-labs/skills):

```bash
npx skills add Aboudjem/lockpatch
```

Nada más que instalar: sin dependencias, sin servidor, sin cuenta. Si `gitleaks`, `trufflehog`,
`semgrep` u `osv-scanner` ya están en tu máquina, los usa y lo indica en la cabecera del informe; y si
no están, ejecuta las alternativas documentadas y también lo indica.

## Cómo se usa

### 1. Apúntalo a la aplicación

```text
/lockpatch
```

Lee tus manifiestos, imprime una ficha de stack que cabe en una pantalla y hace exactamente tres
preguntas, porque esas tres cambian lo que se ejecuta después y ninguna otra lo hace: ¿está la
aplicación en línea y al alcance de desconocidos ahora mismo?, ¿es público el repositorio o lo ha sido
alguna vez?, ¿comparte esta base de datos más de un cliente? Dar una URL es opcional, y es la mayor
diferencia entre un informe sólido y uno débil.

### 2. Lee la línea del veredicto

```text
LOCKPATCH   gate: DO NOT LAUNCH
coverage 47 checked / 8 unproven / 4 n/a   [static + live: tidemark-preview.vercel.app]
scan: gitleaks yes, osv yes, semgrep no, trufflehog no
findings: 2 critical  1 high  1 medium  0 low
```

Después se detiene y pregunta. Un informe sobre el que no pediste que se actuara es una entrega
completa.

### 3. Arregla un hallazgo cada vez

```text
fix R1
```

Cada arreglo se propone con su diff, lo apruebas tú para ese arreglo en concreto, se aplica tras un
commit de resguardo y después se vuelve a demostrar en las dos direcciones. No hay modo por lotes en
el que apruebes todo de golpe, y ningún arreglo se marca como cerrado a partir de un diff.

## Cómo funciona

**La escalera.** Cada candidato sube cuatro peldaños antes de poder aparecer como hallazgo, y eso es
lo que impide que el informe se convierta en cuarenta puntos que nadie lee.

```
Rung 4  IMPACT    Name the asset in plain words
Rung 3  CONTROL   Show that nothing stops it, through the actual calling role
Rung 2  REACH     Show who can get there: unauthenticated, any account, another tenant
Rung 1  EXISTS    file:line
Rung 0  ABSTAIN   UNPROVEN, with the reason and the command that would settle it
```

El peldaño 0 es un resultado de primera clase. Un hallazgo equivocado pero afirmado con seguridad es
lo peor que puede producir este skill, porque manda a alguien a «arreglar» un login que funciona, a
medianoche, la víspera de un lanzamiento.

**Tres resultados, nunca dos.** Cada control termina en `PASS`, `FAIL`, `UNPROVEN` o `N/A`. Un grep
vacío no es prueba de que un control exista, así que nunca se convierte en un `PASS`.

**La evidencia tiene niveles, y cada línea de prueba lleva su etiqueta.** `static` se leyó en el
repositorio. `executed` se ejecutó aquí y esta es su salida. `recipe` es un comando escrito para ti
que nadie ejecutó, y por eso nunca puede sostener un `PASS` ni cerrar un hallazgo.

**La prueba emparejada.** Cada arreglo se demuestra dos veces, en direcciones opuestas. Es la regla
que casi todas las herramientas de seguridad se saltan.

```
Before   attacker's request succeeds      legitimate user's request succeeds
Fix      the control is added
After    attacker's request FAILS         legitimate user's request STILL SUCCEEDS
```

Un parche que devuelve `403` a todo el mundo cierra el agujero y cierra el producto. Y «falla»
significa rechazado, en concreto: un timeout, un 500 o un resultado vacío porque la fila de prueba
nunca existió parecen un fallo y no demuestran nada.

**El veredicto, siempre con su cobertura.** No hay puntuación sobre 100, porque un número invita a
decir «hemos pasado de 62 a 78», y porque cualquier suma ponderada se manipula añadiendo controles que
pasan. Lo que se entrega es un recuento y tres etiquetas calculadas por regla, y ninguna etiqueta se
imprime jamás sin sus contadores de cobertura en la misma línea:

```text
GATE: NOTHING CONFIRMED HERE   coverage 41 checked / 9 unproven / 6 n/a   [static only, no live probes]
```

Los contadores no son decoración. Sin ellos, una ejecución a fondo y una que apenas pudo revisar nada
imprimen la misma etiqueta. Y la tercera etiqueta es deliberadamente la fórmula `NOTHING CONFIRMED
HERE`, no «segura» ni «aprobada», porque lo único que afirma es que nada llegó a CRITICAL ni a HIGH
dentro de lo que esta ejecución concreta pudo comprobar.

<p align="center">
  <img src="https://raw.githubusercontent.com/Aboudjem/lockpatch/main/assets/how-it-works.svg" alt="El proceso de lockpatch: alcance, mapa de la superficie, controles, sondas en vivo, informe y arreglo previa aprobación." width="100%">
</p>

## Qué comprueba

65 controles en siete grupos, ordenados por lo que un atacante prueba primero. El catálogo completo,
con un comando `DETECT` y otro `VERIFY` por control, está en
[skills/lockpatch/references/controls.md](https://github.com/Aboudjem/lockpatch/blob/main/skills/lockpatch/references/controls.md);
el índice legible es [docs/controls.md](https://github.com/Aboudjem/lockpatch/blob/main/docs/controls.md).

| Grupo | Cubre | Por qué está aquí |
| --- | --- | --- |
| **KEYS** (8) | Secretos, exposición y alcance de claves, rotación | Primero, porque si una clave se filtró el daño puede estar ya hecho y el reloj corre |
| **DOOR** (9) | Autenticación | Sesiones, cookies, almacenamiento de contraseñas, tokens, límites en el login |
| **ROOMS** (10) | Autorización | Seguridad a nivel de fila, IDOR, aislamiento entre inquilinos, asignación masiva, campos privilegiados |
| **PIPES** (12) | La frontera y el cable | Inyección, XSS, CSRF, SSRF, CORS, redirecciones, webhooks, cabeceras, HTTPS |
| **VAULT** (8) | Datos en reposo, y datos que salen | Cifrado, forma de las respuestas, fugas por error, registros, copias de seguridad, exportaciones |
| **FLOOR** (10) | Abuso y lógica de negocio | Límites de tasa, bots, subidas, manipulación de precios, máquinas de estado, funciones de IA |
| **SUPPLY** (7) | Sobre lo que construyes | Dependencias, lockfiles, scripts de instalación, permisos de CI, entornos de preview |

ROOMS es donde viven las brechas caras y donde el código escrito por un agente es más débil, porque
una comprobación de autorización que falta se parece exactamente a código que funciona en todas las
pruebas que un desarrollador escribe para sí mismo.

## En tu editor

Funciona en Claude Code, Cursor, Codex, Copilot, Gemini CLI y más de 70 agentes más mediante
`npx skills add`.

| Dónde | Cómo |
| --- | --- |
| Claude Code | `claude plugin install lockpatch@10x` |
| Cursor, Codex, Gemini CLI, OpenCode, Windsurf, Zed, Continue.dev | `npx skills add Aboudjem/lockpatch -a <agent>` |
| VS Code y GitHub Copilot | `npx skills add Aboudjem/lockpatch -a github-copilot` |
| Todo lo demás | copia `skills/lockpatch/` en el directorio de skills de tu agente |

El skill es Markdown, así que viaja. Lo que cambia entre entornos es la herramienta que hay debajo, y
lockpatch se degrada con honestidad en lugar de en silencio: un agente sin shell no puede ejecutar los
comandos `DETECT`, así que esos controles vuelven como `UNPROVEN` con el comando escrito para ti, y un
agente sin red pone `static only` en la cabecera del informe. Las dos siguen siendo ejecuciones
útiles. Ninguna tiene permiso para informar de un `PASS` que no se ganó. El código `-a` de cada agente
está en [docs/editors.md](https://github.com/Aboudjem/lockpatch/blob/main/docs/editors.md).

## Conviene saber

> [!IMPORTANT]
> Una ejecución limpia no significa que tu aplicación sea segura. La tercera etiqueta del veredicto es
> literalmente `NOTHING CONFIRMED HERE`, no «segura» ni «aprobada», porque lo único que dice es que en
> los controles que esta ejecución pudo comprobar de verdad nada llegó a CRITICAL ni a HIGH. Lee los
> contadores de cobertura de la misma línea y después lee
> [Límites honestos](https://github.com/Aboudjem/lockpatch/blob/main/docs/limits.md) antes de decirle a
> nadie que la aplicación ha pasado.

- **Es de solo lectura hasta que apruebas un arreglo.** Las fases 0 a 4 leen archivos, ejecutan
  comandos y, con tu sí explícito, hacen como mucho unas 30 peticiones benignas contra un único host
  del que has confirmado ser propietario. Ningún `DELETE`, ninguna petición que modifique datos,
  ninguna prueba de carga.
- **Nunca rota una credencial ni reescribe el historial de git.** Escribe el runbook de rotación y lo
  ejecutas tú. Rota primero y limpia el historial después, porque una clave que estuvo pública cinco
  minutos está comprometida para siempre.
- **Ningún valor secreto llega al informe.** Todo se censura al prefijo del proveedor más cuatro
  caracteres, como `sk_live_51Nq...`.
- **No es un test de intrusión ni una auditoría de cumplimiento.** Nadie lo firma. Contrata una
  evaluación real si tu aplicación maneja pagos, datos de salud o credenciales de los sistemas de
  otras personas.
- **La valoración es determinista, el escaneo no.** El descubrimiento y la clasificación son juicios,
  así que dos ejecuciones pueden encontrar cosas distintas, y por eso existe `surface.json`.

## Más información

- [Guía rápida](https://github.com/Aboudjem/lockpatch/blob/main/docs/quickstart.md), una primera
  ejecución de principio a fin, con la salida que realmente ves
- [Instalar en tu editor](https://github.com/Aboudjem/lockpatch/blob/main/docs/editors.md), el código
  `-a` y las dos rutas del CLI de skills
- [Un informe completo](https://github.com/Aboudjem/lockpatch/blob/main/examples/sample-report.md), un
  `.lockpatch/report.md` entero con cuatro hallazgos, el apéndice de no probados y la sección «lo que
  no se ha comprobado, y por qué»
- [Límites honestos](https://github.com/Aboudjem/lockpatch/blob/main/docs/limits.md), todo lo que
  lockpatch no promete, en detalle
- [El catálogo de controles](https://github.com/Aboudjem/lockpatch/blob/main/docs/controls.md), los 65
  controles en siete grupos
- [FAQ](https://github.com/Aboudjem/lockpatch/blob/main/docs/faq.md) · [Changelog](https://github.com/Aboudjem/lockpatch/blob/main/CHANGELOG.md) · [Contribuir](https://github.com/Aboudjem/lockpatch/blob/main/CONTRIBUTING.md) · [Política de seguridad](https://github.com/Aboudjem/lockpatch/blob/main/SECURITY.md) · [El skill en sí](https://github.com/Aboudjem/lockpatch/blob/main/skills/lockpatch/SKILL.md)

Verificado en CI por 162 comprobaciones: 90 de `python3 tests/test_manifests.py`
y 72 de `python3 evals/check_skill.py skills/lockpatch/SKILL.md`.

---

<sub>Creado por <a href="https://github.com/Aboudjem">Adam Boudjemaa</a> · MIT. Catálogo de controles,
matriz de severidad y semántica de RLS rederivados de la documentación primaria de PostgreSQL,
Supabase y OWASP, 2026. Hermano de <a href="https://github.com/Aboudjem/loopify">loopify</a> y de
<a href="https://github.com/Aboudjem/goalify">goalify</a>.
<a href="https://github.com/Aboudjem/lockpatch/issues">¿Has visto algo que falta?</a></sub>

<sub>Traducción asistida por máquina y después revisada. La versión de referencia es el <a href="../README.md">README.md</a> en inglés.</sub>
