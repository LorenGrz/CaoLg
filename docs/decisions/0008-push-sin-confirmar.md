# 0008 — Commit y push a main sin confirmar (solo en este repo)

Fecha: 2026-11-09 · Estado: aceptada

## Contexto

El `AGENTS.md` de este repo dice: «Después de cada cambio: tests + `bash -n`, commit (Conventional Commits) y
push a `main` sin preguntar (pedido de Loren)». Es una instrucción explícita del usuario que reemplaza la regla
compartida del baseline de agents-config (#6: las acciones hacia afuera, como el push, piden confirmación previa).
El baseline (#7) exige registrar en un ADR del proyecto toda política que reemplaza una práctica base.

En la práctica el historial usa una rama por cambio y `merge --no-ff` a `main` (`Merge feat/...`), no commits
directos: la regla permite el push sin preguntar, no obliga a saltear la rama.

## Decisión

- Se mantiene la regla tal como la escribió Loren; no se cambia su texto.
- Alcance: solo este repo (caolg). No se extiende a otros repos, ni a organizaciones, ni a otros proyectos de Loren.
- Los workers de CAO nunca hacen push (está en todos los perfiles de `profiles/`); el permiso es del agente que
  edita este repo en sesión con Loren, no de los workers que lance el líder.
- Siguen valiendo el resto de las reglas: sin `git push --force`, sin secretos en el repo (es público) y tests +
  `bash -n` antes de commitear.

## Consecuencias

- Un push equivocado a `main` queda público de inmediato: la verificación antes del commit es la única red.
- Si el repo pasa a tener colaboradores o a usarse con una organización, esta decisión se revisa y se vuelve a
  pedir confirmación.
