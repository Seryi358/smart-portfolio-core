from dataclasses import dataclass, field
from typing import List

@dataclass(frozen=True)
class Instrumento:
    """Representa un activo financiero, inmutable.

    Args:
        ticker: Sigla del instrumento (ej. "AAPL", "US10Y").
        tipo: Tipo de instrumento ("Acción", "Bono", etc.).
        sector: Sector económico ("Tecnología", "Gobierno", etc.).
    """
    ticker: str
    tipo: str
    sector: str

    # No hay métodos adicionales. Por ser "frozen", no se pueden
    # modificar los atributos después de la creación. Python arrojará
    # dataclasses.FrozenInstanceError si intenta reasignar un campo.


@dataclass
class Posicion:
    """Representa una posición en un instrumento financiero.

    Args:
        instrumento: Instancia de `Instrumento` asociada a la posición.
        cantidad: Número de unidades compradas. Debe ser positivo.
        precio_entrada: Precio al que se adquirió la posición.
    """
    instrumento: Instrumento
    _cantidad: float  # atributo interno (prefijo _) para controlarlo vía property
    precio_entrada: float

    def __post_init__(self) -> None:
        """Valida los atributos después de inicializar la instancia.

        - Verifica que `instrumento` sea una instancia de Instrumento.
        - Controla que `cantidad` sea numérica y no negativa.
        - Controla que `precio_entrada` sea numérico.
        """
        if not isinstance(self.instrumento, Instrumento):
            raise TypeError("instrumento debe ser de tipo Instrumento")
        # Usa el setter de cantidad para validar el valor inicial
        self.cantidad = self._cantidad
        if not isinstance(self.precio_entrada, (int, float)):
            raise TypeError("precio_entrada debe ser numérico")

    @property
    def cantidad(self) -> float:
        """Cantidad de unidades.

        El getter retorna el valor almacenado en `_cantidad`. El setter
        valida que sea un número no negativo.
        """
        return self._cantidad

    @cantidad.setter
    def cantidad(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("cantidad debe ser numérica")
        if value < 0:
            raise ValueError("cantidad no puede ser negativa")
        self._cantidad = float(value)

    def calcular_valor_actual(self, precio_mercado: float) -> float:
        """Calcula el valor actual de la posición.

        Args:
            precio_mercado: Precio actual del instrumento.

        Returns:
            Valor de la posición = cantidad * precio_mercado.
        """
        if not isinstance(precio_mercado, (int, float)):
            raise TypeError("precio_mercado debe ser numérico")
        return self.cantidad * precio_mercado
    def calcular_ganancia_no_realizada(self, precio_actual: float) -> float:
        """Calcula la ganancia o pérdida no realizada (PnL).

        Args:
            precio_actual: Precio actual del instrumento.

        Returns:
            Ganancia o pérdida = (precio_actual - precio_entrada) * cantidad
        """
        if not isinstance(precio_actual, (int, float)):
            raise TypeError("precio_actual debe ser numérico")
        return (precio_actual - self.precio_entrada) * self.cantidad

    def tiene_alerta_perdida(self, precio_actual: float, umbral: float = 0.10) -> bool:
        """Indica si la pérdida no realizada supera el umbral porcentual.

        Args:
            precio_actual: Precio actual del instrumento.
            umbral: Porcentaje máximo de pérdida permitido (default 0.10 = 10%).

        Returns:
            True si la pérdida es mayor al umbral, False en caso contrario.
        """
        pnl = self.calcular_ganancia_no_realizada(precio_actual)
        costo_base = self.precio_entrada * self.cantidad
        if costo_base == 0:
            return False
        return (pnl / costo_base) < -umbral
