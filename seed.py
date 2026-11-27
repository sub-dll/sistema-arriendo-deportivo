from datetime import date, timedelta

from database import init_db
import services


def poblar_datos_ejemplo():
    init_db()

    if services.listar_categorias():
        print("La base de datos ya contiene registros. Elimina 'arriendo_deportivo.db' si deseas regenerarla.")
        return

    # 1. Categorías
    cat_ciclismo = services.crear_categoria("Ciclismo", "Bicicletas y accesorios de ruta o cerro")
    cat_agua = services.crear_categoria("Deportes Acuáticos", "Implementos para lago, río y mar")
    cat_montana = services.crear_categoria("Montañismo", "Equipamiento de trekking y alta montaña")

    # 2. Equipos (usando los 3 tipos del Factory Method)
    eq_bici = services.crear_equipo("Bicicleta MTB Aro 29", cat_ciclismo.id, 15000, 6, "terrestre")
    eq_casco = services.crear_equipo("Casco Enduro", cat_ciclismo.id, 4000, 10, "terrestre")
    eq_kayak = services.crear_equipo("Kayak Doble", cat_agua.id, 22000, 4, "acuatico")
    eq_sup = services.crear_equipo("Tabla Stand Up Paddle", cat_agua.id, 18000, 5, "acuatico")
    eq_carpa = services.crear_equipo("Carpa 4 Estaciones", cat_montana.id, 25000, 3, "montana")

    # 3. Clientes
    cli_1 = services.crear_cliente("Camila Rojas", "camila.rojas@ejemplo.cl", "+56 9 8123 4567")
    cli_2 = services.crear_cliente("Matías Paredes", "matias.paredes@ejemplo.cl", "+56 9 7654 3210")
    cli_3 = services.crear_cliente("Valentina Soto", "valentina.soto@ejemplo.cl", "+56 9 9345 6789")

    # 4. Arriendos (mezcla de activos y devueltos para alimentar los gráficos)
    hoy = date.today()
    a1 = services.registrar_arriendo(eq_bici.id, cli_1.id, hoy - timedelta(days=5), hoy - timedelta(days=3), 2)
    services.registrar_devolucion(a1.id)

    a2 = services.registrar_arriendo(eq_bici.id, cli_2.id, hoy - timedelta(days=2), hoy, 1)
    services.registrar_devolucion(a2.id)

    services.registrar_arriendo(eq_bici.id, cli_3.id, hoy, hoy + timedelta(days=2), 1)
    services.registrar_arriendo(eq_kayak.id, cli_1.id, hoy, hoy + timedelta(days=3), 2)
    services.registrar_arriendo(eq_sup.id, cli_2.id, hoy, hoy + timedelta(days=1), 1)
    services.registrar_arriendo(eq_carpa.id, cli_3.id, hoy, hoy + timedelta(days=4), 1)
    services.registrar_arriendo(eq_casco.id, cli_1.id, hoy, hoy + timedelta(days=2), 2)

    print("Datos de ejemplo cargados correctamente en 'arriendo_deportivo.db'.")


if __name__ == "__main__":
    poblar_datos_ejemplo()