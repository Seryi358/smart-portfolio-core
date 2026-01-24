from dataclasses import dataclass, field
from typing import List, Dict
from .modelos import Posicion, Instrumento


@dataclass
class Portafolio:
    """Gestiona una colección de posiciones financieras."""
    posiciones: List[Posicion] = field(default_factory=list)

    def agregar_posicion(self, posicion: Posicion) -> None:
        """Agrega una posición al portafolio.

        Args:
            posicion: Instancia de Posicion a agregar.
        """
        if not isinstance(posicion, Posicion):
            raise TypeError("solo se pueden agregar objetos Posicion")
        self.posiciones.append(posicion)

    def valor_total(self, precios_mercado: Dict[str, float]) -> float:
        """Calcula el valor total del portafolio.

        Args:
            precios_mercado: Diccionario con precios actuales por ticker.
        Returns:
            Suma de los valores actuales de todas las posiciones.
        """
        total = 0.0
        for pos in self.posiciones:
            ticker = pos.instrumento.ticker
            if ticker not in precios_mercado:
                raise ValueError(f"Falta precio de mercado para {ticker}")
            total += pos.calcular_valor_actual(precios_mercado[ticker])
        return total

    def posiciones_por_ticker(self) -> Dict[str, List[Posicion]]:
        """Agrupa las posiciones por ticker y retorna un diccionario."""
        agrupadas: Dict[str, List[Posicion]] = {}
        for pos in self.posiciones:
            clave = pos.instrumento.ticker
            agrupadas.setdefault(clave, []).append(pos)
        return agrupadas
