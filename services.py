from datetime import date, datetime

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from database import SessionLocal
from factory import obtener_creador
from models import Arriendo, Categoria, Cliente, Equipo


class ReglaNegocioError(Exception):
    """Error controlado para validaciones y reglas de negocio del sistema."""


def _parsear_fecha(valor) -> date:
    if isinstance(valor, date) and not isinstance(valor, datetime):
        return valor
    if isinstance(valor, str):
        try:
            return datetime.strptime(valor.strip(), "%Y-%m-%d").date()
        except ValueError as exc:
            raise ReglaNegocioError("Formato de fecha inválido. Use YYYY-MM-DD.") from exc
    raise ReglaNegocioError("Fecha inválida.")


# ==================== CATEGORÍAS ====================

def crear_categoria(nombre: str, descripcion: str = "") -> Categoria:
    nombre = nombre.strip()
    descripcion = (descripcion or "").strip()
    if not nombre:
        raise ReglaNegocioError("El nombre de la categoría es obligatorio.")

    with SessionLocal() as session:
        existente = session.query(Categoria).filter(func.lower(Categoria.nombre) == nombre.lower()).first()
        if existente:
            raise ReglaNegocioError(f"Ya existe una categoría con el nombre '{nombre}'.")

        categoria = Categoria(nombre=nombre, descripcion=descripcion)
        session.add(categoria)
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise ReglaNegocioError("No se pudo crear la categoría por conflicto de datos.") from exc
        return categoria


def listar_categorias() -> list[Categoria]:
    with SessionLocal() as session:
        return session.query(Categoria).order_by(Categoria.id.asc()).all()


def actualizar_categoria(categoria_id: int, nombre: str, descripcion: str = "") -> Categoria:
    nombre = nombre.strip()
    descripcion = (descripcion or "").strip()
    if not nombre:
        raise ReglaNegocioError("El nombre de la categoría es obligatorio.")

    with SessionLocal() as session:
        categoria = session.query(Categoria).get(categoria_id)
        if not categoria:
            raise ReglaNegocioError("La categoría indicada no existe.")

        duplicada = (
            session.query(Categoria)
            .filter(func.lower(Categoria.nombre) == nombre.lower(), Categoria.id != categoria_id)
            .first()
        )
        if duplicada:
            raise ReglaNegocioError(f"Ya existe otra categoría llamada '{nombre}'.")

        categoria.nombre = nombre
        categoria.descripcion = descripcion
        session.commit()
        return categoria


def eliminar_categoria(categoria_id: int) -> None:
    with SessionLocal() as session:
        categoria = session.query(Categoria).get(categoria_id)
        if not categoria:
            raise ReglaNegocioError("La categoría indicada no existe.")

        tiene_equipos = session.query(Equipo).filter(Equipo.categoria_id == categoria_id).first()
        if tiene_equipos:
            raise ReglaNegocioError(
                "No se puede eliminar la categoría porque tiene equipos asociados."
            )

        session.delete(categoria)
        session.commit()


# ==================== EQUIPOS ====================

def crear_equipo(
    nombre: str,
    categoria_id: int,
    precio_diario: float,
    stock_total: int,
    tipo_equipo: str,
) -> Equipo:
    nombre = nombre.strip()
    if not nombre:
        raise ReglaNegocioError("El nombre del equipo es obligatorio.")
    if precio_diario <= 0:
        raise ReglaNegocioError("El precio diario debe ser mayor a 0.")
    if stock_total < 0:
        raise ReglaNegocioError("El stock total no puede ser negativo.")

    with SessionLocal() as session:
        categoria = session.query(Categoria).get(categoria_id)
        if not categoria:
            raise ReglaNegocioError("La categoría seleccionada no existe.")

        try:
            creador = obtener_creador(tipo_equipo)
        except ValueError as exc:
            raise ReglaNegocioError(str(exc)) from exc

        equipo = creador.crear_equipo(
            nombre=nombre,
            categoria_id=categoria_id,
            precio_diario=precio_diario,
            stock_total=stock_total,
        )
        session.add(equipo)
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise ReglaNegocioError("Error de integridad al guardar el equipo.") from exc
        return equipo


def listar_equipos(solo_disponibles: bool = False) -> list[Equipo]:
    with SessionLocal() as session:
        query = session.query(Equipo).options(joinedload(Equipo.categoria))
        if solo_disponibles:
            query = query.filter(Equipo.stock_disponible > 0)
        return query.order_by(Equipo.id.asc()).all()


def actualizar_equipo(
    equipo_id: int,
    nombre: str,
    categoria_id: int,
    precio_diario: float,
    stock_total: int,
) -> Equipo:
    nombre = nombre.strip()
    if not nombre:
        raise ReglaNegocioError("El nombre del equipo es obligatorio.")
    if precio_diario <= 0:
        raise ReglaNegocioError("El precio diario debe ser mayor a 0.")
    if stock_total < 0:
        raise ReglaNegocioError("El stock total no puede ser negativo.")

    with SessionLocal() as session:
        equipo = session.query(Equipo).get(equipo_id)
        if not equipo:
            raise ReglaNegocioError("El equipo indicado no existe.")

        categoria = session.query(Categoria).get(categoria_id)
        if not categoria:
            raise ReglaNegocioError("La categoría seleccionada no existe.")

        unidades_prestadas = equipo.stock_total - equipo.stock_disponible
        if stock_total < unidades_prestadas:
            raise ReglaNegocioError(
                f"El stock total no puede ser menor a las unidades actualmente arrendadas ({unidades_prestadas})."
            )

        equipo.nombre = nombre
        equipo.categoria_id = categoria_id
        equipo.precio_diario = precio_diario
        equipo.stock_total = stock_total
        equipo.stock_disponible = stock_total - unidades_prestadas
        session.commit()
        return equipo


def eliminar_equipo(equipo_id: int) -> None:
    with SessionLocal() as session:
        equipo = session.query(Equipo).get(equipo_id)
        if not equipo:
            raise ReglaNegocioError("El equipo indicado no existe.")

        tiene_arriendos = session.query(Arriendo).filter(Arriendo.equipo_id == equipo_id).first()
        if tiene_arriendos:
            raise ReglaNegocioError(
                "No se puede eliminar el equipo porque tiene arriendos registrados."
            )

        session.delete(equipo)
        session.commit()


# ==================== CLIENTES ====================

def crear_cliente(nombre: str, correo: str, telefono: str) -> Cliente:
    nombre = nombre.strip()
    correo = correo.strip().lower()
    telefono = telefono.strip()

    if not nombre:
        raise ReglaNegocioError("El nombre del cliente es obligatorio.")
    if not correo or "@" not in correo:
        raise ReglaNegocioError("Debe ingresar un correo electrónico válido.")
    if not telefono:
        raise ReglaNegocioError("El teléfono del cliente es obligatorio.")

    with SessionLocal() as session:
        existente = session.query(Cliente).filter(func.lower(Cliente.correo) == correo).first()
        if existente:
            raise ReglaNegocioError(f"Ya existe un cliente registrado con el correo '{correo}'.")

        cliente = Cliente(nombre=nombre, correo=correo, telefono=telefono)
        session.add(cliente)
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise ReglaNegocioError("No se pudo registrar el cliente por conflicto de datos.") from exc
        return cliente


def listar_clientes() -> list[Cliente]:
    with SessionLocal() as session:
        return session.query(Cliente).order_by(Cliente.id.asc()).all()


def actualizar_cliente(cliente_id: int, nombre: str, correo: str, telefono: str) -> Cliente:
    nombre = nombre.strip()
    correo = correo.strip().lower()
    telefono = telefono.strip()

    if not nombre:
        raise ReglaNegocioError("El nombre del cliente es obligatorio.")
    if not correo or "@" not in correo:
        raise ReglaNegocioError("Debe ingresar un correo electrónico válido.")
    if not telefono:
        raise ReglaNegocioError("El teléfono del cliente es obligatorio.")

    with SessionLocal() as session:
        cliente = session.query(Cliente).get(cliente_id)
        if not cliente:
            raise ReglaNegocioError("El cliente indicado no existe.")

        duplicado = (
            session.query(Cliente)
            .filter(func.lower(Cliente.correo) == correo, Cliente.id != cliente_id)
            .first()
        )
        if duplicado:
            raise ReglaNegocioError(f"Ya existe otro cliente con el correo '{correo}'.")

        cliente.nombre = nombre
        cliente.correo = correo
        cliente.telefono = telefono
        session.commit()
        return cliente


def eliminar_cliente(cliente_id: int) -> None:
    with SessionLocal() as session:
        cliente = session.query(Cliente).get(cliente_id)
        if not cliente:
            raise ReglaNegocioError("El cliente indicado no existe.")

        tiene_arriendos = session.query(Arriendo).filter(Arriendo.cliente_id == cliente_id).first()
        if tiene_arriendos:
            raise ReglaNegocioError(
                "No se puede eliminar el cliente porque tiene arriendos registrados."
            )

        session.delete(cliente)
        session.commit()


# ==================== ARRIENDOS Y DEVOLUCIONES ====================

def registrar_arriendo(
    equipo_id: int,
    cliente_id: int,
    fecha_inicio,
    fecha_fin_prevista,
    cantidad: int,
) -> Arriendo:
    if cantidad <= 0:
        raise ReglaNegocioError("La cantidad solicitada debe ser mayor a 0.")

    f_inicio = _parsear_fecha(fecha_inicio)
    f_fin = _parsear_fecha(fecha_fin_prevista)
    if f_fin < f_inicio:
        raise ReglaNegocioError("La fecha de término prevista no puede ser anterior a la fecha de inicio.")

    with SessionLocal() as session:
        equipo = session.query(Equipo).get(equipo_id)
        if not equipo:
            raise ReglaNegocioError("El equipo seleccionado no existe.")

        cliente = session.query(Cliente).get(cliente_id)
        if not cliente:
            raise ReglaNegocioError("El cliente seleccionado no existe.")

        if cantidad > equipo.stock_disponible:
            raise ReglaNegocioError(
                f"Stock insuficiente. Disponible: {equipo.stock_disponible}, solicitado: {cantidad}."
            )

        arriendo = Arriendo(
            equipo_id=equipo_id,
            cliente_id=cliente_id,
            fecha_inicio=f_inicio,
            fecha_fin_prevista=f_fin,
            cantidad=cantidad,
            estado="ACTIVO",
        )
        # Se registra el arriendo y se descuenta el stock dentro de la misma transacción
        equipo.stock_disponible -= cantidad
        session.add(arriendo)
        try:
            session.commit()
        except Exception as exc:
            session.rollback()
            raise ReglaNegocioError(f"No se pudo completar el arriendo: {exc}") from exc
        return arriendo


def registrar_devolucion(arriendo_id: int) -> Arriendo:
    with SessionLocal() as session:
        arriendo = (
            session.query(Arriendo)
            .options(joinedload(Arriendo.equipo))
            .filter(Arriendo.id == arriendo_id)
            .first()
        )
        if not arriendo:
            raise ReglaNegocioError("El arriendo indicado no existe.")

        if arriendo.estado != "ACTIVO":
            raise ReglaNegocioError("Este arriendo ya fue devuelto; no se permiten devoluciones duplicadas.")

        equipo = arriendo.equipo
        if equipo.stock_disponible + arriendo.cantidad > equipo.stock_total:
            raise ReglaNegocioError("Inconsistencia de stock: la devolución superaría el stock total.")

        arriendo.estado = "DEVUELTO"
        equipo.stock_disponible += arriendo.cantidad
        try:
            session.commit()
        except Exception as exc:
            session.rollback()
            raise ReglaNegocioError(f"No se pudo procesar la devolución: {exc}") from exc
        return arriendo


def listar_arriendos(solo_activos: bool = False) -> list[Arriendo]:
    with SessionLocal() as session:
        query = session.query(Arriendo).options(
            joinedload(Arriendo.equipo),
            joinedload(Arriendo.cliente),
        )
        if solo_activos:
            query = query.filter(Arriendo.estado == "ACTIVO")
        return query.order_by(Arriendo.id.desc()).all()


# ==================== DATOS PARA GRÁFICOS ====================

def obtener_arriendos_por_categoria() -> list[tuple[str, int]]:
    """Cuenta operaciones de arriendo por categoría (no suma unidades)."""
    with SessionLocal() as session:
        resultados = (
            session.query(Categoria.nombre, func.count(Arriendo.id))
            .join(Equipo, Equipo.categoria_id == Categoria.id)
            .join(Arriendo, Arriendo.equipo_id == Equipo.id)
            .group_by(Categoria.id, Categoria.nombre)
            .order_by(func.count(Arriendo.id).desc())
            .all()
        )
        return [(nombre, total) for nombre, total in resultados]


def obtener_equipos_mas_arrendados(limite: int = 10) -> list[tuple[str, int]]:
    """Cuenta operaciones de arriendo por equipo (no suma unidades)."""
    with SessionLocal() as session:
        resultados = (
            session.query(Equipo.nombre, func.count(Arriendo.id))
            .join(Arriendo, Arriendo.equipo_id == Equipo.id)
            .group_by(Equipo.id, Equipo.nombre)
            .order_by(func.count(Arriendo.id).desc())
            .limit(limite)
            .all()
        )
        return [(nombre, total) for nombre, total in resultados]