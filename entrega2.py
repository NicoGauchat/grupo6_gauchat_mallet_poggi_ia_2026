from simpleai.search import CspProblem, backtrack

def build_camp(camp_size, habs, generators, labs, deposits, airlocks, craters):
    filas, columnas = camp_size
    
    # 1. CREACIÓN DE VARIABLES 
    variables = []
    for i in range(generators): variables.append(f"gen_{i}")
    for i in range(labs): variables.append(f"lab_{i}")
    for i in range(deposits): variables.append(f"dep_{i}")
    for i in range(airlocks): variables.append(f"air_{i}")
    for i in range(habs): variables.append(f"hab_{i}") # Habitaciones al final
        
    # 2. CREACIÓN DE DOMINIOS 
    coordenadas_del_mapa = []
    for f in range(filas):
        for c in range(columnas):
            coordenadas_del_mapa.append((f, c))
            
    dominios = {}
    for var in variables:
        dominios[var] = coordenadas_del_mapa

    restricciones = []
    
    # R1: Sin superposición (En parejas para activar la poda inmediata)
    def restriccion_no_superposicion(variables, values):
        return values[0] != values[1]
    for i in range(len(variables)):
        for j in range(i + 1, len(variables)):
            restricciones.append(((variables[i], variables[j]), restriccion_no_superposicion))
    
    # R2: Cráteres intransitables
    def restriccion_crater(variables, values):
        return values[0] not in craters
    for var in variables:
        restricciones.append(((var,), restriccion_crater))
        
    # R3: Esclusas en el borde
    def restriccion_esclusa_borde(variables, values):
        f, c = values[0]
        return f == 0 or f == filas - 1 or c == 0 or c == columnas - 1
    for var in variables:
        if var.startswith("air"):
            restricciones.append(((var,), restriccion_esclusa_borde))
            
    # R4: Habitacionales al interior
    def restriccion_habitacional_interior(variables, values):
        f, c = values[0]
        return not (f == 0 or f == filas - 1 or c == 0 or c == columnas - 1)
    for var in variables:
        if var.startswith("hab"):
            restricciones.append(((var,), restriccion_habitacional_interior))
            
    # R6: Aislamiento entre generadores
    def restriccion_aislamiento_generadores(variables, values):
        f1, c1 = values[0]
        f2, c2 = values[1]
        return abs(f1 - f2) + abs(c1 - c2) != 1
    generadores = [v for v in variables if v.startswith("gen")]
    for i in range(len(generadores)):
        for j in range(i + 1, len(generadores)):
            restricciones.append(((generadores[i], generadores[j]), restriccion_aislamiento_generadores))
            
    # R5: Seguridad energética (Generador no adyacente a habitacional)
    habitaciones = [v for v in variables if v.startswith("hab")]
    for hab in habitaciones:
        for gen in generadores:
            restricciones.append(((hab, gen), restriccion_aislamiento_generadores))
            
    # R7: Cadena de suministro científico (Laboratorio adyacente a depósito)
    def restriccion_laboratorio_deposito(variables, values):
        pos_lab = values[0]
        pos_depositos = values[1:]
        return any(abs(pos_lab[0] - pos_dep[0]) + abs(pos_lab[1] - pos_dep[1]) == 1 for pos_dep in pos_depositos)
        
    laboratorios = [v for v in variables if v.startswith("lab")]
    depositos = [v for v in variables if v.startswith("dep")]
    for lab in laboratorios:
        ambito = tuple([lab] + depositos)
        restricciones.append((ambito, restriccion_laboratorio_deposito))
        
    # R8: Ruta de evacuación (Habitacional con celda adyacente libre)
    def restriccion_evacuacion(variables, values):
        pos_hab = values[0]
        pos_todos_los_demas = values[1:]
        f, c = pos_hab
        vecinos = [(f - 1, c), (f + 1, c), (f, c - 1), (f, c + 1)]
        for vf, vc in vecinos:
            if 0 <= vf < filas and 0 <= vc < columnas:
                if (vf, vc) not in craters and (vf, vc) not in pos_todos_los_demas:
                    return True
        return False
        
    for hab_actual in habitaciones:
        otras_variables = [v for v in variables if v != hab_actual]
        ambito = tuple([hab_actual] + otras_variables)
        restricciones.append((ambito, restriccion_evacuacion))

    # 4. RESOLUCIÓN DEL CSP
    problema = CspProblem(variables, dominios, restricciones)
    solucion = backtrack(problema)
    
    if solucion is None:
        return None
        
    resultado_final = []
    for var, pos in solucion.items():
        tipo = var.split("_")[0]
        f, c = pos
        resultado_final.append((tipo, f, c))
        
    return resultado_final