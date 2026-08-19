# SISTEMA COMC

Montado el 18/08/2026. Todo vive en kobe (`/root/comc-data/`) y en el VPS
(`/root/.openclaw/workspace/comc/`). Nada depende de ninguna conversacion.

## Rutina

    parte                    cada manana: dinero, acciones, 3 bloques
    op compra COD PRECIO     al comprar (entra al inventario + foto del baremo)
    op venta COD PRECIO      al vender (sale del inventario + calcula neto)
    of add "Carta" VEND $    al ofertar
    of vendedores            antes de ofertar a alguien nuevo
    op seguimiento           tras vender: vendi barato?
    op revision              el baremo acierta? (necesita 25-30 operaciones)

Los lunes: revisar las cartas muertas, de mayor a menor capital atascado.

## Ficheros

    reglas.txt          los umbrales. Cambiar uno = cambiar el sistema
    inventario.txt      lo que tengo: coste, mi precio, fecha, nota
    punto-mira.txt      lo que vigilo
    operaciones.txt     historial de compras y ventas
    ofertas.txt         ofertas y ficha de vendedores
    ventas/             historial de ventas por carta, crece solo
    snapshots/          mediciones de liquidez cada noche

## Que corre solo

23:00 UTC (+0-90 min aleatorio): feed -> 98 jugadores en 4 deportes ->
fino de 25 candidatas + mis cartas -> acumulador de ventas.
03:00 resumen del dia USA. 04:00 inventario.

## Arbol de decision al comprar

1. El precio pedido pasa la puerta del margen?
       P1 <= (P2 - 0.01) x 0.95 / (1 + neto_min)
       SI  -> COMPRAR YA. No negociar.
       NO  -> paso 2
2. Hay un precio que la pase y este por encima del 80% del listado?
       SI  -> UNA oferta a ese precio
       NO  -> descartar
3. Rechazo = fin. Ni una segunda oferta al mismo vendedor en 30 dias.

P2 es el techo de venta REAL: si el primer escalon tiene varias copias
del mismo vendedor (ballena), tu techo es ese mismo precio, no el
siguiente distinto.

## Lecciones, con numeros

**L-A. La liquidez es la puerta; el gap es el premio.** Sin liquidez no
puedes salir, y peor: no controlas tu precio de salida, porque cualquiera
te subcotiza antes de que aparezca un comprador. Las 3 operaciones hechas
con metodo: +18.5%, +26.0%, +9.4%. Las 2 hechas sin mirar liquidez:
-54.8% y -69.8%.

**L-B. Muchas copias no es liquidez.** Broome #235 tenia 10 copias
listadas y 7 ventas en 4 meses. Las copias se acumulan porque nadie
las quiere.

**L-C. Ballena.** Si un vendedor tiene varias copias en el primer
escalon, no hay hueco: compres la que compres, no puedes vender por
encima. Mahomes Donruss #100 tenia 4 copias de cardswithrob a $0.88.

**L-D. Importar de eBay cuesta $0.50 fijos por carta, a tu cargo.**
Neto = (precio de lista - 0.50) x 0.95. Con cartas de $2-4 eso es el
25-60% del valor. Experimento Bryant y Castle: -86% y -89%. Solo
compensa importar por encima de $20.

**L-E. Las cartas con etiqueta de condicion (EX to NM) viven en otro
mercado.** Riley: 2 copias en EX-NM contra 25 en Raw. El 15/08 se
vendieron 4 Raw a $0.87 mientras la suya, a $0.73, no se movio. Un
descuento que persiste no es una ineficiencia: es demanda menor.

**L-F. El 5% se paga siempre; el 10% de retirada, una sola vez.** El
10% NO entra en el baremo (seria cobrarlo en cada vuelta). Solo se
informa en `op revision`.

**L-G. Lo que compone es el porcentaje, no los centimos.** Con el
bankroll desplegado, 49 cartas de $1 y 10 de $5 dan lo mismo; la
diferencia es que las baratas son 5 veces mas trabajo.

## Frenos contra mis propios errores

- Si el precio pedido ya da margen, el parte dice COMPRA YA. No negociar
  algo que ya sirve (Wemby 12/08: 6 ofertas a un precio que ya valia).
- `of add` no deja repetir oferta al mismo vendedor por la misma carta
  en 30 dias.
- El stop de tiempo solo salta si ademas se va en perdida.
- Las cartas con nota "hold" quedan exentas de stop y de muertas.

## Calendario

    1 nov    arranca la NBA. ET pasa a UTC-5: correr una hora el cron
    1 dic    revision de las 5 cartas en hold. Bryant y Castle se
             venden ese dia pase lo que pase
    ago-sep  desplegar en MLB (en temporada, eventos diarios)
    sep-ene  NFL (una jornada por semana, senal limpia)

## Pendiente

- Comprobar si la Flagg Chrome lleva etiqueta de condicion
- Lista de seguimiento diario MLB/NFL para medir reaccion a eventos
- Puerta de percentil con ventana de 30 dias (necesita mas historico)
- Cerrar PasswordAuthentication en el VPS y rotar 3 claves
L-018: las filas con cuenta atras ("Xd left", puja) en la rejilla
de COMC son cross-promo a subastas externas de eBay (ej.
Promotions/eBay_Auction/...), no inventario propio de COMC. El
muro (id="hp...") ya las excluye por diseno de regex - confirmado
con Flagg Topps #201 el 19/08: min=$5.00 real, no $0.99 de puja.
No hace falta tocar nada del scan.
