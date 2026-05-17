from simpleai.search import SearchProblem, astar
import math


class ProblemaRover(SearchProblem):

    def __init__(self, rover_inicio, bateria_inicial, zonas_sombra, muestras_igneas, muestras_sedimentarias):

        self.zonas_sombra = tuple(zonas_sombra)

        max_fila = 0
        max_columna = 0
        for muestra in muestras_igneas:
            fila_muestra_ignea, columna_muestra_ignea = muestra
            if fila_muestra_ignea > max_fila:
                max_fila = fila_muestra_ignea
            if columna_muestra_ignea > max_columna:
                max_columna = columna_muestra_ignea
        
        for muestra in muestras_sedimentarias:
            fila_muestra_sedimentaria, columna_muestra_sedimentaria = muestras_sedimentarias
            if fila_muestra_sedimentaria > max_fila:
                max_fila = fila_muestra_sedimentaria
            if columna_muestra_sedimentaria > max_columna:
                max_columna = columna_muestra_sedimentaria

        self.max_fila = max_fila
        self.max_columna = max_columna

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
        
        if muestras_en_bodega == 0 and muestras_igneas.len == 0 and muestras_sedimentarias.len == 0:
            return True
        
        return False
    
    def actions(self, state):
        posicion, bateria, taladro_equipado, muestras_en_bodega, muestras_igneas, muestras_sedimentarias = state
        acciones = []

        fila_posicion, columna_posicion = posicion

        if bateria >= 2:

            #moverse
            acciones_moverse = []

            if fila_posicion - 1 >= 0:
                acciones_moverse.append((("moverse"), (fila_posicion - 1, columna_posicion)))
            if fila_posicion + 1 <= self.max_fila:
                acciones_moverse.append((("moverse"), (fila_posicion + 1, columna_posicion)))
            if columna_posicion - 1 >= 0:
                acciones_moverse.append((("moverse"), (fila_posicion, columna_posicion - 1)))
            if columna_posicion + 1 <= self.max_columna:
                acciones_moverse.append((("moverse"), (fila_posicion, columna_posicion + 1))) 

            # Si queda con 1 de batería, evitás caer en sombra porque ahí no podría recargar
            if bateria == 2:
                for accion in acciones_moverse:
                    tipo_accion, posicion_final = accion
                    if posicion_final not in self.zonas_sombra:
                        acciones.append(accion)
            else:
                acciones.extend(acciones_moverse)

            if bateria != 2 and posicion not in self.zonas_sombra: # mejorar condicion
                #equipar
                if taladro_equipado == "termico":
                    acciones.append(("equipar", ("percusión")))
                if taladro_equipado == "percusión":
                    acciones.append((("equipar"), ("termico")))
                if taladro_equipado == None:
                    acciones.append((("equipar"), ("termico")))
                    acciones.append(("equipar", ("percusión")))

                #depositar una capsula
                if muestras_en_bodega == 1 and muestras_igneas.len == 0 and muestras_sedimentarias.len == 0:
                    acciones.append((("depositar"), None))

        if bateria >= 5:
            acciones_sobremarcha = []

            if fila_posicion - 2 >= 0:
                acciones_sobremarcha.append((("sobremarcha"), (fila_posicion - 2, columna_posicion)))
            if fila_posicion + 2 <= self.max_fila:
                acciones_sobremarcha.append((("sobremarcha"), (fila_posicion + 2, columna_posicion)))
            if columna_posicion - 2 >= 0:
                acciones_sobremarcha.append((("sobremarcha"), (fila_posicion, columna_posicion - 2)))
            if columna_posicion + 2 <= self.max_columna:
                acciones_sobremarcha.append((("sobremarcha"), (fila_posicion, columna_posicion + 2))) 

            if bateria == 5:
                for accion in acciones_sobremarcha:
                    tipo_accion, posicion_final = accion
                    if posicion_final not in self.zonas_sombra:
                        acciones.append(accion)
            else:
                acciones.extend(acciones_sobremarcha)

        if bateria >= 4 and muestras_en_bodega < 2:
            if posicion in muestras_igneas and taladro_equipado == "termico":
                acciones.append((("recolectar"), ("ignea")))
            if posicion in muestras_sedimentarias and taladro_equipado == "percusión":
                acciones.append((("recolectar"), ("sedimentaria")))

        if bateria >= 3:
            #depositar capsulas
            if muestras_en_bodega == 2:
                acciones.append((("depositar"), None))

        #recargar
        if posicion not in self.zonas_sombra:
            acciones.append((("recargar"), None))

        return tuple(acciones)

    
    def result(self, state, action):
        estado_final = list(state)
        posicion, bateria, taladro_equipado, muestras_en_bodega, muestras_igneas, muestras_sedimentarias = estado_final
        tipo_accion, parametro = action

        if tipo_accion == "moverse":
            posicion = parametro
            bateria -= 1

        if tipo_accion == "sobremarcha":
            posicion = parametro
            bateria -= 4
        
        if tipo_accion == "equipar":
            taladro_equipado = parametro
            bateria -= 1
        
        if tipo_accion == "recolectar":
            if taladro_equipado == "termico":
                muestras_igneas.remove(posicion)
            else:
                muestras_sedimentarias.remove(posicion)
            muestras_en_bodega += 1
            bateria -= 3
        
        if tipo_accion == "depositar":
            muestras_en_bodega = 0
            bateria -= 1
        
        if tipo_accion == "recargar":
            if bateria + 10 > 20:
                bateria = 20
            else:
                bateria += 20

        return tuple(posicion, bateria, taladro_equipado, muestras_en_bodega, muestras_igneas, muestras_sedimentarias)


    def cost(self, state1, action, state2):
        tipo_accion, parametro = action
        posicion, bateria, taladro_equipado, muestras_en_bodega, muestras_igneas, muestras_sedimentarias = state1

        if tipo_accion == "moverse" or tipo_accion == "sobremarcha":
            tiempo = 1

        if tipo_accion == "equipar":
            tiempo = 3
        
        if tipo_accion == "recolectar":
            tiempo = 2
        
        if tipo_accion == "depositar":
            tiempo = muestras_en_bodega
        
        if tipo_accion == "recargar":
            tiempo = 4

        return tiempo


    def heuristic(self, state):
        posicion, bateria, taladro_equipado, muestras_en_bodega, muestras_igneas, muestras_sedimentarias = state
        heuristica = 0
        estimado_bateria_gastada = 0

        #distancia hacia la muestra mas lejana
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

        heuristica += distancia / 2 #dividido dos pq se puede usar sobremarcha
        estimado_bateria_gastada += distancia * 1 #cada movimiento de celda requiere 1 de bateria

        #tiempo que se tarda en cambiar el taladro
        if muestras_igneas.len != 0 and taladro_equipado != "termico":
            heuristica += 3
            estimado_bateria_gastada += 1
        if muestras_sedimentarias.len != 0 and taladro_equipado != "percusión":
            heuristica += 3
            estimado_bateria_gastada += 1


        #tardamos 2 minutos en extraer cada carga
        heuristica += 2 * (muestras_igneas.len + muestras_sedimentarias.len)
        estimado_bateria_gastada += 3 * (muestras_igneas.len + muestras_sedimentarias.len)

        #tiempo que se tarda en depositar
        heuristica += muestras_en_bodega + muestras_igneas.len + muestras_sedimentarias.len
        estimado_bateria_gastada += muestras_en_bodega + muestras_igneas.len + muestras_sedimentarias.len

        bateria_necesaria = bateria - estimado_bateria_gastada
        if bateria_necesaria < 1:
            #dividimos por 10, pq es cuanta bateria recargamos, por cuatro pq es el tiempo que gastamos
            heuristica += (math.floor(abs(bateria_necesaria) / 10)) * 4

