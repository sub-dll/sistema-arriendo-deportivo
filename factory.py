from abc import ABC, abstractmethod

from models import Equipo, EquipoAcuatico, EquipoMontana, EquipoTerrestre


class CreadorEquipo(ABC):
    """Clase creadora abstracta (Factory Method)."""

    @abstractmethod
    def crear_equipo(
        self,
        nombre: str,
        categoria_id: int,
        precio_diario: float,
        stock_total: int,
    ) -> Equipo:
        """Método fábrica que las subclases implementan para instanciar su tipo de equipo."""
        pass


class CreadorEquipoTerrestre(CreadorEquipo):
    def crear_equipo(
        self,
        nombre: str,
        categoria_id: int,
        precio_diario: float,
        stock_total: int,
    ) -> Equipo:
        return EquipoTerrestre(
            nombre=nombre,
            categoria_id=categoria_id,
            precio_diario=precio_diario,
            stock_total=stock_total,
            stock_disponible=stock_total,
        )


class CreadorEquipoAcuatico(CreadorEquipo):
    def crear_equipo(
        self,
        nombre: str,
        categoria_id: int,
        precio_diario: float,
        stock_total: int,
    ) -> Equipo:
        return EquipoAcuatico(
            nombre=nombre,
            categoria_id=categoria_id,
            precio_diario=precio_diario,
            stock_total=stock_total,
            stock_disponible=stock_total,
        )


class CreadorEquipoMontana(CreadorEquipo):
    def crear_equipo(
        self,
        nombre: str,
        categoria_id: int,
        precio_diario: float,
        stock_total: int,
    ) -> Equipo:
        return EquipoMontana(
            nombre=nombre,
            categoria_id=categoria_id,
            precio_diario=precio_diario,
            stock_total=stock_total,
            stock_disponible=stock_total,
        )


CREADORES_DISPONIBLES = {
    "terrestre": CreadorEquipoTerrestre,
    "acuatico": CreadorEquipoAcuatico,
    "montana": CreadorEquipoMontana,
}


def obtener_creador(tipo_equipo: str) -> CreadorEquipo:
    """Devuelve el creador concreto según el tipo de equipamiento solicitado."""
    clave = tipo_equipo.strip().lower()
    creador_cls = CREADORES_DISPONIBLES.get(clave)
    if not creador_cls:
        tipos_validos = ", ".join(CREADORES_DISPONIBLES.keys())
        raise ValueError(f"Tipo de equipo inválido '{tipo_equipo}'. Opciones: {tipos_validos}.")
    return creador_cls()