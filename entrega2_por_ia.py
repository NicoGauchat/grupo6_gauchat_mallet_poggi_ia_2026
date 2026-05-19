from simpleai.search import CspProblem, backtrack


def build_camp(camp_size, habs, generators, labs, deposits, airlocks, craters):
    """
    Parámetros:
    - camp_size: tupla (filas, columnas)
    - habs, generators, labs, deposits, airlocks: enteros con las cantidades de cada módulo.
    - craters: lista de tuplas (fila, columna) con celdas inaccesibles.

    Resultado:
    - Una lista de tuplas (tipo, fila, columna), donde tipo es "hab", "gen", "lab", "dep" o "air".
    - Si no existe ninguna distribución válida, retornar None.
    """

    rows, cols = camp_size
    if rows <= 0 or cols <= 0:
        return None
    if min(habs, generators, labs, deposits, airlocks) < 0:
        return None

    crater_set = {
        (r, c)
        for (r, c) in craters
        if 0 <= r < rows and 0 <= c < cols
    }

    def is_border(cell):
        r, c = cell
        return r == 0 or r == rows - 1 or c == 0 or c == cols - 1

    def orth_neighbors(cell):
        r, c = cell
        candidates = ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        return [(nr, nc) for (nr, nc) in candidates if 0 <= nr < rows and 0 <= nc < cols]

    def orth_adjacent(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

    def has_available_neighbor(cell):
        return any(nei not in crater_set for nei in orth_neighbors(cell))

    all_cells = [(r, c) for r in range(rows) for c in range(cols)]
    available_cells = sorted([cell for cell in all_cells if cell not in crater_set])
    border_cells = sorted([cell for cell in available_cells if is_border(cell)])
    interior_cells = sorted([cell for cell in available_cells if not is_border(cell)])

    air_vars = [f"air_{i}" for i in range(airlocks)]
    dep_vars = [f"dep_{i}" for i in range(deposits)]
    gen_vars = [f"gen_{i}" for i in range(generators)]
    lab_vars = [f"lab_{i}" for i in range(labs)]
    hab_vars = [f"hab_{i}" for i in range(habs)]
    lab_support_vars = [f"lab_sup_{i}" for i in range(labs)]
    hab_free_vars = [f"hab_free_{i}" for i in range(habs)]

    def valid_hab_cell(cell):
        return cell in interior_cells and has_available_neighbor(cell)

    def valid_lab_cell(cell):
        return cell in available_cells and has_available_neighbor(cell)

    hab_domain = sorted([cell for cell in all_cells if valid_hab_cell(cell)])
    lab_domain = sorted([cell for cell in all_cells if valid_lab_cell(cell)])
    gen_domain = available_cells[:]
    dep_domain = available_cells[:]
    air_domain = border_cells[:]

    def support_domain_for(base_domain):
        support = []
        for cell in available_cells:
            if any(orth_adjacent(cell, base) for base in base_domain):
                support.append(cell)
        return support

    lab_support_domain = support_domain_for(lab_domain)
    hab_free_domain = support_domain_for(hab_domain)

    total_modules = habs + generators + labs + deposits + airlocks
    if total_modules > len(available_cells):
        return None
    if airlocks > 0 and not air_domain:
        return None
    if habs > 0 and not hab_domain:
        return None
    if labs > 0 and not lab_domain:
        return None
    if deposits > 0 and not dep_domain:
        return None
    if generators > 0 and not gen_domain:
        return None
    if labs > 0 and not lab_support_domain:
        return None
    if habs > 0 and not hab_free_domain:
        return None
    if airlocks > len(air_domain):
        return None
    if habs > len(hab_domain):
        return None
    if labs > len(lab_domain):
        return None
    if labs > 0 and deposits == 0:
        return None

    module_vars = tuple(air_vars + dep_vars + gen_vars + lab_vars + hab_vars)
    variables = tuple(air_vars + dep_vars + gen_vars + lab_vars + hab_vars + lab_support_vars + hab_free_vars)

    domains = {}
    for v in air_vars:
        domains[v] = air_domain[:]
    for v in dep_vars:
        domains[v] = dep_domain[:]
    for v in gen_vars:
        domains[v] = gen_domain[:]
    for v in lab_vars:
        domains[v] = lab_domain[:]
    for v in hab_vars:
        domains[v] = hab_domain[:]
    for v in lab_support_vars:
        domains[v] = lab_support_domain[:]
    for v in hab_free_vars:
        domains[v] = hab_free_domain[:]

    constraints = []

    def all_assigned(values):
        return all(v is not None for v in values)

    # 1. Sin superposición (solo módulos reales)
    def no_overlap(_variables, values):
        assigned = [v for v in values if v is not None]
        return len(assigned) == len(set(assigned))

    for i in range(len(module_vars)):
        for j in range(i + 1, len(module_vars)):
            constraints.append(((module_vars[i], module_vars[j]), no_overlap))

    # 2. Cráteres intransitables
    def not_in_crater(_variables, values):
        return all(v not in crater_set for v in values if v is not None)

    for v in variables:
        constraints.append(((v,), not_in_crater))

    # 3. Esclusas en el borde
    def air_on_border(_variables, values):
        if not all_assigned(values):
            return True
        return values[0] in border_cells

    for v in air_vars:
        constraints.append(((v,), air_on_border))

    # 4. Habitacionales al interior
    def hab_interior(_variables, values):
        if not all_assigned(values):
            return True
        return values[0] in interior_cells

    for v in hab_vars:
        constraints.append(((v,), hab_interior))

    # 5. Seguridad energética
    def gen_not_adjacent_to_hab(_variables, values):
        if not all_assigned(values):
            return True
        return not orth_adjacent(values[0], values[1])

    for g in gen_vars:
        for h in hab_vars:
            constraints.append(((g, h), gen_not_adjacent_to_hab))

    # 6. Aislamiento entre generadores
    def gen_not_adjacent_to_gen(_variables, values):
        if not all_assigned(values):
            return True
        return not orth_adjacent(values[0], values[1])

    for i in range(len(gen_vars)):
        for j in range(i + 1, len(gen_vars)):
            constraints.append(((gen_vars[i], gen_vars[j]), gen_not_adjacent_to_gen))

    # 7. Cadena de suministro científico
    def lab_support_adjacent(_variables, values):
        if not all_assigned(values):
            return True
        return orth_adjacent(values[0], values[1])

    def lab_support_is_some_dep(_variables, values):
        if not all_assigned(values):
            return True
        support_cell = values[0]
        dep_cells = values[1:]
        return support_cell in dep_cells

    for lab_var, sup_var in zip(lab_vars, lab_support_vars):
        constraints.append(((lab_var, sup_var), lab_support_adjacent))
        constraints.append(((sup_var,) + tuple(dep_vars), lab_support_is_some_dep))

    # 8. Ruta de evacuación
    def hab_free_adjacent(_variables, values):
        if not all_assigned(values):
            return True
        return orth_adjacent(values[0], values[1])

    def hab_free_cell_is_empty(_variables, values):
        if not all_assigned(values):
            return True
        free_cell = values[0]
        occupied_modules = set(values[1:])
        return free_cell not in occupied_modules

    for hab_var, free_var in zip(hab_vars, hab_free_vars):
        other_modules = tuple(v for v in module_vars if v != hab_var)
        constraints.append(((hab_var, free_var), hab_free_adjacent))
        constraints.append(((free_var,) + other_modules, hab_free_cell_is_empty))

    # Romper simetrías entre módulos indistinguibles
    def ordered_pair(_variables, values):
        if not all_assigned(values):
            return True
        return values[0] < values[1]

    def add_symmetry_breaking(group):
        for i in range(len(group) - 1):
            constraints.append(((group[i], group[i + 1]), ordered_pair))

    add_symmetry_breaking(air_vars)
    add_symmetry_breaking(dep_vars)
    add_symmetry_breaking(gen_vars)
    add_symmetry_breaking(lab_vars)
    add_symmetry_breaking(hab_vars)

    problem = CspProblem(variables, domains, constraints)
    solution = backtrack(problem)

    if solution is None:
        return None

    type_order = {"air": 0, "hab": 1, "gen": 2, "lab": 3, "dep": 4}
    result = []

    for v in air_vars:
        result.append(("air",) + tuple(solution[v]))
    for v in hab_vars:
        result.append(("hab",) + tuple(solution[v]))
    for v in gen_vars:
        result.append(("gen",) + tuple(solution[v]))
    for v in lab_vars:
        result.append(("lab",) + tuple(solution[v]))
    for v in dep_vars:
        result.append(("dep",) + tuple(solution[v]))

    result.sort(key=lambda item: (type_order[item[0]], item[1], item[2]))
    return result