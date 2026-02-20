import numpy as np
import time
import random
import heapq
from collections import deque
from IPython.display import clear_output


class Entorno:
    def __init__(self, matriz):
        self.matriz = np.array(matriz).copy()
        self.columnas = len(matriz[0])
        self.filas = len(matriz)

    def leer_celda(self, x, y):
        if x < 0 or x >= self.filas or y < 0 or y >= self.columnas:
            return 2  # fuera del mapa = muro
        return self.matriz[x][y]

    def limpiar_celda(self, x, y):
        if self.matriz[x][y] == 1:
            self.matriz[x][y] = 0

    def esta_limpio(self):
        return not np.any(self.matriz == 1)

    def mostrar(self, agente):
        clear_output(wait=True)
        for i in range(self.filas):
            for j in range(self.columnas):
                if i == agente.x and j == agente.y:
                    print("🤖", end=" ")
                elif self.matriz[i][j] == 1:
                    print("📗", end=" ")  # basura
                elif self.matriz[i][j] == 2:
                    print("🧱", end=" ")  # muro
                else:
                    print("📕", end=" ")  # limpio
            print()
        print("Pasos:", agente.pasos)


class Agente:
    def __init__(self, x_inicial=0, y_inicial=0):
        self.x = x_inicial
        self.y = y_inicial
        self.pasos = 0

    def percibir(self, entorno):
        pass

    def decidir(self, percepcion):
        pass

    def actuar(self, accion, entorno):
        pass

    def step(self, entorno):
        percepcion = self.percibir(entorno)
        accion = self.decidir(percepcion)
        self.actuar(accion, entorno)
        self.pasos += 1


class AgenteReactivo(Agente):
    def percibir(self, entorno):
        return entorno.leer_celda(self.x, self.y)

    def decidir(self, percepcion):
        if percepcion == 1:
            return "LIMPIAR"
        return "MOVER"

    def actuar(self, accion, entorno):
        if accion == "LIMPIAR":
            entorno.limpiar_celda(self.x, self.y)
        else:
            m = random.choice(['U', 'D', 'L', 'R'])
            x_actual, y_actual = self.x, self.y
            if m == 'U':
                x_actual -= 1
            elif m == 'D':
                x_actual += 1
            elif m == 'L':
                y_actual -= 1
            elif m == 'R':
                y_actual += 1

            if entorno.leer_celda(x_actual, y_actual) != 2:
                self.x, self.y = x_actual, y_actual


class AgenteManhattan(Agente):  # ahora sí A*
    def __init__(self, x_inicial=0, y_inicial=0):
        super().__init__(x_inicial, y_inicial)
        self.plan = []        # movimientos pendientes ['U','R',...]
        self.objetivo = None  # (x,y) de la basura actual

    def percibir(self, entorno):
        lista_basuras = []
        for i in range(entorno.filas):
            for j in range(entorno.columnas):
                if entorno.leer_celda(i, j) == 1:
                    lista_basuras.append((i, j))

        sucio_aqui = (entorno.leer_celda(self.x, self.y) == 1)
        return {"entorno": entorno, "lista_basuras": lista_basuras, "sucio_aqui": sucio_aqui}

    def _vecinos(self, entorno, x, y):
        for dx, dy, m in [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]:
            nx, ny = x + dx, y + dy
            if entorno.leer_celda(nx, ny) != 2:
                yield nx, ny, m

    def _heuristica(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])  # Manhattan

    def _reconstruir_camino(self, came_from, actual):
        path = [actual]
        while actual in came_from:
            actual = came_from[actual]
            path.append(actual)
        path.reverse()
        return path

    def _coords_a_movs(self, path):
        movs = []
        for (x1, y1), (x2, y2) in zip(path, path[1:]):
            if x2 == x1 - 1:
                movs.append('U')
            elif x2 == x1 + 1:
                movs.append('D')
            elif y2 == y1 - 1:
                movs.append('L')
            elif y2 == y1 + 1:
                movs.append('R')
        return movs

    def _a_star(self, entorno, start, goal):
        open_heap = []
        heapq.heappush(open_heap, (0, start))

        came_from = {}
        g = {start: 0}

        while open_heap:
            _, current = heapq.heappop(open_heap)

            if current == goal:
                return self._reconstruir_camino(came_from, current)

            cx, cy = current
            for nx, ny, _ in self._vecinos(entorno, cx, cy):
                vecino = (nx, ny)
                tentative_g = g[current] + 1

                if tentative_g < g.get(vecino, float('inf')):
                    came_from[vecino] = current
                    g[vecino] = tentative_g
                    f = tentative_g + self._heuristica(vecino, goal)
                    heapq.heappush(open_heap, (f, vecino))

        return None  # sin ruta

    # Escoge la basura más cercana REAL (por pasos) y alcanzable (evita objetivos tras muros)
    def _objetivo_mas_cercano(self, entorno, basuras):
        if not basuras:
            return None

        objetivos = set(basuras)
        q = deque([(self.x, self.y)])
        visit = {(self.x, self.y)}

        while q:
            x, y = q.popleft()
            if (x, y) in objetivos:
                return (x, y)

            for nx, ny, _ in self._vecinos(entorno, x, y):
                if (nx, ny) not in visit:
                    visit.add((nx, ny))
                    q.append((nx, ny))

        return None

    def decidir(self, percepcion):
        entorno = percepcion["entorno"]

        # 1) si hay basura en mi celda: limpio
        if percepcion["sucio_aqui"]:
            self.plan = []
            self.objetivo = None
            return "LIMPIAR"

        # 2) si no hay basura en el mapa
        if not percepcion["lista_basuras"]:
            self.plan = []
            self.objetivo = None
            return "NADA"

        # 3) si no hay plan o el objetivo ya no existe: replanteo
        if (not self.plan) or (self.objetivo not in percepcion["lista_basuras"]):
            self.objetivo = self._objetivo_mas_cercano(entorno, percepcion["lista_basuras"])
            if self.objetivo is None:
                return "NADA"

            path = self._a_star(entorno, (self.x, self.y), self.objetivo)
            if not path or len(path) < 2:
                return "NADA"

            self.plan = self._coords_a_movs(path)

        # 4) ejecutar el siguiente movimiento del plan
        return self.plan.pop(0)

    def actuar(self, accion, entorno):
        if accion == "LIMPIAR":
            entorno.limpiar_celda(self.x, self.y)
            return

        if accion in ("U", "D", "L", "R"):
            x_actual, y_actual = self.x, self.y
            if accion == "U":
                x_actual -= 1
            elif accion == "D":
                x_actual += 1
            elif accion == "L":
                y_actual -= 1
            elif accion == "R":
                y_actual += 1

            if entorno.leer_celda(x_actual, y_actual) != 2:
                self.x, self.y = x_actual, y_actual


mapa1 = [
    [2, 0, 0, 0, 1, 1, 0, 2, 1, 0, 0, 0, 0, 1, 0, 1, 1, 2, 2, 0],
    [1, 1, 0, 0, 2, 0, 0, 1, 0, 0, 0, 0, 0, 2, 2, 0, 0, 1, 0, 0],
    [1, 0, 0, 0, 2, 0, 0, 0, 0, 0, 1, 0, 0, 2, 0, 0, 1, 2, 0, 0],
    [1, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 2, 1, 1, 0, 2, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 2, 1, 0, 0, 2, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 2, 0, 1, 0, 0, 0],
    [0, 0, 2, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0],
    [0, 0, 0, 0, 1, 2, 1, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 2, 0, 0],
    [0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0],
    [1, 1, 0, 0, 1, 2, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1],
    [0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 1, 0, 0, 0, 0, 1, 2, 0, 0, 2],
    [0, 0, 0, 0, 2, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 2, 0, 0],
    [2, 1, 0, 0, 0, 0, 1, 1, 2, 0, 0, 2, 0, 0, 2, 2, 1, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 2, 0, 0, 2, 0],
    [0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 2, 0, 1, 1, 0],
    [0, 1, 0, 0, 0, 2, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    [0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1],
]


mundo = Entorno(mapa1)

# robot = AgenteReactivo(2, 3)   # si quieres probar el reactivo
robot = AgenteManhattan(2, 3)    # A*

for _ in range(5000):  # sube el límite para asegurar que alcance a limpiar todo
    robot.step(mundo)
    mundo.mostrar(robot)

    if mundo.esta_limpio():
        print("mapa limpio")
        break

    time.sleep(0)  # pon 0.05 si quieres ver animación más lenta
