import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkcalendar import DateEntry

from database import (
    init_db,
    insert_movimiento,
    load_movimientos,
    load_movimientos_por_fecha,
    delete_movimiento,
    update_movimiento,
    get_balance_total,
    get_balance_por_fecha,
    get_totales_por_categoria,
    get_totales_por_categoria_filtrado,
    load_dolares,
    load_all_dolares,
    load_all_dolares_por_fecha,
    insert_operacion_dolar,
    update_operacion_dolar,
    delete_operacion_dolar,
)

CATEGORIAS_GASTOS = ["Comida", "Transporte", "Servicios", "Ocio"]
CATEGORIAS_INGRESOS = ["Salario", "Freelance"]


def validar_fecha(fecha):
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def obtener_rango_fecha(opcion_combo, fecha_manual):
    hoy = datetime.today().date()

    if opcion_combo == "Hoy":
        return hoy.strftime("%Y-%m-%d"), hoy.strftime("%Y-%m-%d")
    elif opcion_combo == "Última semana":
        desde = hoy - timedelta(days=7)
        return desde.strftime("%Y-%m-%d"), hoy.strftime("%Y-%m-%d")
    elif opcion_combo == "Último mes":
        desde = hoy - timedelta(days=30)
        return desde.strftime("%Y-%m-%d"), hoy.strftime("%Y-%m-%d")
    elif opcion_combo == "Último año":
        desde = hoy - timedelta(days=365)
        return desde.strftime("%Y-%m-%d"), hoy.strftime("%Y-%m-%d")
    elif opcion_combo == "Fecha específica":
        fecha = datetime.strptime(fecha_manual, "%Y-%m-%d").date()
        return fecha.strftime("%Y-%m-%d"), fecha.strftime("%Y-%m-%d")
    else:
        return None, None


def build_tab(parent, tipo: str):
    frame = ttk.Frame(parent, padding=12)

    ttk.Label(frame, text=tipo.title(), font=("Segoe UI", 14, "bold")).grid(
        row=0, column=0, sticky="w"
    )

    form = ttk.LabelFrame(frame, text="Nuevo movimiento", padding=10)
    form.grid(row=1, column=0, sticky="ew", pady=(10, 10))

    categorias_actuales = CATEGORIAS_INGRESOS if tipo == "ingresos" else CATEGORIAS_GASTOS

    fecha_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
    monto_var = tk.StringVar()
    categoria_var = tk.StringVar(value=categorias_actuales[0] if categorias_actuales else "")
    descripcion_var = tk.StringVar()

    form_vars = {
        "fecha": fecha_var,
        "monto": monto_var,
        "categoria": categoria_var,
        "descripcion": descripcion_var
    }

    tipo_db = "ingreso" if tipo == "ingresos" else "gasto"
    filtro_var = tk.StringVar(value="Hoy")

    def refrescar_tabla(fecha_inicio=None, fecha_fin=None):
        for item in tree.get_children():
            tree.delete(item)

        if fecha_inicio or fecha_fin:
            movimientos = load_movimientos_por_fecha(tipo_db, fecha_inicio, fecha_fin)
        else:
            movimientos = load_movimientos(tipo_db)

        for mov in movimientos:
            if mov[3] == "DOLARES":
                accion = "Movimiento dólar"
            else:
                accion = "Editar | Borrar"

            tree.insert(
                "",
                "end",
                values=(mov[0], mov[1], f"{mov[2]:.2f}", mov[3], mov[4], accion)
            )

    def agregar():
        fecha = fecha_var.get().strip()
        monto = monto_var.get().strip()
        categoria = categoria_var.get().strip()
        descripcion = descripcion_var.get().strip()

        if not fecha:
            messagebox.showerror("Error", "La fecha es obligatoria")
            return

        if not validar_fecha(fecha):
            messagebox.showerror("Error", "La fecha debe tener formato YYYY-MM-DD")
            return

        if not categoria:
            messagebox.showerror("Error", "La categoría es obligatoria")
            return

        try:
            monto = float(monto)
        except ValueError:
            messagebox.showerror("Error", "El monto debe ser un número")
            return

        if monto <= 0:
            messagebox.showerror("Error", "El monto debe ser positivo")
            return

        insert_movimiento(fecha, monto, tipo_db, categoria, descripcion)

        fecha_entry.set_date(datetime.today())
        fecha_var.set(datetime.today().strftime("%Y-%m-%d"))
        monto_var.set("")
        if categorias_actuales:
            categoria_var.set(categorias_actuales[0])
        descripcion_var.set("")

        refrescar_tabla()

    def editar_movimiento(id_mov, fecha, monto, categoria, descripcion):
        edit_win = tk.Toplevel(frame)
        edit_win.title("Editar movimiento")
        edit_win.geometry("420x250")
        edit_win.resizable(False, False)

        fecha_edit_var = tk.StringVar(value=fecha)
        monto_edit_var = tk.StringVar(value=str(monto))
        categoria_edit_var = tk.StringVar(value=categoria)
        descripcion_edit_var = tk.StringVar(value=descripcion)

        ttk.Label(edit_win, text="Fecha").grid(row=0, column=0, padx=10, pady=8, sticky="w")
        fecha_edit_entry = DateEntry(
            edit_win,
            textvariable=fecha_edit_var,
            width=12,
            background="darkblue",
            foreground="white",
            borderwidth=2,
            date_pattern="yyyy-mm-dd"
        )
        fecha_edit_entry.grid(row=0, column=1, padx=10, pady=8, sticky="ew")
        fecha_edit_entry.set_date(datetime.strptime(fecha, "%Y-%m-%d"))

        ttk.Label(edit_win, text="Monto").grid(row=1, column=0, padx=10, pady=8, sticky="w")
        ttk.Entry(edit_win, textvariable=monto_edit_var).grid(row=1, column=1, padx=10, pady=8, sticky="ew")

        ttk.Label(edit_win, text="Categoría").grid(row=2, column=0, padx=10, pady=8, sticky="w")
        ttk.Combobox(
            edit_win,
            textvariable=categoria_edit_var,
            values=categorias_actuales,
            state="readonly"
        ).grid(row=2, column=1, padx=10, pady=8, sticky="ew")

        ttk.Label(edit_win, text="Descripción").grid(row=3, column=0, padx=10, pady=8, sticky="w")
        ttk.Entry(edit_win, textvariable=descripcion_edit_var).grid(row=3, column=1, padx=10, pady=8, sticky="ew")

        edit_win.columnconfigure(1, weight=1)

        def guardar_cambios():
            fecha_nueva = fecha_edit_var.get().strip()
            monto_nuevo = monto_edit_var.get().strip()
            categoria_nueva = categoria_edit_var.get().strip()
            descripcion_nueva = descripcion_edit_var.get().strip()

            if not fecha_nueva:
                messagebox.showerror("Error", "La fecha es obligatoria")
                return

            if not validar_fecha(fecha_nueva):
                messagebox.showerror("Error", "La fecha debe tener formato YYYY-MM-DD")
                return

            if not categoria_nueva:
                messagebox.showerror("Error", "La categoría es obligatoria")
                return

            try:
                monto_nuevo = float(monto_nuevo)
            except ValueError:
                messagebox.showerror("Error", "El monto debe ser un número")
                return

            if monto_nuevo <= 0:
                messagebox.showerror("Error", "El monto debe ser positivo")
                return

            update_movimiento(id_mov, fecha_nueva, monto_nuevo, categoria_nueva, descripcion_nueva)
            refrescar_tabla()
            edit_win.destroy()

        ttk.Button(edit_win, text="Guardar", command=guardar_cambios).grid(
            row=4, column=1, padx=10, pady=15, sticky="e"
        )

    def eliminar_movimiento(id_mov):
        if messagebox.askyesno("Confirmar", "¿Estás seguro de eliminar este movimiento?"):
            delete_movimiento(id_mov)
            refrescar_tabla()

    def manejar_click_tree(event):
        fila = tree.identify_row(event.y)

        if not fila:
            return

        columna = tree.identify_column(event.x)
        if columna != "#6":
            return

        valores = tree.item(fila, "values")
        id_mov = valores[0]

        bbox = tree.bbox(fila, "#6")
        if not bbox:
            return

        if valores[3] == "DOLARES":
            messagebox.showinfo(
                "Información",
                "Este movimiento corresponde a una operación con dólares y no se puede editar ni eliminar desde aquí."
            )
            return

        x, y, w, h = bbox
        mitad = x + w / 2

        if event.x < mitad:
            editar_movimiento(id_mov, valores[1], valores[2], valores[3], valores[4])
        else:
            eliminar_movimiento(id_mov)

    def abrir_categorias():
        win = tk.Toplevel(frame)
        win.title("Categorías")
        win.geometry("300x300")

        lista = categorias_actuales

        listbox = tk.Listbox(win)
        listbox.pack(fill="both", expand=True, padx=10, pady=10)

        for c in lista:
            listbox.insert("end", c)

        entry = ttk.Entry(win)
        entry.pack(fill="x", padx=10, pady=(0, 10))

        def agregar_cat():
            nueva = entry.get().strip()
            if nueva and nueva not in lista:
                lista.append(nueva)
                listbox.insert("end", nueva)
                categoria_var.set(nueva)
                combo_categoria["values"] = lista
                entry.delete(0, "end")

        ttk.Button(win, text="Agregar", command=agregar_cat).pack(pady=(0, 10))

    ttk.Label(form, text="Fecha").grid(row=0, column=0, sticky="w", pady=5)

    fecha_entry = DateEntry(
        form,
        textvariable=fecha_var,
        width=12,
        background="darkblue",
        foreground="white",
        borderwidth=2,
        date_pattern="yyyy-mm-dd"
    )
    fecha_entry.grid(row=0, column=1, sticky="ew", pady=5)
    fecha_entry.set_date(datetime.today())

    ttk.Label(form, text="Monto").grid(row=1, column=0, sticky="w", pady=5)
    ttk.Entry(form, textvariable=monto_var).grid(row=1, column=1, sticky="ew", pady=5)

    ttk.Label(form, text="Categoría").grid(row=2, column=0, sticky="w", pady=5)
    combo_categoria = ttk.Combobox(
        form,
        textvariable=categoria_var,
        values=categorias_actuales,
        state="readonly"
    )
    combo_categoria.grid(row=2, column=1, sticky="ew", pady=5)

    ttk.Label(form, text="Descripción").grid(row=3, column=0, sticky="w", pady=5)
    ttk.Entry(form, textvariable=descripcion_var).grid(row=3, column=1, sticky="ew", pady=5)

    ttk.Button(form, text="Gestionar categorías", command=abrir_categorias).grid(row=4, column=0, sticky="w")
    ttk.Button(form, text="Agregar", command=agregar).grid(row=4, column=1, sticky="e", pady=(10, 0))
    form.columnconfigure(1, weight=1)

    def buscar_por_fecha():
        opcion = filtro_var.get()
        fecha_manual = calendario.get_date().strftime("%Y-%m-%d")
        fecha_desde, fecha_hasta = obtener_rango_fecha(opcion, fecha_manual)
        refrescar_tabla(fecha_desde, fecha_hasta)

    def limpiar_filtro():
        filtro_var.set("Hoy")
        actualizar_estado_calendario()
        refrescar_tabla()

    def actualizar_estado_calendario(event=None):
        if filtro_var.get() == "Fecha específica":
            calendario.configure(state="normal")
        else:
            calendario.configure(state="disabled")

    filtros = ttk.LabelFrame(frame, text="Buscar por fecha", padding=10)
    filtros.grid(row=2, column=0, sticky="ew", pady=(0, 10))

    ttk.Label(filtros, text="Rango").grid(row=0, column=0, padx=5, pady=5, sticky="w")

    combo_filtro = ttk.Combobox(
        filtros,
        textvariable=filtro_var,
        values=["Hoy", "Última semana", "Último mes", "Último año", "Fecha específica"],
        state="readonly",
        width=18
    )
    combo_filtro.grid(row=0, column=1, padx=5, pady=5)
    combo_filtro.bind("<<ComboboxSelected>>", actualizar_estado_calendario)

    ttk.Label(filtros, text="Fecha").grid(row=0, column=2, padx=5, pady=5, sticky="w")

    calendario = DateEntry(
        filtros,
        width=12,
        background="darkblue",
        foreground="white",
        borderwidth=2,
        date_pattern="yyyy-mm-dd"
    )
    calendario.grid(row=0, column=3, padx=5, pady=5)

    ttk.Button(filtros, text="Buscar", command=buscar_por_fecha).grid(row=0, column=4, padx=5, pady=5)
    ttk.Button(filtros, text="Limpiar", command=limpiar_filtro).grid(row=0, column=5, padx=5, pady=5)

    actualizar_estado_calendario()

    table = ttk.LabelFrame(frame, text="Movimientos", padding=10)
    table.grid(row=3, column=0, sticky="nsew")

    tree = ttk.Treeview(
        table,
        columns=("id", "fecha", "monto", "categoria", "descripcion", "accion"),
        show="headings"
    )
    tree.heading("id", text="ID")
    tree.heading("fecha", text="Fecha")
    tree.heading("monto", text="Monto")
    tree.heading("categoria", text="Categoría")
    tree.heading("descripcion", text="Descripción")
    tree.heading("accion", text="Acción")
    tree.grid(row=0, column=0, sticky="nsew")

    table.columnconfigure(0, weight=1)
    table.rowconfigure(0, weight=1)

    tree.column("id", width=0, stretch=False)
    tree.column("fecha", anchor="center", width=120)
    tree.column("monto", anchor="center", width=100)
    tree.column("categoria", anchor="center", width=140)
    tree.column("descripcion", anchor="center", width=220)
    tree.column("accion", anchor="center", width=140)

    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(3, weight=1)

    tree.bind("<Button-1>", manejar_click_tree)

    refrescar_tabla()

    return frame, form, table, form_vars, tree, refrescar_tabla


def build_balance_tab(parent):
    frame = ttk.Frame(parent, padding=12)
    filtro_var = tk.StringVar(value="Hoy")

    ttk.Label(frame, text="Balance", font=("Segoe UI", 16, "bold")).grid(
        row=0, column=0, columnspan=3, pady=(0, 15)
    )

    filtros = ttk.LabelFrame(frame, text="Buscar por fecha", padding=10)
    filtros.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10))

    ttk.Label(filtros, text="Rango").grid(row=0, column=0, padx=5, pady=5, sticky="w")

    combo_filtro = ttk.Combobox(
        filtros,
        textvariable=filtro_var,
        values=["Hoy", "Última semana", "Último mes", "Último año", "Fecha específica"],
        state="readonly",
        width=18
    )
    combo_filtro.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(filtros, text="Fecha").grid(row=0, column=2, padx=5, pady=5, sticky="w")

    calendario = DateEntry(
        filtros,
        width=12,
        background="darkblue",
        foreground="white",
        borderwidth=2,
        date_pattern="yyyy-mm-dd"
    )
    calendario.grid(row=0, column=3, padx=5, pady=5)

    ingresos_frame = ttk.LabelFrame(frame, text="Ingresos por categoría", padding=10)
    ingresos_frame.grid(row=2, column=0, sticky="nsew", padx=10)

    center_frame = ttk.Frame(frame, padding=10)
    center_frame.grid(row=2, column=1, sticky="nsew", padx=10)

    gastos_frame = ttk.LabelFrame(frame, text="Gastos por categoría", padding=10)
    gastos_frame.grid(row=2, column=2, sticky="nsew", padx=10)

    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)
    frame.columnconfigure(2, weight=1)
    frame.rowconfigure(2, weight=1)

    ingresos_label = ttk.Label(center_frame, text="Ingresos: $ 0.00", font=("Segoe UI", 12))
    ingresos_label.pack(pady=(20, 10))

    balance_label = ttk.Label(center_frame, text="$ 0.00", font=("Segoe UI", 24, "bold"))
    balance_label.pack(pady=10)

    ttk.Label(center_frame, text="Balance total", font=("Segoe UI", 12)).pack()

    gastos_label = ttk.Label(center_frame, text="Gastos: $ 0.00", font=("Segoe UI", 12))
    gastos_label.pack(pady=(10, 20))

    def dibujar_torta(chart_frame, datos, titulo):
        for widget in chart_frame.winfo_children():
            widget.destroy()

        if not datos:
            ttk.Label(chart_frame, text="Sin datos").pack(expand=True)
            return

        labels = [fila[0] for fila in datos]
        valores = [fila[1] for fila in datos]

        fig = Figure(figsize=(4, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.pie(valores, labels=labels, autopct="%1.1f%%")
        ax.set_title(titulo)

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def refrescar_balance(fecha_desde=None, fecha_hasta=None):
        if fecha_desde or fecha_hasta:
            ingresos, gastos, balance = get_balance_por_fecha(fecha_desde, fecha_hasta)
            datos_ingresos = get_totales_por_categoria_filtrado("ingreso", fecha_desde, fecha_hasta)
            datos_gastos = get_totales_por_categoria_filtrado("gasto", fecha_desde, fecha_hasta)
        else:
            ingresos, gastos, balance = get_balance_total()
            datos_ingresos = get_totales_por_categoria("ingreso")
            datos_gastos = get_totales_por_categoria("gasto")

        ingresos_label.config(text=f"Ingresos: $ {ingresos:.2f}")
        gastos_label.config(text=f"Gastos: $ {gastos:.2f}")
        balance_label.config(text=f"$ {balance:.2f}")

        dibujar_torta(ingresos_frame, datos_ingresos, "Ingresos")
        dibujar_torta(gastos_frame, datos_gastos, "Gastos")

    def buscar_balance():
        opcion = filtro_var.get()
        fecha_manual = calendario.get_date().strftime("%Y-%m-%d")
        fecha_desde, fecha_hasta = obtener_rango_fecha(opcion, fecha_manual)
        refrescar_balance(fecha_desde, fecha_hasta)

    def limpiar_balance():
        filtro_var.set("Hoy")
        actualizar_estado_calendario()
        refrescar_balance()

    def actualizar_estado_calendario(event=None):
        if filtro_var.get() == "Fecha específica":
            calendario.configure(state="normal")
        else:
            calendario.configure(state="disabled")

    combo_filtro.bind("<<ComboboxSelected>>", actualizar_estado_calendario)

    ttk.Button(filtros, text="Buscar", command=buscar_balance).grid(row=0, column=4, padx=5, pady=5)
    ttk.Button(filtros, text="Limpiar", command=limpiar_balance).grid(row=0, column=5, padx=5, pady=5)

    actualizar_estado_calendario()
    refrescar_balance()

    return frame, refrescar_balance


def build_tab_dolares(parent, refresh_all):
    frame = ttk.Frame(parent, padding=12)

    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)
    frame.columnconfigure(2, weight=1)
    frame.rowconfigure(3, weight=1)

    ttk.Label(frame, text="Compra / Venta de dólares", font=("Segoe UI", 14, "bold")).grid(
        row=0, column=0, columnspan=3, sticky="w", pady=(0, 10)
    )

    compra_frame = ttk.LabelFrame(frame, text="Compré dólares", padding=10)
    compra_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8))

    balance_frame = ttk.LabelFrame(frame, text="Balance", padding=10)
    balance_frame.grid(row=1, column=1, sticky="nsew", padx=8)

    venta_frame = ttk.LabelFrame(frame, text="Vendí dólares", padding=10)
    venta_frame.grid(row=1, column=2, sticky="nsew", padx=(8, 0))

    monto_compra_var = tk.DoubleVar()
    precio_compra_var = tk.DoubleVar()
    monto_venta_var = tk.DoubleVar()
    precio_venta_var = tk.DoubleVar()

    filtro_var = tk.StringVar(value="Hoy")

    def limpiar_compra():
        fecha_compra_entry.set_date(datetime.today())
        monto_compra_var.set(0.0)
        precio_compra_var.set(0.0)

    def limpiar_venta():
        fecha_venta_entry.set_date(datetime.today())
        monto_venta_var.set(0.0)
        precio_venta_var.set(0.0)

    def actualizar_balance():
        compras = load_dolares("compra")
        ventas = load_dolares("venta")

        total_usd_comprados = sum(fila[2] for fila in compras)
        total_usd_vendidos = sum(fila[2] for fila in ventas)

        total_pesos_compras = sum(fila[2] * fila[3] for fila in compras)
        total_pesos_ventas = sum(fila[2] * fila[3] for fila in ventas)

        saldo_usd = total_usd_comprados - total_usd_vendidos
        saldo_pesos = total_pesos_ventas - total_pesos_compras

        lbl_usd.config(text=f"Saldo en USD: {saldo_usd:.2f}")
        lbl_compras.config(text=f"Total comprado: USD {total_usd_comprados:.2f}")
        lbl_ventas.config(text=f"Total vendido: USD {total_usd_vendidos:.2f}")
        lbl_pesos_compra.config(text=f"Pesos usados en compras: ${total_pesos_compras:,.2f}")
        lbl_pesos_venta.config(text=f"Pesos recibidos por ventas: ${total_pesos_ventas:,.2f}")
        lbl_resultado.config(text=f"Diferencia neta en pesos: ${saldo_pesos:,.2f}")

    def refrescar_historial(fecha_inicio=None, fecha_fin=None):
        tree_dolares.delete(*tree_dolares.get_children())

        if fecha_inicio or fecha_fin:
            movimientos = load_all_dolares_por_fecha(fecha_inicio, fecha_fin)
        else:
            movimientos = load_all_dolares()

        for mov in movimientos:
            dolar_id = mov[0]
            fecha = mov[1]
            monto = mov[2]
            precio = mov[3]
            tipo = mov[4]
            total_pesos = monto * precio

            tree_dolares.insert(
                "",
                "end",
                values=(
                    dolar_id,
                    fecha,
                    "Compra" if tipo == "compra" else "Venta",
                    f"{monto:.2f}",
                    f"${precio:.2f}",
                    f"${total_pesos:,.2f}",
                    "Editar | Borrar"
                ),
                tags=(tipo,)
            )

    def guardar_compra():
        fecha = fecha_compra_entry.get().strip()
        monto = monto_compra_var.get()
        precio = precio_compra_var.get()

        if not fecha:
            messagebox.showerror("Error", "La fecha es obligatoria.")
            return

        if not validar_fecha(fecha):
            messagebox.showerror("Error", "La fecha no tiene un formato válido.")
            return

        if monto <= 0:
            messagebox.showerror("Error", "El monto en USD debe ser mayor a 0.")
            return

        if precio <= 0:
            messagebox.showerror("Error", "El precio por unidad debe ser mayor a 0.")
            return

        insert_operacion_dolar(fecha, monto, precio, "compra")
        limpiar_compra()
        actualizar_balance()
        refrescar_historial()
        refresh_all()
        messagebox.showinfo("Éxito", "Compra registrada correctamente.")

    def guardar_venta():
        fecha = fecha_venta_entry.get().strip()
        monto = monto_venta_var.get()
        precio = precio_venta_var.get()

        if not fecha:
            messagebox.showerror("Error", "La fecha es obligatoria.")
            return

        if not validar_fecha(fecha):
            messagebox.showerror("Error", "La fecha no tiene un formato válido.")
            return

        if monto <= 0:
            messagebox.showerror("Error", "El monto en USD debe ser mayor a 0.")
            return

        if precio <= 0:
            messagebox.showerror("Error", "El precio por unidad debe ser mayor a 0.")
            return

        insert_operacion_dolar(fecha, monto, precio, "venta")
        limpiar_venta()
        actualizar_balance()
        refrescar_historial()
        refresh_all()
        messagebox.showinfo("Éxito", "Venta registrada correctamente.")

    def editar_dolar(dolar_id, fecha, tipo, monto, precio):
        edit_win = tk.Toplevel(frame)
        edit_win.title("Editar operación en dólares")
        edit_win.geometry("420x260")
        edit_win.resizable(False, False)

        fecha_var = tk.StringVar(value=fecha)
        tipo_var = tk.StringVar(value=tipo)
        monto_var = tk.StringVar(value=str(monto))
        precio_var = tk.StringVar(value=str(precio))

        ttk.Label(edit_win, text="Fecha").grid(row=0, column=0, padx=10, pady=8, sticky="w")
        fecha_entry = DateEntry(
            edit_win,
            textvariable=fecha_var,
            width=12,
            background="darkblue",
            foreground="white",
            borderwidth=2,
            date_pattern="yyyy-mm-dd"
        )
        fecha_entry.grid(row=0, column=1, padx=10, pady=8, sticky="ew")
        fecha_entry.set_date(datetime.strptime(fecha, "%Y-%m-%d"))

        ttk.Label(edit_win, text="Tipo").grid(row=1, column=0, padx=10, pady=8, sticky="w")
        ttk.Combobox(
            edit_win,
            textvariable=tipo_var,
            values=["compra", "venta"],
            state="readonly"
        ).grid(row=1, column=1, padx=10, pady=8, sticky="ew")

        ttk.Label(edit_win, text="Monto USD").grid(row=2, column=0, padx=10, pady=8, sticky="w")
        ttk.Entry(edit_win, textvariable=monto_var).grid(row=2, column=1, padx=10, pady=8, sticky="ew")

        ttk.Label(edit_win, text="Precio por unidad").grid(row=3, column=0, padx=10, pady=8, sticky="w")
        ttk.Entry(edit_win, textvariable=precio_var).grid(row=3, column=1, padx=10, pady=8, sticky="ew")

        edit_win.columnconfigure(1, weight=1)

        def guardar_cambios():
            fecha_nueva = fecha_var.get().strip()
            tipo_nuevo = tipo_var.get().strip()
            monto_nuevo = monto_var.get().strip()
            precio_nuevo = precio_var.get().strip()

            if not fecha_nueva:
                messagebox.showerror("Error", "La fecha es obligatoria")
                return

            if not validar_fecha(fecha_nueva):
                messagebox.showerror("Error", "La fecha debe tener formato YYYY-MM-DD")
                return

            try:
                monto_nuevo = float(monto_nuevo)
                precio_nuevo = float(precio_nuevo)
            except ValueError:
                messagebox.showerror("Error", "Monto y precio deben ser numéricos")
                return

            if monto_nuevo <= 0 or precio_nuevo <= 0:
                messagebox.showerror("Error", "Monto y precio deben ser mayores a 0")
                return

            update_operacion_dolar(dolar_id, fecha_nueva, monto_nuevo, precio_nuevo, tipo_nuevo)
            actualizar_balance()
            refrescar_historial()
            refresh_all()
            edit_win.destroy()

        ttk.Button(edit_win, text="Guardar", command=guardar_cambios).grid(
            row=4, column=1, padx=10, pady=15, sticky="e"
        )

    def eliminar_dolar_ui(dolar_id):
        if messagebox.askyesno("Confirmar", "¿Estás seguro de eliminar esta operación en dólares?"):
            delete_operacion_dolar(dolar_id)
            actualizar_balance()
            refrescar_historial()
            refresh_all()

    def manejar_click_tree_dolares(event):
        fila = tree_dolares.identify_row(event.y)

        if not fila:
            return

        columna = tree_dolares.identify_column(event.x)
        if columna != "#7":
            return

        valores = tree_dolares.item(fila, "values")
        dolar_id = int(valores[0])

        bbox = tree_dolares.bbox(fila, "#7")
        if not bbox:
            return

        x, y, w, h = bbox
        mitad = x + w / 2

        fecha = valores[1]
        tipo = valores[2].lower()
        monto = valores[3]
        precio = valores[4].replace("$", "").replace(",", "")

        if event.x < mitad:
            editar_dolar(dolar_id, fecha, tipo, monto, precio)
        else:
            eliminar_dolar_ui(dolar_id)

    def buscar_dolares_por_fecha():
        opcion = filtro_var.get()
        fecha_manual = calendario_filtro.get_date().strftime("%Y-%m-%d")
        fecha_desde, fecha_hasta = obtener_rango_fecha(opcion, fecha_manual)
        refrescar_historial(fecha_desde, fecha_hasta)

    def limpiar_filtro_dolares():
        filtro_var.set("Hoy")
        actualizar_estado_calendario_dolares()
        refrescar_historial()

    def actualizar_estado_calendario_dolares(event=None):
        if filtro_var.get() == "Fecha específica":
            calendario_filtro.configure(state="normal")
        else:
            calendario_filtro.configure(state="disabled")

    ttk.Label(compra_frame, text="Fecha").grid(row=0, column=0, sticky="w", pady=4)
    fecha_compra_entry = DateEntry(compra_frame, width=18, date_pattern="yyyy-mm-dd")
    fecha_compra_entry.grid(row=0, column=1, sticky="ew", pady=4)

    ttk.Label(compra_frame, text="Monto USD").grid(row=1, column=0, sticky="w", pady=4)
    ttk.Entry(compra_frame, textvariable=monto_compra_var).grid(row=1, column=1, sticky="ew", pady=4)

    ttk.Label(compra_frame, text="Precio por unidad").grid(row=2, column=0, sticky="w", pady=4)
    ttk.Entry(compra_frame, textvariable=precio_compra_var).grid(row=2, column=1, sticky="ew", pady=4)

    ttk.Button(compra_frame, text="Guardar compra", command=guardar_compra).grid(
        row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0)
    )
    compra_frame.columnconfigure(1, weight=1)

    lbl_usd = ttk.Label(balance_frame, text="Saldo en USD: 0.00", font=("Segoe UI", 11, "bold"))
    lbl_usd.grid(row=0, column=0, sticky="w", pady=4)

    lbl_compras = ttk.Label(balance_frame, text="Total comprado: USD 0.00")
    lbl_compras.grid(row=1, column=0, sticky="w", pady=4)

    lbl_ventas = ttk.Label(balance_frame, text="Total vendido: USD 0.00")
    lbl_ventas.grid(row=2, column=0, sticky="w", pady=4)

    lbl_pesos_compra = ttk.Label(balance_frame, text="Pesos usados en compras: $0.00")
    lbl_pesos_compra.grid(row=3, column=0, sticky="w", pady=4)

    lbl_pesos_venta = ttk.Label(balance_frame, text="Pesos recibidos por ventas: $0.00")
    lbl_pesos_venta.grid(row=4, column=0, sticky="w", pady=4)

    lbl_resultado = ttk.Label(balance_frame, text="Diferencia neta en pesos: $0.00")
    lbl_resultado.grid(row=5, column=0, sticky="w", pady=4)

    ttk.Label(venta_frame, text="Fecha").grid(row=0, column=0, sticky="w", pady=4)
    fecha_venta_entry = DateEntry(venta_frame, width=18, date_pattern="yyyy-mm-dd")
    fecha_venta_entry.grid(row=0, column=1, sticky="ew", pady=4)

    ttk.Label(venta_frame, text="Monto USD").grid(row=1, column=0, sticky="w", pady=4)
    ttk.Entry(venta_frame, textvariable=monto_venta_var).grid(row=1, column=1, sticky="ew", pady=4)

    ttk.Label(venta_frame, text="Precio por unidad").grid(row=2, column=0, sticky="w", pady=4)
    ttk.Entry(venta_frame, textvariable=precio_venta_var).grid(row=2, column=1, sticky="ew", pady=4)

    ttk.Button(venta_frame, text="Guardar venta", command=guardar_venta).grid(
        row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0)
    )
    venta_frame.columnconfigure(1, weight=1)

    filtros_frame = ttk.LabelFrame(frame, text="Buscar por fecha", padding=10)
    filtros_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(15, 10))

    ttk.Label(filtros_frame, text="Rango").grid(row=0, column=0, padx=5, pady=5, sticky="w")

    combo_filtro = ttk.Combobox(
        filtros_frame,
        textvariable=filtro_var,
        values=["Hoy", "Última semana", "Último mes", "Último año", "Fecha específica"],
        state="readonly",
        width=18
    )
    combo_filtro.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(filtros_frame, text="Fecha").grid(row=0, column=2, padx=5, pady=5, sticky="w")

    calendario_filtro = DateEntry(
        filtros_frame,
        width=12,
        background="darkblue",
        foreground="white",
        borderwidth=2,
        date_pattern="yyyy-mm-dd"
    )
    calendario_filtro.grid(row=0, column=3, padx=5, pady=5)

    ttk.Button(filtros_frame, text="Buscar", command=buscar_dolares_por_fecha).grid(row=0, column=4, padx=5, pady=5)
    ttk.Button(filtros_frame, text="Limpiar", command=limpiar_filtro_dolares).grid(row=0, column=5, padx=5, pady=5)

    combo_filtro.bind("<<ComboboxSelected>>", actualizar_estado_calendario_dolares)
    actualizar_estado_calendario_dolares()

    historial_frame = ttk.LabelFrame(frame, text="Movimientos en dólares", padding=10)
    historial_frame.grid(row=3, column=0, columnspan=3, sticky="nsew", pady=(0, 10))

    tree_dolares = ttk.Treeview(
        historial_frame,
        columns=("id", "fecha", "tipo", "usd", "precio", "pesos", "accion"),
        show="headings"
    )

    tree_dolares.heading("id", text="ID")
    tree_dolares.heading("fecha", text="Fecha")
    tree_dolares.heading("tipo", text="Tipo")
    tree_dolares.heading("usd", text="USD")
    tree_dolares.heading("precio", text="Precio")
    tree_dolares.heading("pesos", text="Total $")
    tree_dolares.heading("accion", text="Acción")

    tree_dolares.column("id", width=0, stretch=False)
    tree_dolares.column("fecha", anchor="center", width=120)
    tree_dolares.column("tipo", anchor="center", width=100)
    tree_dolares.column("usd", anchor="center", width=100)
    tree_dolares.column("precio", anchor="center", width=120)
    tree_dolares.column("pesos", anchor="center", width=140)
    tree_dolares.column("accion", anchor="center", width=140)

    tree_dolares.pack(fill="both", expand=True)
    tree_dolares.tag_configure("compra", foreground="green")
    tree_dolares.tag_configure("venta", foreground="red")
    tree_dolares.bind("<Button-1>", manejar_click_tree_dolares)

    actualizar_balance()
    refrescar_historial()

    return frame


def main():
    init_db()

    root = tk.Tk()
    root.title("Gestor de gastos")
    root.geometry("1000x650")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    tab_gastos, form_g, table_g, vars_g, tree_g, refrescar_gastos = build_tab(notebook, "gastos")
    tab_ingresos, form_i, table_i, vars_i, tree_i, refrescar_ingresos = build_tab(notebook, "ingresos")
    tab_balance, refrescar_balance = build_balance_tab(notebook)

    def refresh_all():
        refrescar_gastos()
        refrescar_ingresos()
        refrescar_balance()

    tab_dolares = build_tab_dolares(notebook, refresh_all)

    notebook.add(tab_gastos, text="Gastos")
    notebook.add(tab_ingresos, text="Ingresos")
    notebook.add(tab_balance, text="Balance")
    notebook.add(tab_dolares, text="Dólares")

    root.mainloop()


if __name__ == "__main__":
    main()