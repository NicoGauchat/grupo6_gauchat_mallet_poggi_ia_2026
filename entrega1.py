from simpleai.search import SearchProblem, astar

class RoverProblem(SearchProblem):
    def __init__(self, estado_inicial, zonas_sombra, max_bateria=20):
        
        super().__init__(estado_inicial)
        
        self.zonas_sombra = zonas_sombra
        self.max_bateria = max_bateria

        posicion_inicial = estado_inicial[0]
        igneas = estado_inicial[4]
        sedim = estado_inicial[5]

        todos_los_puntos = [posicion_inicial] + list(zonas_sombra) + list(igneas) + list(sedim)
        
        filas = [p[0] for p in todos_los_puntos]
        cols = [p[1] for p in todos_los_puntos]
        
        self.min_f, self.max_f = min(filas) - 2, max(filas) + 2
        self.min_c, self.max_c = min(cols) - 2, max(cols) + 2

    def actions(self, state):
        posicion, bateria, taladro, carga_actual, igneas_rest, sedim_rest = state
        acciones_validas = []

        if bateria > 1:
            if self.min_f <= posicion[0] + 1 <= self.max_f:
                acciones_validas.append(("moverse", (posicion[0] + 1, posicion[1])))
            if self.min_f <= posicion[0] - 1 <= self.max_f:
                acciones_validas.append(("moverse", (posicion[0] - 1, posicion[1])))
            if self.min_c <= posicion[1] + 1 <= self.max_c:
                acciones_validas.append(("moverse", (posicion[0], posicion[1] + 1)))
            if self.min_c <= posicion[1] - 1 <= self.max_c:
                acciones_validas.append(("moverse", (posicion[0], posicion[1] - 1)))

        if bateria > 4:
            if self.min_f <= posicion[0] + 2 <= self.max_f:
                acciones_validas.append(("sobremarcha", (posicion[0] + 2, posicion[1])))
            if self.min_f <= posicion[0] - 2 <= self.max_f:
                acciones_validas.append(("sobremarcha", (posicion[0] - 2, posicion[1])))
            if self.min_c <= posicion[1] + 2 <= self.max_c:
                acciones_validas.append(("sobremarcha", (posicion[0], posicion[1] + 2)))
            if self.min_c <= posicion[1] - 2 <= self.max_c:
                acciones_validas.append(("sobremarcha", (posicion[0], posicion[1] - 2)))

        if bateria > 1:
            if taladro != "termico":
                acciones_validas.append(("equipar", "termico"))
            if taladro != "percusion":
                acciones_validas.append(("equipar", "percusion"))

        if bateria > 1:
            if carga_actual == 2:
                acciones_validas.append(("depositar", None))
            elif carga_actual == 1 and len(igneas_rest) == 0 and len(sedim_rest) == 0:
                acciones_validas.append(("depositar", None))

        if bateria > 3 and carga_actual < 2:
            if posicion in igneas_rest and taladro == "termico":
                acciones_validas.append(("recolectar", "ignea"))
            if posicion in sedim_rest and taladro == "percusion":
                acciones_validas.append(("recolectar", "sedimentaria"))
                
        
        if posicion not in self.zonas_sombra and bateria < self.max_bateria:
            acciones_validas.append(("recargar", None))
            
        return acciones_validas

    def result(self, state, action):
        posicion, bateria, taladro, carga_actual, igneas_rest, sedim_rest = state
        tipo_accion, parametro = action 
        
        nueva_posicion = posicion
        nueva_bateria = bateria
        nuevo_taladro = taladro
        nueva_carga = carga_actual
        
        nuevas_igneas = set(igneas_rest) 
        nuevas_sedim = set(sedim_rest)
        
        if tipo_accion == "moverse":
            nueva_posicion = parametro
            nueva_bateria -= 1
            
        elif tipo_accion == "sobremarcha":
            nueva_posicion = parametro
            nueva_bateria -= 4
            
        elif tipo_accion == "equipar":
            nuevo_taladro = parametro
            nueva_bateria -= 1
            
        elif tipo_accion == "depositar":
            nueva_carga = 0
            nueva_bateria -= 1
            
        elif tipo_accion == "recolectar":
            nueva_carga += 1
            nueva_bateria -= 3
            if parametro == "ignea":
                nuevas_igneas.remove(nueva_posicion)
            elif parametro == "sedimentaria":
                nuevas_sedim.remove(nueva_posicion)
                
        elif tipo_accion == "recargar":
            nueva_bateria = min(self.max_bateria, bateria + 10)
            
        
        return (nueva_posicion, nueva_bateria, nuevo_taladro, nueva_carga, frozenset(nuevas_igneas), frozenset(nuevas_sedim))
    
    def is_goal(self, state):
        posicion, bateria, taladro, carga_actual, igneas_rest, sedim_rest = state
        if bateria > 0 and carga_actual == 0 and len(igneas_rest) == 0 and len(sedim_rest) == 0:
            return True
        return False
    
    def cost(self, state, action, state2):
        tipo_accion, parametro = action
        
        if tipo_accion == "moverse":
            return 1
            
        elif tipo_accion == "sobremarcha":
            return 1
            
        elif tipo_accion == "equipar":
            return 3
            
        elif tipo_accion == "recolectar":
            return 2
            
        elif tipo_accion == "recargar":
            return 4
            
        elif tipo_accion == "depositar":
            posicion, bateria, taladro, carga_actual, igneas_rest, sedim_rest = state 
            if carga_actual == 2:
                return 2
            return 1
            
    def heuristic(self, state):
        posicion, bateria, taladro, carga_actual, igneas_rest, sedim_rest = state

        
        restantes = list(igneas_rest) + list(sedim_rest)

        if not restantes:
            return carga_actual

       
        dist_max = max(
            abs(posicion[0] - r[0]) + abs(posicion[1] - r[1])
            for r in restantes
        )
        viaje = (dist_max + 1) // 2

      
        recoleccion = 2 * len(restantes)

     
        deposito = carga_actual + len(restantes)

    
        equipamiento = 0
        hay_igneas = len(igneas_rest) > 0
        hay_sedim = len(sedim_rest) > 0

        if hay_igneas and hay_sedim:
            if taladro is None or taladro == "Ninguno":
                equipamiento = 6
            else:
                equipamiento = 3
        elif hay_igneas:
            if taladro != "termico":
                equipamiento = 3
        elif hay_sedim:
            if taladro != "percusion":
                equipamiento = 3

        return viaje + recoleccion + deposito + equipamiento
    
def planear_rover(rover_inicio, bateria_inicial, zonas_sombra, muestras_igneas, muestras_sedimentarias):

    estado_inicial = (
        rover_inicio, 
        bateria_inicial, 
        "Ninguno", 
        0, 
        frozenset(muestras_igneas), 
        frozenset(muestras_sedimentarias)
    )
    
    problema = RoverProblem(estado_inicial, zonas_sombra)
    
    resultado = astar(problema, graph_search=True)

    acciones = []
    for accion, estado in resultado.path():
        if accion is not None: 
            acciones.append(accion)
    return acciones