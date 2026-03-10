import sqlite3

DB_PATH = "gastos.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS movimientos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                monto REAL NOT NULL,
                tipo TEXT NOT NULL,
                categoria TEXT NOT NULL,
                descripcion TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS dolares(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                monto REAL NOT NULL,
                precio_por_unidad REAL NOT NULL,
                tipo TEXT NOT NULL,
                movimiento_id INTEGER,
                FOREIGN KEY (movimiento_id) REFERENCES movimientos(id) ON DELETE CASCADE
            )
        """)


def insert_movimiento(fecha, monto, tipo, categoria, descripcion):
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO movimientos (fecha, monto, tipo, categoria, descripcion)
            VALUES (?, ?, ?, ?, ?)
        """, (fecha, monto, tipo, categoria, descripcion))
        return cur.lastrowid


def load_movimientos(tipo):
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT id, fecha, monto, categoria, descripcion
            FROM movimientos
            WHERE tipo = ?
            ORDER BY fecha DESC, id DESC
        """, (tipo,))
        return cur.fetchall()


def load_movimientos_por_fecha(tipo, fecha_inicio=None, fecha_fin=None):
    with get_conn() as conn:
        query = """
            SELECT id, fecha, monto, categoria, descripcion
            FROM movimientos
            WHERE tipo = ?
        """
        params = [tipo]

        if fecha_inicio:
            query += " AND fecha >= ?"
            params.append(fecha_inicio)

        if fecha_fin:
            query += " AND fecha <= ?"
            params.append(fecha_fin)

        query += " ORDER BY fecha DESC, id DESC"

        cur = conn.execute(query, params)
        return cur.fetchall()


def delete_movimiento(mov_id):
    with get_conn() as conn:
        conn.execute("""
            DELETE FROM movimientos
            WHERE id = ?
        """, (mov_id,))


def update_movimiento(mov_id, fecha, monto, categoria, descripcion):
    with get_conn() as conn:
        conn.execute("""
            UPDATE movimientos
            SET fecha = ?, monto = ?, categoria = ?, descripcion = ?
            WHERE id = ?
        """, (fecha, monto, categoria, descripcion, mov_id))


def get_balance_total():
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT
                SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END),
                SUM(CASE WHEN tipo = 'gasto' THEN monto ELSE 0 END)
            FROM movimientos
        """)
        ingresos, gastos = cur.fetchone()
        ingresos = ingresos or 0
        gastos = gastos or 0
        return ingresos, gastos, ingresos - gastos


def get_balance_por_fecha(fecha_inicio=None, fecha_fin=None):
    with get_conn() as conn:
        query = """
            SELECT
                SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END),
                SUM(CASE WHEN tipo = 'gasto' THEN monto ELSE 0 END)
            FROM movimientos
            WHERE 1=1
        """
        params = []

        if fecha_inicio:
            query += " AND fecha >= ?"
            params.append(fecha_inicio)

        if fecha_fin:
            query += " AND fecha <= ?"
            params.append(fecha_fin)

        cur = conn.execute(query, params)
        ingresos, gastos = cur.fetchone()
        ingresos = ingresos or 0
        gastos = gastos or 0
        return ingresos, gastos, ingresos - gastos


def get_totales_por_categoria(tipo):
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT categoria, SUM(monto)
            FROM movimientos
            WHERE tipo = ?
            GROUP BY categoria
            ORDER BY SUM(monto) DESC
        """, (tipo,))
        return cur.fetchall()


def get_totales_por_categoria_filtrado(tipo, fecha_inicio=None, fecha_fin=None):
    with get_conn() as conn:
        query = """
            SELECT categoria, SUM(monto)
            FROM movimientos
            WHERE tipo = ?
        """
        params = [tipo]

        if fecha_inicio:
            query += " AND fecha >= ?"
            params.append(fecha_inicio)

        if fecha_fin:
            query += " AND fecha <= ?"
            params.append(fecha_fin)

        query += """
            GROUP BY categoria
            ORDER BY SUM(monto) DESC
        """

        cur = conn.execute(query, params)
        return cur.fetchall()


def insert_operacion_dolar(fecha, monto_usd, precio_por_unidad, tipo_dolar):
    with get_conn() as conn:
        monto_pesos = monto_usd * precio_por_unidad

        if tipo_dolar == "compra":
            tipo_mov = "gasto"
            descripcion = f"Compra de {monto_usd:.2f} USD a ${precio_por_unidad:.2f} por unidad"
        else:
            tipo_mov = "ingreso"
            descripcion = f"Venta de {monto_usd:.2f} USD a ${precio_por_unidad:.2f} por unidad"

        cur = conn.execute("""
            INSERT INTO movimientos (fecha, monto, tipo, categoria, descripcion)
            VALUES (?, ?, ?, ?, ?)
        """, (fecha, monto_pesos, tipo_mov, "DOLARES", descripcion))

        movimiento_id = cur.lastrowid

        conn.execute("""
            INSERT INTO dolares (fecha, monto, precio_por_unidad, tipo, movimiento_id)
            VALUES (?, ?, ?, ?, ?)
        """, (fecha, monto_usd, precio_por_unidad, tipo_dolar, movimiento_id))


def load_dolares(tipo):
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT id, fecha, monto, precio_por_unidad, tipo, movimiento_id
            FROM dolares
            WHERE tipo = ?
            ORDER BY fecha DESC, id DESC
        """, (tipo,))
        return cur.fetchall()


def load_dolares_por_fecha(tipo, fecha_inicio=None, fecha_fin=None):
    with get_conn() as conn:
        query = """
            SELECT id, fecha, monto, precio_por_unidad, tipo, movimiento_id
            FROM dolares
            WHERE tipo = ?
        """
        params = [tipo]

        if fecha_inicio:
            query += " AND fecha >= ?"
            params.append(fecha_inicio)

        if fecha_fin:
            query += " AND fecha <= ?"
            params.append(fecha_fin)

        query += " ORDER BY fecha DESC, id DESC"

        cur = conn.execute(query, params)
        return cur.fetchall()


def load_all_dolares():
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT id, fecha, monto, precio_por_unidad, tipo, movimiento_id
            FROM dolares
            ORDER BY fecha DESC, id DESC
        """)
        return cur.fetchall()


def load_all_dolares_por_fecha(fecha_inicio=None, fecha_fin=None):
    with get_conn() as conn:
        query = """
            SELECT id, fecha, monto, precio_por_unidad, tipo, movimiento_id
            FROM dolares
            WHERE 1=1
        """
        params = []

        if fecha_inicio:
            query += " AND fecha >= ?"
            params.append(fecha_inicio)

        if fecha_fin:
            query += " AND fecha <= ?"
            params.append(fecha_fin)

        query += " ORDER BY fecha DESC, id DESC"

        cur = conn.execute(query, params)
        return cur.fetchall()


def delete_operacion_dolar(dolar_id):
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT movimiento_id
            FROM dolares
            WHERE id = ?
        """, (dolar_id,))
        fila = cur.fetchone()

        if not fila:
            return

        movimiento_id = fila[0]

        conn.execute("DELETE FROM dolares WHERE id = ?", (dolar_id,))
        conn.execute("DELETE FROM movimientos WHERE id = ?", (movimiento_id,))


def update_operacion_dolar(dolar_id, fecha, monto_usd, precio_por_unidad, tipo_dolar):
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT movimiento_id
            FROM dolares
            WHERE id = ?
        """, (dolar_id,))
        fila = cur.fetchone()

        if not fila:
            return

        movimiento_id = fila[0]
        monto_pesos = monto_usd * precio_por_unidad

        if tipo_dolar == "compra":
            tipo_mov = "gasto"
            descripcion = f"Compra de {monto_usd:.2f} USD a ${precio_por_unidad:.2f} por unidad"
        else:
            tipo_mov = "ingreso"
            descripcion = f"Venta de {monto_usd:.2f} USD a ${precio_por_unidad:.2f} por unidad"

        conn.execute("""
            UPDATE dolares
            SET fecha = ?, monto = ?, precio_por_unidad = ?, tipo = ?
            WHERE id = ?
        """, (fecha, monto_usd, precio_por_unidad, tipo_dolar, dolar_id))

        conn.execute("""
            UPDATE movimientos
            SET fecha = ?, monto = ?, tipo = ?, categoria = ?, descripcion = ?
            WHERE id = ?
        """, (fecha, monto_pesos, tipo_mov, "DOLARES", descripcion, movimiento_id))