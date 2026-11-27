from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

import services


def crear_figura_reportes() -> Figure:
    """Genera una figura con los dos gráficos exigidos a partir de la BD."""
    datos_categorias = services.obtener_arriendos_por_categoria()
    datos_equipos = services.obtener_equipos_mas_arrendados(limite=8)

    fig = Figure(figsize=(10, 4.4), dpi=100)
    fig.patch.set_facecolor("white")

    # Gráfico 1: Cantidad de arriendos por categoría
    ax1 = fig.add_subplot(1, 2, 1)
    ax1.set_title("Arriendos por categoría", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Categoría")
    ax1.set_ylabel("N° de arriendos")

    if datos_categorias:
        nombres_cat = [fila[0] for fila in datos_categorias]
        totales_cat = [fila[1] for fila in datos_categorias]
        barras1 = ax1.bar(nombres_cat, totales_cat, color="#2C3E50", width=0.55)
        ax1.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax1.tick_params(axis="x", rotation=20)
        for barra in barras1:
            altura = barra.get_height()
            ax1.text(
                barra.get_x() + barra.get_width() / 2,
                altura,
                f"{int(altura)}",
                ha="center",
                va="bottom",
                fontsize=9,
            )
    else:
        ax1.text(
            0.5,
            0.5,
            "Sin arriendos registrados",
            ha="center",
            va="center",
            transform=ax1.transAxes,
            color="#7F8C8D",
        )
        ax1.set_xticks([])
        ax1.set_yticks([])

    # Gráfico 2: Equipos con mayor número de arriendos
    ax2 = fig.add_subplot(1, 2, 2)
    ax2.set_title("Equipos con más arriendos", fontsize=11, fontweight="bold")
    ax2.set_xlabel("N° de arriendos")
    ax2.set_ylabel("Equipo")

    if datos_equipos:
        nombres_eq = [fila[0] for fila in datos_equipos][::-1]
        totales_eq = [fila[1] for fila in datos_equipos][::-1]
        barras2 = ax2.barh(nombres_eq, totales_eq, color="#18BC9C", height=0.55)
        ax2.xaxis.set_major_locator(MaxNLocator(integer=True))
        for barra in barras2:
            ancho = barra.get_width()
            ax2.text(
                ancho,
                barra.get_y() + barra.get_height() / 2,
                f" {int(ancho)}",
                ha="left",
                va="center",
                fontsize=9,
            )
    else:
        ax2.text(
            0.5,
            0.5,
            "Sin arriendos registrados",
            ha="center",
            va="center",
            transform=ax2.transAxes,
            color="#7F8C8D",
        )
        ax2.set_xticks([])
        ax2.set_yticks([])

    fig.tight_layout(pad=2.0)
    return fig