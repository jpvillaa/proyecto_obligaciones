# Proyecto Obligaciones
# Realizado por Jose Pablo Villa Arango

# Librerias requeridas
# Manipulacion y analisis de datos 
import pandas as pd
# Gestor de base de datos SQLite
import sqlite3
# Generador de API - Fast API
from fastapi import FastAPI
# Declaracion de modelo a partir de la clase para mostrar en la API
from pydantic import BaseModel


# ------------------------------------------------------------------ Parte 1 ------------------------------------------------------------------
# Se debe realizar el desarrollo con el lenguaje de consulta SQL y para esto puede hacer uso de cualquier motor de base de datos.
# En este caso se escoge SQLite para evitar que el usuario final requiera configuraciones adicionales de creaciona de la base datos y conexiones a la misma

# Se toma la tabla de obligaciones clientes y se convierte a DataFrame
obligaciones = pd.read_excel(r'src\Obligaciones_clientes.xlsx',sheet_name='Obligaciones_clientes',header=0)
# Se toma la tabla de tasas y se convierte a DataFrame
tasas = pd.read_excel(r'src\tasas_productos.xlsx',sheet_name='Tasas',header=0)

# Generacion de conexion a la base de datos
# con esto se crea la base de datos en la ruta indicada cada vez que se ejeute el programa y por eso no se cargar la base de datos al repositorio
conexion_db = sqlite3.connect("src/productos.db", check_same_thread=False)
# Generacion del onjeto cursor para ejejcutar los comandos SQL
cursor_db = conexion_db.cursor()
# Creacion de las tablas, donde se debe tener en cuenta la metadata de cada una, para la identificacion de campos y tipos de campos
# para aquellos tipo string se cambia por el varchar mas adeacuado, asi mimso los double se ajustan a decimal para evitar aproximaciones que afecten los calculos
#   Creacion de la tabla obligaciones
cursor_db.execute(
    """
    CREATE TABLE obligaciones(
        radicado INTEGER NOT NULL,
        num_documento INTEGER NOT NULL,
        cod_segm_tasa VARCHAR(5) NOT NULL,
        cod_subsegm_tasa INTEGER NOT NULL,
        cal_interna_tasa VARCHAR(5) NOT NULL,
        id_producto	VARCHAR(50) NOT NULL,
        tipo_id_producto VARCHAR(50) NOT NULL,
        valor_inicial DECIMAL(10,5) NOT NULL,
        fecha_desembolso TIMESTAMP NOT NULL,
        plazo DECIMAL(10,0),
        cod_periodicidad DECIMAL(5,0) NOT NULL,
        periodicidad VARCHAR(15) NOT NULL,
        saldo_deuda DECIMAL(10,10) NOT NULL,
        modalidad VARCHAR(10) NOT NULL,
        tipo_plazo VARCHAR(5) NOT NULL
        );
    """
)
#   Seleccion de indices para mejora en el rendimiento de las consultas
cursor_db.execute("""CREATE INDEX idx_obligaciones_cod_segmento ON obligaciones (cod_segm_tasa);""")
cursor_db.execute("""CREATE INDEX idx_obligaciones_cod_subsegmento ON obligaciones (cod_subsegm_tasa);""")
cursor_db.execute("""CREATE INDEX idx_obligaciones_cal_riesgos ON obligaciones (cal_interna_tasa);""")
#   Creacion de la tabla Tasas
cursor_db.execute(
    """
    CREATE TABLE tasas(
        cod_segmento VARCHAR(5) NOT NULL,
        segmento VARCHAR(30) NOT NULL,
        cod_subsegmento INTEGER NOT NULL,
        calificacion_riesgos VARCHAR(5) NOT NULL,
        tasa_cartera DECIMAL(1,10) NOT NULL,
        tasa_operacion_especifica DECIMAL(1,10) NOT NULL,
        tasa_hipotecario DECIMAL(1,10) NOT NULL,
        tasa_leasing DECIMAL(1,10) NOT NULL,
        tasa_sufi DECIMAL(1,10) NOT NULL,
        tasa_factoring DECIMAL(1,10) NOT NULL,
        tasa_tarjeta DECIMAL(1,10) NOT NULL
        );
    """
)
#   Seleccion de indices para mejora en el rendimiento de las consultas
cursor_db.execute("""CREATE INDEX idx_tasas_cod_segmento ON tasas (cod_segmento);""")
cursor_db.execute("""CREATE INDEX idx_tasas_cod_subsegmento ON tasas (cod_subsegmento);""")
cursor_db.execute("""CREATE INDEX idx_tasas_cal_riesgos ON tasas (calificacion_riesgos);""")
# Ingesta de los datos desde cada DataFrame construido a su tabla respectiva en la base de datos
obligaciones.to_sql('obligaciones', conexion_db, if_exists='append', index=False)
tasas.to_sql('tasas', conexion_db, if_exists='append', index=False)

# como se requiere almacenar algunos datos adicionales, se crean las columnas necesarias y su tipo de dato
# modificacion de la tabla oblicaciones, agregando las columnas producto, tasa, tasa efectiva y valor final  
cursor_db.execute("""ALTER TABLE obligaciones ADD COLUMN producto VARCHAR(25)""")
cursor_db.execute("""ALTER TABLE obligaciones ADD COLUMN tasa DECIMAL(1,10)""")
cursor_db.execute("""ALTER TABLE obligaciones ADD COLUMN tasa_efectiva DECIMAL(1,10)""")
cursor_db.execute("""ALTER TABLE obligaciones ADD COLUMN valor_final DECIMAL(10,5)""")
# Columna producto
# Asignacion del campo de producto a partir de la columna id_producto
cursor_db.execute(
    """
    UPDATE obligaciones
    SET producto=
    (
    CASE 
    WHEN id_producto LIKE '%Tarjeta%' THEN 'tarjeta'
    WHEN id_producto LIKE '%Cartera%' THEN 'cartera'
    WHEN id_producto LIKE '%Operacion_especifica%' THEN 'operacion_especifica'
    WHEN id_producto LIKE '%Sufi%' THEN 'sufi'
    WHEN id_producto LIKE '%Leasing%' THEN 'leasing'
    WHEN id_producto LIKE '%Hipotecario%' THEN 'hipotecario'
    WHEN id_producto LIKE '%Factoring%' THEN 'factoring'
    END
    );
    """
)
# Columna tasa
# Asignacion del campo de tasa a partir del producto, correlacionado a la tabla tasas segun el segmento, subsegmento y calificacion de riesgo
# Bajo terminos de rendiemiento seria mejor mediante INNER JOIN, pero esta funcionalidad no la permite este motor de base de datos
cursor_db.execute(
    """
    UPDATE obligaciones
    SET tasa=
    (
    SELECT
    CASE 
    WHEN producto='tarjeta' THEN tasa_tarjeta
    WHEN producto='cartera' THEN tasa_cartera
    WHEN producto='operacion_especifica' THEN tasa_operacion_especifica
    WHEN producto='sufi' THEN tasa_sufi
    WHEN producto='leasing' THEN tasa_leasing
    WHEN producto='hipotecario' THEN tasa_hipotecario
    WHEN producto='factoring' THEN tasa_factoring
    END
    FROM tasas WHERE cod_segm_tasa = cod_segmento AND cod_subsegm_tasa = cod_subsegmento AND cal_interna_tasa = calificacion_riesgos
    );
    """
)
# Columna tasa_efectiva
# Asignacion del valor de tasa efectiva a partir de la formula suministrada, se realizan algunos procesimientos matematicos para simplificar el proceso
cursor_db.execute("""UPDATE obligaciones SET tasa_efectiva=(POW((1+tasa),(CAST(cod_periodicidad AS DOUBLE)/12))-1);""")
# Columna valor_final
# Asignacion del valor_final a partir del calculo suministrado
cursor_db.execute("""UPDATE obligaciones SET valor_final=tasa_efectiva*valor_inicial;""")

#   Creacion de la tabla obligaciones_clientes_productos para almacenar el resultado del iteral 4
cursor_db.execute(
    """
    CREATE TABLE obligaciones_clientes_productos(
        num_documento INTEGER PRIMARY KEY NOT NULL,
        cantidad_obligaciones INTEGER NOT NULL,
        valor_total DECIMAL(10,5) NOT NULL
        );
    """
)
# Ingesta de los datos con la logica solicitada
# sumar el valor_final de todas las obligaciones por cliente y dejar únicamente las que tenga una cantidad de productos mayor o igual a 2 
cursor_db.execute(
    """
    INSERT INTO obligaciones_clientes_productos
    SELECT num_documento, COUNT(num_documento), SUM(valor_final)
    FROM obligaciones
    GROUP BY num_documento
    HAVING COUNT(num_documento)>=2
    """
)
# Extarccion de la tabla obligaciones con las modificaciones realizadas a archivo de excel
resultado_parte1_obligaciones = pd.read_sql(
    """
    SELECT radicado,num_documento,cod_segm_tasa,cod_subsegm_tasa,cal_interna_tasa,id_producto,tipo_id_producto,valor_inicial,
    fecha_desembolso,plazo,cod_periodicidad,periodicidad,saldo_deuda,modalidad,tipo_plazo,producto,tasa,tasa_efectiva,valor_final 
    FROM obligaciones
    """, conexion_db)
resultado_parte1_obligaciones.to_excel('resultados/parte1_obligaciones.xlsx', index=False)
# Extarccion de la tabla obligaciones_clientes_productos
resultado_parte1_obligaciones_clientes = pd.read_sql(
    """
    SELECT num_documento,cantidad_obligaciones,valor_total 
    FROM obligaciones_clientes_productos ORDER BY cantidad_obligaciones
    """, conexion_db)
resultado_parte1_obligaciones_clientes.to_excel('resultados/parte1_obligaciones_clientes.xlsx', index=False)


# ------------------------------------------------------------------ Parte 2 ------------------------------------------------------------------
# Utilizando el lenguaje programación de Python y usando la librería pandas, se debe realizar todos los ejercicios de la parte 1
# Los DataFrames ya se encuentran creados desde el paso anterior

# Funcion que retorna el producto a partir del campo id_producto, validando si este campo la palabra clave que permite diferenciarlos
# para evitar inconsistencias se convierte ese campo a minusculas para validar
def obtener_producto(row):
    id_producto = row['id_producto'].lower()

    if('tarjeta' in id_producto): 
        return 'tarjeta'
    elif('cartera' in id_producto): 
        return 'cartera'
    elif('operacion_especifica' in id_producto): 
        return 'operacion_especifica'
    elif('sufi' in id_producto): 
        return 'sufi'
    elif('leasing' in id_producto): 
        return 'leasing'
    elif('hipotecario' in id_producto): 
        return 'hipotecario'
    elif('factoring' in id_producto): 
        return 'factoring'
    else:
        return ''

# Funcion que retorna la tasa a partir del campo producto, cuando cumpla con la condicion se retorna la tasa que le corresponde al producto
def obtener_tasa(row):
    producto = row['producto']
    tasa_tarjeta = row['tasa_tarjeta']
    tasa_cartera = row['tasa_cartera']
    tasa_operacion_especifica = row['tasa_operacion_especifica']
    tasa_sufi = row['tasa_sufi']
    tasa_leasing = row['tasa_leasing']
    tasa_hipotecario = row['tasa_hipotecario']
    tasa_factoring = row['tasa_factoring']

    if(producto=='tarjeta'): 
        return tasa_tarjeta
    elif(producto=='cartera'): 
        return tasa_cartera
    elif(producto=='operacion_especifica'): 
        return tasa_operacion_especifica
    elif(producto=='sufi'): 
        return tasa_sufi
    elif(producto=='leasing'): 
        return tasa_leasing
    elif(producto=='hipotecario'): 
        return tasa_hipotecario
    elif(producto=='factoring'): 
        return tasa_factoring
    else:
        return 0

# Manipulacion y transformacion de datos
# Inner Join entre la tabla obligaciones y tasas a partir de las llaves que comparten, lo que se alamcenara en un nuevo DataFrame
resultado_parte2_obligaciones = obligaciones.merge(tasas, how='inner', left_on=['cod_segm_tasa','cod_subsegm_tasa','cal_interna_tasa'], right_on=['cod_segmento','cod_subsegmento','calificacion_riesgos'])
# Asignacion de nueva columna para el campo producto, aplicando la funcion obtener_producto al DataFrame mediante el comando apply
resultado_parte2_obligaciones['producto'] = resultado_parte2_obligaciones.apply(obtener_producto, axis=1)
# Asignacion de nueva columna para el campo tasa, aplicando la funcion obtener_tasa al DataFrame mediante el comando apply
resultado_parte2_obligaciones['tasa'] = resultado_parte2_obligaciones.apply(obtener_tasa, axis=1)
# Asignacion de nueva columna para el campo tasa_efectiva, aplicando la formula designada (con su simplificacion)
resultado_parte2_obligaciones['tasa_efectiva'] = ((1+resultado_parte2_obligaciones['tasa'])**(resultado_parte2_obligaciones['cod_periodicidad']/12))-1
# Asignacion de nueva columna para el campo valor_final, aplicando el calculo indicado
resultado_parte2_obligaciones['valor_final'] = resultado_parte2_obligaciones['tasa_efectiva']*resultado_parte2_obligaciones['valor_inicial']

# Genercion de DatFrame para calculo de valor total de obligacion por cliente
resultado_parte2_obligaciones_clientes = resultado_parte2_obligaciones.groupby('num_documento')['valor_final'].agg(['count','sum']).reset_index().rename(columns={'count':'num_obligaciones', 'sum':'valor_total'})
# Filtracion para solo aquellos clientes que tengan obligaciones mayor o igual a 2
resultado_parte2_obligaciones_clientes = resultado_parte2_obligaciones_clientes[resultado_parte2_obligaciones_clientes['num_obligaciones']>=2]

# Depuracion de datos
# Eliminacion de columnas de tabla tasas que ya no son necesarias
resultado_parte2_obligaciones.drop(columns={'cod_segmento','segmento','cod_subsegmento','calificacion_riesgos','tasa_cartera','tasa_operacion_especifica','tasa_hipotecario','tasa_leasing','tasa_sufi','tasa_factoring','tasa_tarjeta'}, axis=1, inplace=True)

# Entrega de resultados
# Exportar el DataFrame de obligaciones transformado a excel en la ruta resultados
resultado_parte2_obligaciones.to_excel('resultados/parte2_obligaciones.xlsx', index=False)
# Exportar el DataFrame de obligaciones por cliente con obligaciones mayor o igual a 2 a excel en la ruta resultados
resultado_parte2_obligaciones_clientes.to_excel('resultados/parte2_obligaciones_clientes.xlsx', index=False)


# ------------------------------------------------------------------ Parte 3 ------------------------------------------------------------------
# Desarrollar un API desde el lenguaje de programación Python, para exponer información
# Creacion de la app
app = FastAPI(title='Consulta informacion de productos y valor total de cliente')


# Creacion de peticion para obtener el valor total de aquellos clientes que la cantidad de productos e smayor o igual a 2 
# Ruta asignada y asignacion de variable
@app.get("/valor_total_clientes/{num_documento}")
# Definicion de funcion para que a partir del numero de documento retorne el valor total de la tabla obligaciones_clientes_productos
# como la consulta entrega el DataFrame se realiza el ajuste para que solo entregue el valor
def obtener_valor_total_cliente(num_documento):
  informacion_cliente = pd.read_sql("""
                                    SELECT valor_total
                                    FROM obligaciones_clientes_productos
                                    WHERE num_documento=""" + num_documento, conexion_db)
  return {"valor_total": informacion_cliente['valor_total'][0]}