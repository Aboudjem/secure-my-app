<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Aboudjem/secure-my-app/main/assets/hero-dark.svg">
    <img src="https://raw.githubusercontent.com/Aboudjem/secure-my-app/main/assets/hero-light.svg" alt="secure-my-app: descubre qué puede llevarse un desconocido de tu aplicación, después ciérralo y demuestra que está cerrado." width="100%">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/Aboudjem/secure-my-app/actions/workflows/validate.yml"><img src="https://github.com/Aboudjem/secure-my-app/actions/workflows/validate.yml/badge.svg" alt="validate"></a> <a href="https://github.com/Aboudjem/secure-my-app/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT license"></a>
</p>

<p align="center">
  <a href="../README.md">English</a> · <a href="zh-CN.md">简体中文</a> · <a href="ja.md">日本語</a> · <b>Español</b> · <a href="fr.md">Français</a>
  <br><sub>Esta traducción puede ir por detrás del original en inglés.<!-- may-lag --></sub>
</p>

<p align="center">
  <strong>Descubre qué puede llevarse un desconocido de tu aplicación. Después ciérralo y demuestra que está cerrado.</strong>
</p>

## Qué hace

- Lee toda tu aplicación, no un diff, y ejecuta 65 comprobaciones de seguridad con nombre propio.
- Solo informa de un agujero con el comando que lo demuestra y la salida que ese comando dio.
- Los cierra de uno en uno, solo después de que apruebes ese arreglo, y vuelve a probar cada cierre.

## Instalación

```bash
claude plugin marketplace add Aboudjem/10x
claude plugin install secure-my-app@10x       # Claude Code
npx skills add Aboudjem/secure-my-app         # Cursor, Codex, Copilot, Gemini CLI, 70+ others
```

## Qué obtienes

`.secure-my-app/report.md` empieza con una línea de veredicto y cada hallazgo lleva los mismos siete campos.

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

`PROOF` es un comando real y su salida real, con los secretos ocultos. `VERIFY` es el comando cuya salida
tiene que cambiar antes de dar algo por arreglado. `.secure-my-app/surface.json` convierte la segunda pasada en un diff.

## Qué revisa

65 controles en siete grupos, en el orden en que los prueba un atacante ([catálogo completo](https://github.com/Aboudjem/secure-my-app/blob/main/docs/controls.md)).

| Grupo | Cubre |
| --- | --- |
| KEYS (8) | Secretos en el repositorio, claves expuestas, alcance de las claves, rotación |
| DOOR (9) | Inicio de sesión, sesiones, cookies, almacenamiento de contraseñas, tokens |
| ROOMS (10) | Seguridad a nivel de fila, IDOR, aislamiento entre clientes, mass assignment |
| PIPES (13) | Inyección, XSS, CSRF, SSRF, CORS, redirecciones, webhooks, cabeceras |
| VAULT (8) | Cifrado en reposo, forma de las respuestas, fugas por errores, logs, copias |
| FLOOR (10) | Límites de peticiones, bots, subidas, manipulación de precios, funciones de IA |
| SUPPLY (7) | Dependencias, lockfiles, scripts de instalación, permisos de CI |

## Cómo funciona

- Nada se informa sin prueba. Lo que no puede resolver aquí vuelve como `UNPROVEN`, nunca como aprobado.
- Nada cambia en tu repositorio hasta que apruebas ese arreglo concreto. No hay modo por lotes.
- Cada arreglo se prueba dos veces: la petición del atacante ahora falla y tu propio inicio de sesión sigue
  funcionando. Un parche que devuelve `403` a todo el mundo cierra el agujero y cierra el producto.
- Nunca reescribe el historial de git ni rota una credencial. Escribe el procedimiento y tú lo ejecutas.

## Conviene saber

- Una pasada limpia no demuestra que tu aplicación sea segura. El tercer veredicto dice `NOTHING CONFIRMED
  HERE` y nunca se imprime sin sus recuentos de cobertura: nada llegó a CRITICAL ni a HIGH en lo que esta pasada pudo revisar.
- Es de solo lectura hasta que apruebas un arreglo. Con tu permiso explícito hace como mucho unas 30 peticiones
  inofensivas contra un único host que has confirmado que es tuyo. Sin `DELETE` y sin pruebas de carga.
- No es un test de intrusión y nadie lo firma. El resto está en [Límites honestos](https://github.com/Aboudjem/secure-my-app/blob/main/docs/limits.md).

## Más información

- [Inicio rápido](https://github.com/Aboudjem/secure-my-app/blob/main/docs/quickstart.md), una primera pasada de principio a fin
- [Un informe completo](https://github.com/Aboudjem/secure-my-app/blob/main/examples/sample-report.md), cuatro hallazgos y el apéndice de lo no resuelto
- [Límites honestos](https://github.com/Aboudjem/secure-my-app/blob/main/docs/limits.md), todo lo que secure-my-app no promete
- [Instalar en tu editor](https://github.com/Aboudjem/secure-my-app/blob/main/docs/editors.md) · [FAQ](https://github.com/Aboudjem/secure-my-app/blob/main/docs/faq.md) · [Contribuir](https://github.com/Aboudjem/secure-my-app/blob/main/CONTRIBUTING.md) · [El propio skill](https://github.com/Aboudjem/secure-my-app/blob/main/skills/secure-my-app/SKILL.md)

---

<sub>Creado por <a href="https://github.com/Aboudjem">Adam Boudjemaa</a> · MIT. Verificado en CI por 162 comprobaciones, 90 de <code>tests/test_manifests.py</code> y 72 de <code>evals/check_skill.py</code>.
Catálogo de controles, matriz de severidad y semántica de RLS rederivados de la documentación primaria de PostgreSQL, Supabase y OWASP, 2026. Hermano de <a href="https://github.com/Aboudjem/loopify">loopify</a> y <a href="https://github.com/Aboudjem/goalify">goalify</a>. <a href="https://github.com/Aboudjem/secure-my-app/issues">¿Ves algo que falta?</a></sub>

<sub>Traducción asistida por máquina y luego revisada. La versión de referencia es el <a href="../README.md">README.md</a> en inglés.</sub>
