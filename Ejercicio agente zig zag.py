import numpy as np
import time
import random
import heapq
from collections import deque
import os


# ======================
# ENTORNO
# ======================
class Entorno:
    def __init__(self, matriz):
        self.matriz = np.array(matriz).copy()
        self.filas = len(matriz)
        self.columnas = len(matriz[0])

    def leer_celda(self, x, y):
        if x < 0 or x >= self.filas or y < 0 or y >= self.columnas:
            return 2
        return self.matriz[x][y]

    def limpiar_celda(self, x, y):
        if self.matriz[x][y] == 1:
            self.matriz[x][y] = 0

    def esta_limpio(self):
        return not np.any(self.matriz == 1)

    def mostrar(self, agente):
        os.system('cls' if os.name == 'nt' else 'clear')
        for i in range(self.filas):
            for j in range(self.columnas):
                if i == agente.x and j == agente.y:
                    print("🤖", end=" ")
                elif self.matriz[i][j] == 1:
                    print("📗", end=" ")
                elif self.matriz[i][j] == 2:
                    print("🧱", end=" ")
                else:
                    print("📕", end=" ")
            print()
        print("Pasos:", agente.pasos)



class Agente:
    def __init__(self, x_inicial=0, y_inicial=0):
        self.x = x_inicial
        self.y = y_inicial
        self.pasos = 0

    def step(self, entorno):
        if entorno.leer_celda(self.x, self.y) == 1:
            entorno.limpiar_celda(self.x, self.y)
        else:
            self.mover(entorno)

        self.pasos += 1


# ======================
# AGENTE ZIG-ZAG
# ======================
class AgenteReactivoZigZag(Agente):
    def __init__(self, x_inicial=0, y_inicial=0):
        super().__init__(x_inicial, y_inicial)
        self.direccion = 1 

    def mover(self, entorno):
        nuevo_y = self.y + self.direccion
        if entorno.leer_celda(self.x, nuevo_y) != 2:
            self.y = nuevo_y
            return
        
        if entorno.leer_celda(self.x + 1, self.y) != 2:
            self.x += 1
            self.direccion *= -1
            return
        
        if entorno.leer_celda(self.x, self.y - self.direccion) != 2:
            self.direccion *= -1
            self.y += self.direccion


# MAPA 20x20 

mapa20 = [
    [2,0,0,0,1,1,0,2,1,0,0,0,0,1,0,1,1,2,2,0],
    [1,1,0,0,2,0,0,1,0,0,0,0,0,2,2,0,0,1,0,0],
    [1,0,0,0,2,0,0,0,0,0,1,0,0,2,0,0,1,2,0,0],
    [1,0,2,0,0,0,0,0,0,0,0,2,1,1,0,2,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,2,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,1,1,0,1,0,1,1,0,2,1,0,0,2,0,0],
    [0,0,0,0,0,1,0,0,0,0,2,0,0,0,0,1,0,0,0,0],
    [0,0,0,0,0,1,0,0,0,0,0,0,0,1,2,0,1,0,0,0],
    [0,0,2,0,0,0,0,0,2,0,0,0,0,0,0,0,2,0,0,0],
    [0,0,0,0,1,2,1,0,0,0,0,0,0,0,1,2,1,2,0,0],
    [0,1,0,0,1,0,0,0,0,0,0,1,1,0,0,0,1,0,1,0],
    [1,1,0,0,1,2,0,0,0,0,0,1,0,1,1,0,0,1,0,0],
    [0,0,0,0,0,1,0,0,0,2,0,0,1,0,0,0,0,0,0,1],
    [0,0,0,0,1,0,0,0,2,0,1,0,0,0,0,1,2,0,0,2],
    [0,0,0,0,2,1,0,0,1,0,1,0,0,0,1,0,0,2,0,0],
    [2,1,0,0,0,0,1,1,2,0,0,2,0,0,2,2,1,0,0,0],
    [0,0,0,1,0,0,1,1,0,0,1,0,0,0,1,2,0,0,2,0],
    [0,0,0,0,0,1,0,1,0,1,1,0,0,1,0,2,0,1,1,0],
    [0,1,0,0,0,2,0,1,0,0,0,0,0,0,0,0,1,0,0,0],
    [0,0,0,1,0,1,0,0,0,1,1,0,0,0,0,1,0,1,0,1],
]

mundo = Entorno(mapa20)

# posición inicial recomendada
robot = AgenteReactivoZigZag(2, 3)


for _ in range(5000):
    robot.step(mundo)
    mundo.mostrar(robot)

    if mundo.esta_limpio():
        print("✅ MAPA LIMPIO")
        break

    time.sleep(0.05)