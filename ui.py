from datetime import date, timedelta
from tkinter import messagebox
import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import ttkbootstrap as tb

import charts
from factory import CREADORES_DISPONIBLES
import services
from services import ReglaNegocioError


class ArriendoApp(tb.Window):
    def __init__(self):
        super().__init__(themename="flatly")
        self.title("Sistema de Gestión de Arriendo de Equipamiento Deportivo")
        self.geometry("1120x680")
        self.minsize(960, 600)

        # Mapas auxiliares para traducir texto del Combobox -> ID en BD
        self.mapa_categorias: dict[str, int] = {}
        self.mapa_equipos_arriendo: dict[str, int] = {}
        self.mapa_clientes_arriendo: dict[str, int] = {}
        self.equipos_cache: dict[int, object] = {}

        # IDs actualmente seleccionados para edición/eliminación
        self.categoria_sel_id: int | None = None
        self.equipo_sel_id: int | None = None
        self.cliente_sel_id: int | None = None

        self.canvas_graficos = None

        self._construir_interfaz()
        self.refrescar_todo()

    def _construir_interfaz(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tab_categorias = ttk.Frame(self.notebook, padding=10)
        self.tab_equipos = ttk.Frame(self.notebook, padding=10)
        self.tab_clientes = ttk.Frame(self.notebook, padding=10)
        self.tab_arriendos = ttk.Frame(self.notebook, padding=10)
        self.tab_graficos = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.tab_categorias, text="Categorías")
        self.notebook.add(self.tab_equipos, text="Equipos")
        self.notebook.add(self.tab_clientes, text="Clientes")
        self.notebook.add(self.tab_arriendos, text="Arriendos y Devoluciones")
        self.notebook.add(self.tab_graficos, text="Gráficos")

        self._construir_tab_categorias()
        self._construir_tab_equipos()
        self._construir_tab_clientes()
        self._construir_tab_arriendos()
        self._construir_tab_graficos()

        self.notebook.bind("<<NotebookTabChanged>>", self._al_cambiar_pestana)

    def _al_cambiar_pestana(self, event):
        pestana_actual = self.notebook.select()
        if pestana_actual == str(self.tab_graficos):
            self._actualizar_graficos()

    def refrescar_todo(self):
        self._cargar_categorias()
        self._cargar_equipos()
        self._cargar_clientes()
        self._cargar_arriendos()
        self._cargar_combos_arriendo()

    # ==================== PESTAÑA CATEGORÍAS ====================

    def _construir_tab_categorias(self):
        form = ttk.LabelFrame(self.tab_categorias, text="Datos de la categoría", padding=10)
        form.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(form, text="Nombre:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.cat_nombre = ttk.Entry(form, width=30)
        self.cat_nombre.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(form, text="Descripción:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.cat_desc = ttk.Entry(form, width=45)
        self.cat_desc.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        botones = ttk.Frame(form)
        botones.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(8, 0))
        tb.Button(botones, text="Crear", bootstyle="success", command=self._crear_categoria).pack(side=tk.LEFT, padx=4)
        tb.Button(botones, text="Actualizar", bootstyle="primary", command=self._actualizar_categoria).pack(side=tk.LEFT, padx=4)
        tb.Button(botones, text="Eliminar", bootstyle="danger", command=self._eliminar_categoria).pack(side=tk.LEFT, padx=4)
        tb.Button(botones, text="Limpiar", bootstyle="secondary", command=self._limpiar_categoria).pack(side=tk.LEFT, padx=4)

        cols = ("id", "nombre", "descripcion")
        self.tree_categorias = ttk.Treeview(self.tab_categorias, columns=cols, show="headings", height=16)
        self.tree_categorias.heading("id", text="ID")
        self.tree_categorias.heading("nombre", text="Nombre")
        self.tree_categorias.heading("descripcion", text="Descripción")
        self.tree_categorias.column("id", width=60, anchor=tk.CENTER)
        self.tree_categorias.column("nombre", width=220)
        self.tree_categorias.column("descripcion", width=500)
        self.tree_categorias.pack(fill=tk.BOTH, expand=True)
        self.tree_categorias.bind("<<TreeviewSelect>>", self._seleccionar_categoria)

    def _cargar_categorias(self):
        for item in self.tree_categorias.get_children():
            self.tree_categorias.delete(item)

        categorias = services.listar_categorias()
        self.mapa_categorias.clear()
        nombres_combo = []

        for cat in categorias:
            self.tree_categorias.insert("", tk.END, values=(cat.id, cat.nombre, cat.descripcion or ""))
            etiqueta = f"{cat.id} - {cat.nombre}"
            self.mapa_categorias[etiqueta] = cat.id
            nombres_combo.append(etiqueta)

        self.eq_categoria["values"] = nombres_combo

    def _seleccionar_categoria(self, event):
        seleccion = self.tree_categorias.selection()
        if not seleccion:
            return
        valores = self.tree_categorias.item(seleccion[0], "values")
        self.categoria_sel_id = int(valores[0])
        self.cat_nombre.delete(0, tk.END)
        self.cat_nombre.insert(0, valores[1])
        self.cat_desc.delete(0, tk.END)
        self.cat_desc.insert(0, valores[2])

    def _limpiar_categoria(self):
        self.categoria_sel_id = None
        self.cat_nombre.delete(0, tk.END)
        self.cat_desc.delete(0, tk.END)
        self.tree_categorias.selection_remove(self.tree_categorias.selection())

    def _crear_categoria(self):
        try:
            services.crear_categoria(self.cat_nombre.get(), self.cat_desc.get())
            self._limpiar_categoria()
            self.refrescar_todo()
            messagebox.showinfo("Éxito", "Categoría creada correctamente.")
        except ReglaNegocioError as err:
            messagebox.showerror("Validación", str(err))

    def _actualizar_categoria(self):
        if self.categoria_sel_id is None:
            messagebox.showwarning("Aviso", "Seleccione una categoría de la tabla para actualizar.")
            return
        try:
            services.actualizar_categoria(self.categoria_sel_id, self.cat_nombre.get(), self.cat_desc.get())
            self._limpiar_categoria()
            self.refrescar_todo()
            messagebox.showinfo("Éxito", "Categoría actualizada correctamente.")
        except ReglaNegocioError as err:
            messagebox.showerror("Validación", str(err))

    def _eliminar_categoria(self):
        if self.categoria_sel_id is None:
            messagebox.showwarning("Aviso", "Seleccione una categoría de la tabla para eliminar.")
            return
        try:
            services.eliminar_categoria(self.categoria_sel_id)
            self._limpiar_categoria()
            self.refrescar_todo()
            messagebox.showinfo("Éxito", "Categoría eliminada correctamente.")
        except ReglaNegocioError as err:
            messagebox.showerror("Restricción", str(err))

    # ==================== PESTAÑA EQUIPOS ====================

    def _construir_tab_equipos(self):
        form = ttk.LabelFrame(self.tab_equipos, text="Datos del equipo", padding=10)
        form.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(form, text="Nombre:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=4)
        self.eq_nombre = ttk.Entry(form, width=28)
        self.eq_nombre.grid(row=0, column=1, sticky=tk.W, padx=5, pady=4)

        ttk.Label(form, text="Categoría:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=4)
        self.eq_categoria = ttk.Combobox(form, state="readonly", width=26)
        self.eq_categoria.grid(row=0, column=3, sticky=tk.W, padx=5, pady=4)

        ttk.Label(form, text="Tipo (Factory):").grid(row=0, column=4, sticky=tk.W, padx=5, pady=4)
        self.eq_tipo = ttk.Combobox(
            form,
            state="readonly",
            width=16,
            values=list(CREADORES_DISPONIBLES.keys()),
        )
        self.eq_tipo.current(0)
        self.eq_tipo.grid(row=0, column=5, sticky=tk.W, padx=5, pady=4)

        ttk.Label(form, text="Precio diario ($):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=4)
        self.eq_precio = ttk.Entry(form, width=18)
        self.eq_precio.grid(row=1, column=1, sticky=tk.W, padx=5, pady=4)

        ttk.Label(form, text="Stock total:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=4)
        self.eq_stock = ttk.Entry(form, width=18)
        self.eq_stock.grid(row=1, column=3, sticky=tk.W, padx=5, pady=4)

        botones = ttk.Frame(form)
        botones.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=(8, 0))
        tb.Button(botones, text="Crear", bootstyle="success", command=self._crear_equipo).pack(side=tk.LEFT, padx=4)
        tb.Button(botones, text="Actualizar", bootstyle="primary", command=self._actualizar_equipo).pack(side=tk.LEFT, padx=4)
        tb.Button(botones, text="Eliminar", bootstyle="danger", command=self._eliminar_equipo).pack(side=tk.LEFT, padx=4)
        tb.Button(botones, text="Limpiar", bootstyle="secondary", command=self._limpiar_equipo).pack(side=tk.LEFT, padx=4)

        self.var_solo_disponibles = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            form,
            text="Mostrar solo equipos disponibles",
            variable=self.var_solo_disponibles,
            command=self._cargar_equipos,
        ).grid(row=2, column=4, columnspan=2, sticky=tk.E, pady=(8, 0))

        self.lbl_protocolo = ttk.Label(
            self.tab_equipos,
            text="Seleccione un equipo para ver su protocolo de revisión (polimorfismo Factory Method).",
            foreground="#2C3E50",
        )
        self.lbl_protocolo.pack(anchor=tk.W, pady=(0, 6))

        cols = ("id", "nombre", "categoria", "tipo", "precio", "total", "disponible")
        self.tree_equipos = ttk.Treeview(self.tab_equipos, columns=cols, show="headings", height=14)
        encabezados = {
            "id": ("ID", 50, tk.CENTER),
            "nombre": ("Nombre", 210, tk.W),
            "categoria": ("Categoría", 160, tk.W),
            "tipo": ("Tipo", 100, tk.CENTER),
            "precio": ("Precio Diario", 110, tk.E),
            "total": ("Stock Total", 95, tk.CENTER),
            "disponible": ("Disponible", 95, tk.CENTER),
        }
        for col, (texto, ancho, alineacion) in encabezados.items():
            self.tree_equipos.heading(col, text=texto)
            self.tree_equipos.column(col, width=ancho, anchor=alineacion)

        self.tree_equipos.pack(fill=tk.BOTH, expand=True)
        self.tree_equipos.bind("<<TreeviewSelect>>", self._seleccionar_equipo)

    def _cargar_equipos(self):
        for item in self.tree_equipos.get_children():
            self.tree_equipos.delete(item)

        equipos = services.listar_equipos(solo_disponibles=self.var_solo_disponibles.get())
        self.equipos_cache.clear()
        for eq in equipos:
            self.equipos_cache[eq.id] = eq
            nombre_cat = eq.categoria.nombre if eq.categoria else ""
            self.tree_equipos.insert(
                "",
                tk.END,
                values=(
                    eq.id,
                    eq.nombre,
                    nombre_cat,
                    eq.tipo_equipo,
                    f"${eq.precio_diario:,.0f}",
                    eq.stock_total,
                    eq.stock_disponible,
                ),
            )

    def _seleccionar_equipo(self, event):
        seleccion = self.tree_equipos.selection()
        if not seleccion:
            return
        valores = self.tree_equipos.item(seleccion[0], "values")
        eq_id = int(valores[0])
        equipo = self.equipos_cache.get(eq_id)
        if not equipo:
            return

        self.equipo_sel_id = eq_id
        self.eq_nombre.delete(0, tk.END)
        self.eq_nombre.insert(0, equipo.nombre)

        etiqueta_cat = f"{equipo.categoria_id} - {equipo.categoria.nombre}"
        self.eq_categoria.set(etiqueta_cat)

        self.eq_tipo.set(equipo.tipo_equipo)
        self.eq_tipo.configure(state="disabled")

        self.eq_precio.delete(0, tk.END)
        self.eq_precio.insert(0, str(equipo.precio_diario))

        self.eq_stock.delete(0, tk.END)
        self.eq_stock.insert(0, str(equipo.stock_total))

        self.lbl_protocolo.configure(
            text=f"Clase [{equipo.__class__.__name__}] — Protocolo de revisión: {equipo.protocolo_revision()}"
        )

    def _limpiar_equipo(self):
        self.equipo_sel_id = None
        self.eq_nombre.delete(0, tk.END)
        self.eq_categoria.set("")
        self.eq_tipo.configure(state="readonly")
        self.eq_tipo.current(0)
        self.eq_precio.delete(0, tk.END)
        self.eq_stock.delete(0, tk.END)
        self.lbl_protocolo.configure(
            text="Seleccione un equipo para ver su protocolo de revisión (polimorfismo Factory Method)."
        )
        self.tree_equipos.selection_remove(self.tree_equipos.selection())

    def _leer_campos_equipo(self):
        cat_etiqueta = self.eq_categoria.get()
        if cat_etiqueta not in self.mapa_categorias:
            raise ReglaNegocioError("Debe seleccionar una categoría válida.")
        try:
            precio = float(self.eq_precio.get())
        except ValueError as exc:
            raise ReglaNegocioError("El precio diario debe ser un número válido.") from exc
        try:
            stock = int(self.eq_stock.get())
        except ValueError as exc:
            raise ReglaNegocioError("El stock total debe ser un número entero.") from exc
        return self.eq_nombre.get(), self.mapa_categorias[cat_etiqueta], precio, stock

    def _crear_equipo(self):
        try:
            nombre, cat_id, precio, stock = self._leer_campos_equipo()
            tipo = self.eq_tipo.get()
            services.crear_equipo(nombre, cat_id, precio, stock, tipo)
            self._limpiar_equipo()
            self.refrescar_todo()
            messagebox.showinfo("Éxito", "Equipo creado correctamente mediante Factory Method.")
        except ReglaNegocioError as err:
            messagebox.showerror("Validación", str(err))

    def _actualizar_equipo(self):
        if self.equipo_sel_id is None:
            messagebox.showwarning("Aviso", "Seleccione un equipo de la tabla para actualizar.")
            return
        try:
            nombre, cat_id, precio, stock = self._leer_campos_equipo()
            services.actualizar_equipo(self.equipo_sel_id, nombre, cat_id, precio, stock)
            self._limpiar_equipo()
            self.refrescar_todo()
            messagebox.showinfo("Éxito", "Equipo actualizado correctamente.")
        except ReglaNegocioError as err:
            messagebox.showerror("Validación", str(err))

    def _eliminar_equipo(self):
        if self.equipo_sel_id is None:
            messagebox.showwarning("Aviso", "Seleccione un equipo de la tabla para eliminar.")
            return
        try:
            services.eliminar_equipo(self.equipo_sel_id)
            self._limpiar_equipo()
            self.refrescar_todo()
            messagebox.showinfo("Éxito", "Equipo eliminado correctamente.")
        except ReglaNegocioError as err:
            messagebox.showerror("Restricción", str(err))

    # ==================== PESTAÑA CLIENTES ====================

    def _construir_tab_clientes(self):
        form = ttk.LabelFrame(self.tab_clientes, text="Datos del cliente", padding=10)
        form.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(form, text="Nombre:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.cli_nombre = ttk.Entry(form, width=26)
        self.cli_nombre.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(form, text="Correo:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.cli_correo = ttk.Entry(form, width=28)
        self.cli_correo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        ttk.Label(form, text="Teléfono:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        self.cli_telefono = ttk.Entry(form, width=18)
        self.cli_telefono.grid(row=0, column=5, sticky=tk.W, padx=5, pady=5)

        botones = ttk.Frame(form)
        botones.grid(row=1, column=0, columnspan=6, sticky=tk.W, pady=(8, 0))
        tb.Button(botones, text="Crear", bootstyle="success", command=self._crear_cliente).pack(side=tk.LEFT, padx=4)
        tb.Button(botones, text="Actualizar", bootstyle="primary", command=self._actualizar_cliente).pack(side=tk.LEFT, padx=4)
        tb.Button(botones, text="Eliminar", bootstyle="danger", command=self._eliminar_cliente).pack(side=tk.LEFT, padx=4)
        tb.Button(botones, text="Limpiar", bootstyle="secondary", command=self._limpiar_cliente).pack(side=tk.LEFT, padx=4)

        cols = ("id", "nombre", "correo", "telefono")
        self.tree_clientes = ttk.Treeview(self.tab_clientes, columns=cols, show="headings", height=16)
        self.tree_clientes.heading("id", text="ID")
        self.tree_clientes.heading("nombre", text="Nombre")
        self.tree_clientes.heading("correo", text="Correo")
        self.tree_clientes.heading("telefono", text="Teléfono")
        self.tree_clientes.column("id", width=60, anchor=tk.CENTER)
        self.tree_clientes.column("nombre", width=240)
        self.tree_clientes.column("correo", width=280)
        self.tree_clientes.column("telefono", width=160)
        self.tree_clientes.pack(fill=tk.BOTH, expand=True)
        self.tree_clientes.bind("<<TreeviewSelect>>", self._seleccionar_cliente)

    def _cargar_clientes(self):
        for item in self.tree_clientes.get_children():
            self.tree_clientes.delete(item)
        for cli in services.listar_clientes():
            self.tree_clientes.insert("", tk.END, values=(cli.id, cli.nombre, cli.correo, cli.telefono))

    def _seleccionar_cliente(self, event):
        seleccion = self.tree_clientes.selection()
        if not seleccion:
            return
        valores = self.tree_clientes.item(seleccion[0], "values")
        self.cliente_sel_id = int(valores[0])
        self.cli_nombre.delete(0, tk.END)
        self.cli_nombre.insert(0, valores[1])
        self.cli_correo.delete(0, tk.END)
        self.cli_correo.insert(0, valores[2])
        self.cli_telefono.delete(0, tk.END)
        self.cli_telefono.insert(0, valores[3])

    def _limpiar_cliente(self):
        self.cliente_sel_id = None
        self.cli_nombre.delete(0, tk.END)
        self.cli_correo.delete(0, tk.END)
        self.cli_telefono.delete(0, tk.END)
        self.tree_clientes.selection_remove(self.tree_clientes.selection())

    def _crear_cliente(self):
        try:
            services.crear_cliente(self.cli_nombre.get(), self.cli_correo.get(), self.cli_telefono.get())
            self._limpiar_cliente()
            self.refrescar_todo()
            messagebox.showinfo("Éxito", "Cliente registrado correctamente.")
        except ReglaNegocioError as err:
            messagebox.showerror("Validación", str(err))

    def _actualizar_cliente(self):
        if self.cliente_sel_id is None:
            messagebox.showwarning("Aviso", "Seleccione un cliente de la tabla para actualizar.")
            return
        try:
            services.actualizar_cliente(
                self.cliente_sel_id,
                self.cli_nombre.get(),
                self.cli_correo.get(),
                self.cli_telefono.get(),
            )
            self._limpiar_cliente()
            self.refrescar_todo()
            messagebox.showinfo("Éxito", "Cliente actualizado correctamente.")
        except ReglaNegocioError as err:
            messagebox.showerror("Validación", str(err))

    def _eliminar_cliente(self):
        if self.cliente_sel_id is None:
            messagebox.showwarning("Aviso", "Seleccione un cliente de la tabla para eliminar.")
            return
        try:
            services.eliminar_cliente(self.cliente_sel_id)
            self._limpiar_cliente()
            self.refrescar_todo()
            messagebox.showinfo("Éxito", "Cliente eliminado correctamente.")
        except ReglaNegocioError as err:
            messagebox.showerror("Restricción", str(err))

    # ==================== PESTAÑA ARRIENDOS ====================

    def _construir_tab_arriendos(self):
        form = ttk.LabelFrame(self.tab_arriendos, text="Registrar nuevo arriendo", padding=10)
        form.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(form, text="Equipo:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.arr_equipo = ttk.Combobox(form, state="readonly", width=34)
        self.arr_equipo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(form, text="Cliente:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.arr_cliente = ttk.Combobox(form, state="readonly", width=32)
        self.arr_cliente.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        ttk.Label(form, text="Cantidad:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        self.arr_cantidad = ttk.Entry(form, width=10)
        self.arr_cantidad.insert(0, "1")
        self.arr_cantidad.grid(row=0, column=5, sticky=tk.W, padx=5, pady=5)

        ttk.Label(form, text="Fecha inicio:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.arr_fecha_inicio = tb.DateEntry(form, dateformat="%Y-%m-%d", startdate=date.today())
        self.arr_fecha_inicio.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(form, text="Fecha fin prevista:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.arr_fecha_fin = tb.DateEntry(
            form,
            dateformat="%Y-%m-%d",
            startdate=date.today() + timedelta(days=1),
        )
        self.arr_fecha_fin.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)

        tb.Button(
            form,
            text="Registrar arriendo",
            bootstyle="success",
            command=self._registrar_arriendo,
        ).grid(row=1, column=4, columnspan=2, sticky=tk.E, padx=5, pady=5)

        barra_acciones = ttk.Frame(self.tab_arriendos)
        barra_acciones.pack(fill=tk.X, pady=(0, 6))

        self.var_solo_activos = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            barra_acciones,
            text="Ver solo arriendos ACTIVOS (desmarcar para ver historial completo)",
            variable=self.var_solo_activos,
            command=self._cargar_arriendos,
        ).pack(side=tk.LEFT)

        tb.Button(
            barra_acciones,
            text="Registrar devolución del arriendo seleccionado",
            bootstyle="warning",
            command=self._registrar_devolucion,
        ).pack(side=tk.RIGHT)

        cols = ("id", "equipo", "cliente", "inicio", "fin", "cantidad", "estado")
        self.tree_arriendos = ttk.Treeview(self.tab_arriendos, columns=cols, show="headings", height=14)
        encabezados = {
            "id": ("ID", 55, tk.CENTER),
            "equipo": ("Equipo", 220, tk.W),
            "cliente": ("Cliente", 200, tk.W),
            "inicio": ("Fecha Inicio", 110, tk.CENTER),
            "fin": ("Fin Prevista", 110, tk.CENTER),
            "cantidad": ("Cantidad", 85, tk.CENTER),
            "estado": ("Estado", 100, tk.CENTER),
        }
        for col, (texto, ancho, alineacion) in encabezados.items():
            self.tree_arriendos.heading(col, text=texto)
            self.tree_arriendos.column(col, width=ancho, anchor=alineacion)

        self.tree_arriendos.pack(fill=tk.BOTH, expand=True)

    def _cargar_combos_arriendo(self):
        self.mapa_equipos_arriendo.clear()
        etiquetas_eq = []
        for eq in services.listar_equipos(solo_disponibles=False):
            etiqueta = f"{eq.id} - {eq.nombre} (Disp: {eq.stock_disponible})"
            self.mapa_equipos_arriendo[etiqueta] = eq.id
            etiquetas_eq.append(etiqueta)
        self.arr_equipo["values"] = etiquetas_eq
        if self.arr_equipo.get() not in self.mapa_equipos_arriendo:
            self.arr_equipo.set("")

        self.mapa_clientes_arriendo.clear()
        etiquetas_cli = []
        for cli in services.listar_clientes():
            etiqueta = f"{cli.id} - {cli.nombre}"
            self.mapa_clientes_arriendo[etiqueta] = cli.id
            etiquetas_cli.append(etiqueta)
        self.arr_cliente["values"] = etiquetas_cli
        if self.arr_cliente.get() not in self.mapa_clientes_arriendo:
            self.arr_cliente.set("")

    def _cargar_arriendos(self):
        for item in self.tree_arriendos.get_children():
            self.tree_arriendos.delete(item)

        for arr in services.listar_arriendos(solo_activos=self.var_solo_activos.get()):
            self.tree_arriendos.insert(
                "",
                tk.END,
                values=(
                    arr.id,
                    arr.equipo.nombre if arr.equipo else "",
                    arr.cliente.nombre if arr.cliente else "",
                    arr.fecha_inicio.strftime("%Y-%m-%d"),
                    arr.fecha_fin_prevista.strftime("%Y-%m-%d"),
                    arr.cantidad,
                    arr.estado,
                ),
            )

    def _registrar_arriendo(self):
        etiqueta_eq = self.arr_equipo.get()
        etiqueta_cli = self.arr_cliente.get()
        if etiqueta_eq not in self.mapa_equipos_arriendo:
            messagebox.showerror("Validación", "Debe seleccionar un equipo.")
            return
        if etiqueta_cli not in self.mapa_clientes_arriendo:
            messagebox.showerror("Validación", "Debe seleccionar un cliente.")
            return

        try:
            cantidad = int(self.arr_cantidad.get())
        except ValueError:
            messagebox.showerror("Validación", "La cantidad debe ser un número entero.")
            return

        fecha_inicio = self.arr_fecha_inicio.entry.get()
        fecha_fin = self.arr_fecha_fin.entry.get()

        try:
            services.registrar_arriendo(
                equipo_id=self.mapa_equipos_arriendo[etiqueta_eq],
                cliente_id=self.mapa_clientes_arriendo[etiqueta_cli],
                fecha_inicio=fecha_inicio,
                fecha_fin_prevista=fecha_fin,
                cantidad=cantidad,
            )
            self.arr_cantidad.delete(0, tk.END)
            self.arr_cantidad.insert(0, "1")
            self.refrescar_todo()
            messagebox.showinfo("Éxito", "Arriendo registrado y stock descontado.")
        except ReglaNegocioError as err:
            messagebox.showerror("Operación rechazada", str(err))

    def _registrar_devolucion(self):
        seleccion = self.tree_arriendos.selection()
        if not seleccion:
            messagebox.showwarning("Aviso", "Seleccione un arriendo de la tabla para devolver.")
            return

        arriendo_id = int(self.tree_arriendos.item(seleccion[0], "values")[0])
        try:
            arriendo = services.registrar_devolucion(arriendo_id)
            protocolo = arriendo.equipo.protocolo_revision()
            clase_eq = arriendo.equipo.__class__.__name__
            self.refrescar_todo()
            messagebox.showinfo(
                "Devolución registrada",
                f"Se restituyeron {arriendo.cantidad} unidad(es) de '{arriendo.equipo.nombre}'.\n\n"
                f"Protocolo de revisión ({clase_eq}):\n{protocolo}",
            )
        except ReglaNegocioError as err:
            messagebox.showerror("Operación rechazada", str(err))

    # ==================== PESTAÑA GRÁFICOS ====================

    def _construir_tab_graficos(self):
        cabecera = ttk.Frame(self.tab_graficos)
        cabecera.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(
            cabecera,
            text="Reportes basados en operaciones reales registradas en SQLite",
            font=("Segoe UI", 10, "bold"),
        ).pack(side=tk.LEFT)

        tb.Button(
            cabecera,
            text="Actualizar gráficos",
            bootstyle="info",
            command=self._actualizar_graficos,
        ).pack(side=tk.RIGHT)

        self.contenedor_graficos = ttk.Frame(self.tab_graficos)
        self.contenedor_graficos.pack(fill=tk.BOTH, expand=True)

    def _actualizar_graficos(self):
        if self.canvas_graficos is not None:
            self.canvas_graficos.get_tk_widget().destroy()
            self.canvas_graficos = None

        fig = charts.crear_figura_reportes()
        self.canvas_graficos = FigureCanvasTkAgg(fig, master=self.contenedor_graficos)
        self.canvas_graficos.draw()
        self.canvas_graficos.get_tk_widget().pack(fill=tk.BOTH, expand=True)