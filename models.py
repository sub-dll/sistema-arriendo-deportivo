from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from database import Base


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(String(255), nullable=True, default="")

    equipos = relationship("Equipo", back_populates="categoria")

    def __repr__(self):
        return f"<Categoria(id={self.id}, nombre='{self.nombre}')>"


class Equipo(Base):
    __tablename__ = "equipos"
    __table_args__ = (
        CheckConstraint("precio_diario > 0", name="ck_equipo_precio_positivo"),
        CheckConstraint("stock_total >= 0", name="ck_equipo_stock_total_no_negativo"),
        CheckConstraint("stock_disponible >= 0", name="ck_equipo_stock_disp_no_negativo"),
        CheckConstraint(
            "stock_disponible <= stock_total",
            name="ck_equipo_stock_disp_menor_igual_total",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(120), nullable=False)
    categoria_id = Column(
        Integer,
        ForeignKey("categorias.id", ondelete="RESTRICT"),
        nullable=False,
    )
    precio_diario = Column(Float, nullable=False)
    stock_total = Column(Integer, nullable=False)
    stock_disponible = Column(Integer, nullable=False)
    tipo_equipo = Column(String(30), nullable=False)

    categoria = relationship("Categoria", back_populates="equipos")
    arriendos = relationship("Arriendo", back_populates="equipo")

    __mapper_args__ = {
        "polymorphic_identity": "equipo",
        "polymorphic_on": tipo_equipo,
    }

    def protocolo_revision(self) -> str:
        """Regla polimórfica que sobreescribe cada subclase."""
        return "Revisión visual estándar."

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}(id={self.id}, nombre='{self.nombre}', "
            f"disp={self.stock_disponible}/{self.stock_total})>"
        )


class EquipoTerrestre(Equipo):
    __mapper_args__ = {"polymorphic_identity": "terrestre"}

    def protocolo_revision(self) -> str:
        return "Verificar desgaste estructural, frenos/ruedas y limpieza en seco."


class EquipoAcuatico(Equipo):
    __mapper_args__ = {"polymorphic_identity": "acuatico"}

    def protocolo_revision(self) -> str:
        return "Enjuagar con agua dulce, secar completamente y revisar sellos/flotabilidad."


class EquipoMontana(Equipo):
    __mapper_args__ = {"polymorphic_identity": "montana"}

    def protocolo_revision(self) -> str:
        return "Inspeccionar costuras, arneses, anclajes y resistencia térmica."


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(120), nullable=False)
    correo = Column(String(150), nullable=False, unique=True)
    telefono = Column(String(30), nullable=False)

    arriendos = relationship("Arriendo", back_populates="cliente")

    def __repr__(self):
        return f"<Cliente(id={self.id}, nombre='{self.nombre}', correo='{self.correo}')>"


class Arriendo(Base):
    __tablename__ = "arriendos"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_arriendo_cantidad_positiva"),
        CheckConstraint(
            "fecha_fin_prevista >= fecha_inicio",
            name="ck_arriendo_fechas_validas",
        ),
        CheckConstraint(
            "estado IN ('ACTIVO', 'DEVUELTO')",
            name="ck_arriendo_estado_valido",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    equipo_id = Column(
        Integer,
        ForeignKey("equipos.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cliente_id = Column(
        Integer,
        ForeignKey("clientes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin_prevista = Column(Date, nullable=False)
    cantidad = Column(Integer, nullable=False)
    estado = Column(String(20), nullable=False, default="ACTIVO")

    equipo = relationship("Equipo", back_populates="arriendos")
    cliente = relationship("Cliente", back_populates="arriendos")

    def __repr__(self):
        return (
            f"<Arriendo(id={self.id}, equipo_id={self.equipo_id}, "
            f"cantidad={self.cantidad}, estado='{self.estado}')>"
        )