import math
from simpleai.search import SearchProblem, astar


class ProblemaRover(SearchProblem):
    def __init__(
        self,
        rover_inicio,
        bateria_inicial,
        zonas_sombra,
        muestras_igneas,
        muestras_sedimentarias,
    ):
        # Guardamos las zonas de sombra como tupla porque no cambian durante la búsqueda.
        self.zonas_sombra = tuple(zonas_sombra)

        # Armamos una lista con todas las posiciones relevantes.
        # Esto permite calcular un límite dinámico del mapa sin hardcodear 6x6, 5x5, etc.
        posiciones_relevantes = (
            [rover_inicio]
            + list(zonas_sombra)
            + list(muestras_igneas)
            + list(muestras_sedimentarias)
        )

        max_fila = 0
        max_columna = 0

        for fila, columna in posiciones_relevantes:
            if fila > max_fila:
                max_fila = fila
            if columna > max_columna:
                max_columna = columna

        # Dejamos un margen de 2 porque existe la acción sobremarcha.
        # No cambia el planteo, solo evita que el rover quede encerrado artificialmente
        # por un límite demasiado ajustado.
        self.max_fila = max_fila + 2
        self.max_columna = max_columna + 2

        # Estado:
        # (
        #   posicion,
        #   bateria,
        #   taladro_equipado,
        #   muestras_en_bodega,
        #   muestras_igneas_restantes,
        #   muestras_sedimentarias_restantes
        # )
        #
        # Usamos tuplas para que SimpleAI pueda comparar estados en búsqueda en grafo.
        estado_inicial = (
            rover_inicio,
            bateria_inicial,
            None,
            0,
            tuple(muestras_igneas),
            tuple(muestras_sedimentarias),
        )

        super().__init__(estado_inicial)

    def is_goal(self, state):
        posicion, bateria, taladro_equipado, muestras_en_bodega, muestras_igneas, muestras_sedimentarias = state

        # Meta: no quedan muestras en el mapa y la bodega está vacía.
        return (
            muestras_en_bodega == 0
            and len(muestras_igneas) == 0
            and len(muestras_sedimentarias) == 0
        )

    def _queda_muerto_en_sombra(self, posicion, bateria_despues):
        """
        Devuelve True si el rover queda con 1 de batería en una zona de sombra.

        En esa situación no puede recargar y cualquier acción que consuma batería
        lo llevaría a 0, cosa prohibida por la consigna.
        """
        return bateria_despues == 1 and posicion in self.zonas_sombra

    def actions(self, state):
        posicion, bateria, taladro_equipado, muestras_en_bodega, muestras_igneas, muestras_sedimentarias = state
        acciones = []

        fila_posicion, columna_posicion = posicion

        # ------------------------------------------------------------
        # Acción: moverse
        # Consume 1 batería, por eso se permite solo si después queda > 0.
        # ------------------------------------------------------------
        if bateria >= 2:
            acciones_moverse = []

            if fila_posicion - 1 >= 0:
                acciones_moverse.append(("moverse", (fila_posicion - 1, columna_posicion)))

            if fila_posicion + 1 <= self.max_fila:
                acciones_moverse.append(("moverse", (fila_posicion + 1, columna_posicion)))

            if columna_posicion - 1 >= 0:
                acciones_moverse.append(("moverse", (fila_posicion, columna_posicion - 1)))

            if columna_posicion + 1 <= self.max_columna:
                acciones_moverse.append(("moverse", (fila_posicion, columna_posicion + 1)))

            for accion in acciones_moverse:
                tipo_accion, posicion_final = accion
                bateria_despues = bateria - 1

                # Evitamos caer con batería 1 en una zona de sombra.
                if not self._queda_muerto_en_sombra(posicion_final, bateria_despues):
                    acciones.append(accion)

        # ------------------------------------------------------------
        # Acción: sobremarcha
        # Consume 4 batería y mueve exactamente 2 celdas en línea recta.
        # ------------------------------------------------------------
        if bateria >= 5:
            acciones_sobremarcha = []

            if fila_posicion - 2 >= 0:
                acciones_sobremarcha.append(("sobremarcha", (fila_posicion - 2, columna_posicion)))

            if fila_posicion + 2 <= self.max_fila:
                acciones_sobremarcha.append(("sobremarcha", (fila_posicion + 2, columna_posicion)))

            if columna_posicion - 2 >= 0:
                acciones_sobremarcha.append(("sobremarcha", (fila_posicion, columna_posicion - 2)))

            if columna_posicion + 2 <= self.max_columna:
                acciones_sobremarcha.append(("sobremarcha", (fila_posicion, columna_posicion + 2)))

            for accion in acciones_sobremarcha:
                tipo_accion, posicion_final = accion
                bateria_despues = bateria - 4

                # Misma idea que en moverse: no quedar con 1 de batería en sombra.
                if not self._queda_muerto_en_sombra(posicion_final, bateria_despues):
                    acciones.append(accion)

        # ------------------------------------------------------------
        # Acción: equipar
        # Consume 1 batería.
        # Se permite cambiar al otro taladro, o equipar uno si todavía no hay.
        # ------------------------------------------------------------
        if bateria >= 2:
            bateria_despues = bateria - 1

            # Como equipar no cambia la posición, revisamos si queda muerto en la posición actual.
            if not self._queda_muerto_en_sombra(posicion, bateria_despues):
                if taladro_equipado == "termico":
                    acciones.append(("equipar", "percusión"))

                if taladro_equipado == "percusión":
                    acciones.append(("equipar", "termico"))

                if taladro_equipado is None:
                    acciones.append(("equipar", "termico"))
                    acciones.append(("equipar", "percusión"))

        # ------------------------------------------------------------
        # Acción: recolectar
        # Consume 3 batería.
        # Requiere estar en una muestra, tener el taladro correcto y espacio en bodega.
        # ------------------------------------------------------------
        if bateria >= 4 and muestras_en_bodega < 2:
            bateria_despues = bateria - 3

            # Recolectar no cambia la posición, así que evitamos quedar muerto en sombra.
            if not self._queda_muerto_en_sombra(posicion, bateria_despues):
                if posicion in muestras_igneas and taladro_equipado == "termico":
                    acciones.append(("recolectar", "ignea"))

                if posicion in muestras_sedimentarias and taladro_equipado == "percusión":
                    acciones.append(("recolectar", "sedimentaria"))

        # ------------------------------------------------------------
        # Acción: depositar
        # Consume 1 batería.
        #
        # Regla:
        # - normalmente se deposita con 2 muestras,
        # - con 1 muestra solo si ya no quedan muestras en el mapa.
        # ------------------------------------------------------------
        if bateria >= 2 and muestras_en_bodega > 0:
            muestras_en_mapa = len(muestras_igneas) + len(muestras_sedimentarias)

            puede_depositar = (
                muestras_en_bodega == 2
                or (muestras_en_bodega == 1 and muestras_en_mapa == 0)
            )

            if puede_depositar:
                bateria_despues = bateria - 1

                # Si depositar termina el problema, lo permitimos aunque quede con 1 en sombra,
                # porque ya no necesita recargar ni moverse.
                deposito_termina_el_problema = muestras_en_mapa == 0

                if deposito_termina_el_problema or not self._queda_muerto_en_sombra(posicion, bateria_despues):
                    acciones.append(("depositar", None))

        # ------------------------------------------------------------
        # Acción: recargar
        # Solo se puede recargar fuera de zonas de sombra.
        # No la agregamos si la batería ya está llena para evitar ciclos inútiles.
        # ------------------------------------------------------------
        if posicion not in self.zonas_sombra and bateria < 20:
            acciones.append(("recargar", None))

        return tuple(acciones)

    def result(self, state, action):
        posicion, bateria, taladro_equipado, muestras_en_bodega, muestras_igneas, muestras_sedimentarias = state
        tipo_accion, parametro = action

        if tipo_accion == "moverse":
            posicion = parametro
            bateria -= 1

        elif tipo_accion == "sobremarcha":
            posicion = parametro
            bateria -= 4

        elif tipo_accion == "equipar":
            taladro_equipado = parametro
            bateria -= 1

        elif tipo_accion == "recolectar":
            # Las muestras están en tuplas, entonces convertimos a lista para poder remover.
            if parametro == "ignea":
                muestras_igneas_lista = list(muestras_igneas)
                muestras_igneas_lista.remove(posicion)
                muestras_igneas = tuple(muestras_igneas_lista)

            elif parametro == "sedimentaria":
                muestras_sedimentarias_lista = list(muestras_sedimentarias)
                muestras_sedimentarias_lista.remove(posicion)
                muestras_sedimentarias = tuple(muestras_sedimentarias_lista)

            muestras_en_bodega += 1
            bateria -= 3

        elif tipo_accion == "depositar":
            muestras_en_bodega = 0
            bateria -= 1

        elif tipo_accion == "recargar":
            # Recargar restaura 10 unidades, sin superar el máximo de 20.
            bateria = min(20, bateria + 10)

        return (
            posicion,
            bateria,
            taladro_equipado,
            muestras_en_bodega,
            muestras_igneas,
            muestras_sedimentarias,
        )

    def cost(self, state1, action, state2):
        tipo_accion, parametro = action
        posicion, bateria, taladro_equipado, muestras_en_bodega, muestras_igneas, muestras_sedimentarias = state1

        if tipo_accion == "moverse" or tipo_accion == "sobremarcha":
            return 1

        if tipo_accion == "equipar":
            return 3

        if tipo_accion == "recolectar":
            return 2

        if tipo_accion == "depositar":
            # Depositar tarda 1 minuto por muestra entregada.
            # Por eso usamos la cantidad de muestras que había antes de depositar.
            return muestras_en_bodega

        if tipo_accion == "recargar":
            return 4

        return 0

    def heuristic(self, state):
        posicion, bateria, taladro_equipado, muestras_en_bodega, muestras_igneas, muestras_sedimentarias = state

        heuristica = 0
        estimado_bateria_gastada = 0

        cantidad_igneas = len(muestras_igneas)
        cantidad_sedimentarias = len(muestras_sedimentarias)
        cantidad_muestras_mapa = cantidad_igneas + cantidad_sedimentarias
        total_muestras_a_depositar = muestras_en_bodega + cantidad_muestras_mapa

        # ------------------------------------------------------------
        # 1. Distancia hacia la muestra más lejana.
        #
        # Usamos una estimación optimista: suponemos que podemos usar sobremarcha
        # para avanzar 2 celdas en 1 minuto.
        # ------------------------------------------------------------
        distancia_max = 0
        posicion_fila, posicion_columna = posicion

        for muestra in muestras_igneas:
            muestra_fila, muestra_columna = muestra
            distancia = abs(muestra_fila - posicion_fila) + abs(muestra_columna - posicion_columna)

            if distancia > distancia_max:
                distancia_max = distancia

        for muestra in muestras_sedimentarias:
            muestra_fila, muestra_columna = muestra
            distancia = abs(muestra_fila - posicion_fila) + abs(muestra_columna - posicion_columna)

            if distancia > distancia_max:
                distancia_max = distancia

        heuristica += math.ceil(distancia_max / 2)

        # Para batería usamos distancia_max como estimación conservadora del movimiento.
        # No usamos /2 porque la sobremarcha ahorra tiempo, pero no ahorra batería.
        estimado_bateria_gastada += distancia_max

        # ------------------------------------------------------------
        # 2. Tiempo y batería por cambios de taladro.
        #
        # Mantenemos tu idea:
        # si quedan muestras de un tipo y el taladro actual no sirve para ese tipo,
        # en algún momento habrá que equipar/cambiar taladro.
        # ------------------------------------------------------------
        if cantidad_igneas != 0 and taladro_equipado != "termico":
            heuristica += 3
            estimado_bateria_gastada += 1

        if cantidad_sedimentarias != 0 and taladro_equipado != "percusión":
            heuristica += 3
            estimado_bateria_gastada += 1

        # ------------------------------------------------------------
        # 3. Tiempo y batería por recolectar.
        #
        # Cada muestra restante en el mapa debe recolectarse:
        # - tarda 2 minutos,
        # - consume 3 de batería.
        # ------------------------------------------------------------
        heuristica += 2 * cantidad_muestras_mapa
        estimado_bateria_gastada += 3 * cantidad_muestras_mapa

        # ------------------------------------------------------------
        # 4. Tiempo por depositar.
        #
        # Depositar tarda 1 minuto por muestra entregada.
        # Por eso el tiempo mínimo de depósito es la cantidad total de muestras
        # que todavía deben terminar depositadas.
        # ------------------------------------------------------------
        heuristica += total_muestras_a_depositar

        # ------------------------------------------------------------
        # 5. Batería por depositar.
        #
        # Ajuste acordado:
        # depositar consume 1 batería por acción de depositar, no por muestra.
        # Como cada depósito puede llevar hasta 2 muestras, estimamos la cantidad
        # mínima de depósitos con ceil(total / 2).
        # ------------------------------------------------------------
        if total_muestras_a_depositar > 0:
            depositos_minimos = math.ceil(total_muestras_a_depositar / 2)
            estimado_bateria_gastada += depositos_minimos

        # ------------------------------------------------------------
        # 6. Recargas estimadas.
        #
        # Mantenemos tu idea: si con la batería actual no alcanzaría según esta
        # estimación, sumamos tiempo de recarga.
        #
        # Usamos floor como venías planteando, lo cual subestima antes que pasarse.
        # Cada recarga tarda 4 minutos y recupera 10 de batería.
        # ------------------------------------------------------------
        bateria_restante_estimada = bateria - estimado_bateria_gastada

        if bateria_restante_estimada < 1:
            recargas_estimadas = math.floor(abs(bateria_restante_estimada) / 10)
            heuristica += recargas_estimadas * 4

        return heuristica


def planear_rover(
    rover_inicio,
    bateria_inicial,
    zonas_sombra,
    muestras_igneas,
    muestras_sedimentarias,
):
    """
    Función pedida por la consigna.

    Recibe los datos del problema, ejecuta A* y devuelve solamente la lista
    de acciones, en el formato:
    (str_tipo_accion, parametro_opcional)
    """
    problema = ProblemaRover(
        rover_inicio,
        bateria_inicial,
        zonas_sombra,
        muestras_igneas,
        muestras_sedimentarias,
    )

    resultado = astar(problema, graph_search=True)

    # resultado.path() devuelve pares (accion, estado).
    # El primer par tiene accion None porque representa el estado inicial.
    acciones = []

    for accion, estado in resultado.path():
        if accion is not None:
            acciones.append(accion)

    return acciones