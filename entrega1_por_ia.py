from simpleai.search import SearchProblem, astar

MAX_BATERIA = 20
CAPACIDAD = 2

MOV_COST = 1
OVER_COST = 1
EQUIP_COST = 3
RECOLECTAR_COST = 2
RECARGAR_COST = 4

MOV_BAT = 1
OVER_BAT = 4
EQUIP_BAT = 1
RECOLECTAR_BAT = 3
DEPOSITAR_BAT = 1

TIPO_IGNEA = "ignea"
TIPO_SEDIMENTARIA = "sedimentaria"

TALADRO_TERMICO = "termico"
TALADRO_PERCUSION = "percusión"


def taladro_para_muestra(tipo):
    if tipo == TIPO_IGNEA:
        return TALADRO_TERMICO
    return TALADRO_PERCUSION


class RoverProblem(SearchProblem):

    def __init__(
        self,
        rover_inicio,
        bateria_inicial,
        zonas_sombra,
        muestras_igneas,
        muestras_sedimentarias,
    ):

        self.zonas_sombra = set(zonas_sombra)

        self.muestras = {}

        for pos in muestras_igneas:
            self.muestras[pos] = TIPO_IGNEA

        for pos in muestras_sedimentarias:
            self.muestras[pos] = TIPO_SEDIMENTARIA

        estado_inicial = (
            rover_inicio,          # posicion
            bateria_inicial,       # bateria
            None,                  # taladro
            tuple(),               # carga
            frozenset(),           # recolectadas
            frozenset(),           # depositadas
        )

        super().__init__(initial_state=estado_inicial)

    def is_goal(self, state):

        _, _, _, carga, _, depositadas = state

        return (
            len(depositadas) == len(self.muestras)
            and len(carga) == 0
        )

    def actions(self, state):

        pos, bateria, taladro, carga, recolectadas, _ = state

        acciones = []

        f, c = pos

        # movimientos normales
        for df, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:

            destino = (f + df, c + dc)

            if bateria - MOV_BAT > 0:
                acciones.append(("moverse", destino))

        # sobremarcha
        for df, dc in [(-2, 0), (2, 0), (0, -2), (0, 2)]:

            destino = (f + df, c + dc)

            if bateria - OVER_BAT > 0:
                acciones.append(("sobremarcha", destino))

        # equipar
        if bateria - EQUIP_BAT > 0:

            if taladro != TALADRO_TERMICO:
                acciones.append(("equipar", TALADRO_TERMICO))

            if taladro != TALADRO_PERCUSION:
                acciones.append(("equipar", TALADRO_PERCUSION))

        # recolectar
        if (
            pos in self.muestras
            and pos not in recolectadas
            and len(carga) < CAPACIDAD
        ):

            tipo = self.muestras[pos]

            if (
                taladro_para_muestra(tipo) == taladro
                and bateria - RECOLECTAR_BAT > 0
            ):
                acciones.append(("recolectar", tipo))

        # depositar
        if len(carga) > 0 and bateria - DEPOSITAR_BAT > 0:

            faltantes = len(self.muestras) - len(recolectadas)

            if len(carga) == 2 or faltantes == 0:
                acciones.append(("depositar", None))

        # recargar
        if (
            pos not in self.zonas_sombra
            and bateria < MAX_BATERIA
        ):
            acciones.append(("recargar", None))

        return acciones

    def result(self, state, action):

        pos, bateria, taladro, carga, recolectadas, depositadas = state

        carga = list(carga)
        recolectadas = set(recolectadas)
        depositadas = set(depositadas)

        tipo, parametro = action

        if tipo == "moverse":

            pos = parametro
            bateria -= MOV_BAT

        elif tipo == "sobremarcha":

            pos = parametro
            bateria -= OVER_BAT

        elif tipo == "equipar":

            taladro = parametro
            bateria -= EQUIP_BAT

        elif tipo == "recolectar":

            carga.append(pos)
            recolectadas.add(pos)
            bateria -= RECOLECTAR_BAT

        elif tipo == "depositar":

            for muestra in carga:
                depositadas.add(muestra)

            carga = []
            bateria -= DEPOSITAR_BAT

        elif tipo == "recargar":

            bateria = min(MAX_BATERIA, bateria + 10)

        return (
            pos,
            bateria,
            taladro,
            tuple(carga),
            frozenset(recolectadas),
            frozenset(depositadas),
        )

    def cost(self, state, action, state2):

        tipo, _ = action

        if tipo == "moverse":
            return MOV_COST

        if tipo == "sobremarcha":
            return OVER_COST

        if tipo == "equipar":
            return EQUIP_COST

        if tipo == "recolectar":
            return RECOLECTAR_COST

        if tipo == "depositar":
            return len(state[3])

        if tipo == "recargar":
            return RECARGAR_COST

        return 1

    def heuristic(self, state):

        pos, _, _, carga, recolectadas, _ = state

        restantes = [
            p for p in self.muestras
            if p not in recolectadas
        ]

        if not restantes and not carga:
            return 0

        pf, pc = pos

        dist_min = 0

        if restantes:
            dist_min = min(
                abs(rf - pf) + abs(rc - pc)
                for rf, rc in restantes
            )

        h = dist_min
        h += len(restantes) * 2

        if carga:
            h += 1

        return h


def reconstruir_acciones(resultado):

    acciones = []

    nodo = resultado

    while nodo.parent is not None:

        acciones.append(nodo.action)
        nodo = nodo.parent

    acciones.reverse()

    return acciones


def planear_rover(
    rover_inicio,
    bateria_inicial,
    zonas_sombra,
    muestras_igneas,
    muestras_sedimentarias,
):

    problema = RoverProblem(
        rover_inicio,
        bateria_inicial,
        zonas_sombra,
        muestras_igneas,
        muestras_sedimentarias,
    )

    resultado = astar(
        problema,
        graph_search=True,
    )

    if resultado is None:
        return []

    return reconstruir_acciones(resultado)