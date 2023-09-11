# Proyecto Obligaciones
Manipulación de los datos mediante sql y python para calcular la tasa efectiva y valor final de cada producto, a partir de las tasas que se tienen para cada producto, segmento, subsegmento y calificacion de riesgo de cada persona.
Posterior a esto se construye una API para entregar los datos solicitados.
Los archivos de insumo se encuentran en la carpeta src.
Los resultados del procesamiento de este se encuentra en la carpeta resultados (parte 1 y 2), para la parte 3 se debe ejecutar el programa de manera local (se explica al final)
#### Nota: este proyecto fue desarrollado bajo la version de python 3.10 - la cual es la que se recomienda para evitar novedades con las diferentes librerías con las que se trabajan. Adicionalmente como sqlite ahora viene con python, la funcion POW no se encuentra disponible en todas las versiones de python 3 

## ¿Cómo se desarrolló?
Se realizó la creación del repositorio, se procede a clonar la carpeta donde allí se configura un entorno virtual al cual se le instalaron las librerias necesarias, 
adicionalmente se crea el script (main.py) con el cual se procesa la información.
Adicionalmente se crea una rama de desarrollo mientras se realizan los cambios y ajustes.
### Parte 1
Se escoge trabajar con SQLite para evitar que quien realice las validacioens no requiera configurar la base de datos, instalaciones extras o tener que convertir manualmente los archivos a base datos.
Se capturan las tablas obligaciones y tasas de los archivos correspondientes, donde se realiza una transformacion a DataFrame, posteriormente medinate la libreria sqlite3 se crea la base de datos, con las tablas respectivas y se ingresan los datos de cada DataFrame. Con esto configurado se crean unas columnas adicionales para almacenar dichos datos (producto, tasa, tasa_efectiva, valor_final), los cuales se alimentan a partir de la ejecucion de otras consultas y bajo las condiciones indicadas.
Finalmente se crea una nueva tabla para almacenar el resultado del apartado 4 (valor total de obligaciones para clientes con un numero de obligaciones mayor o igual a 2).
Nota: cada vez que se ejecuta el programa la base de datos se crea y al final se pueden visualizar los resultados esperados en la carpeta resultados.

### Parte 2
Se toman los datos de los archivos y se convierte cada uno a DataFrame, se realiza un merge para manipular y procesar la información tal como en la Parte 1, pero ahora con el uso de la librearía Pandas, mediante la funcion apply se ingresa la informacion para las columnas nuevas de producto y tasa; respecto a las restantes tasa_efectiva y valor_final se ejecuta la formula indicada para cada caso. Para entregar el insumo de sumatoria de valor_final por cliente con obligaciones mayor o igual a 2 se emplea la funcion group_by. Ambos resultados se entregan en la carpeta en su respectivo archivo de excel. 

### Parte 3
Para la construcción de la API se implementa el framework FastAPI, donde se crea la app respectiva y un metodo get para cada solicitud, cada uno con su ruta y metodo respectivo donde se consulta la base de datos creada en la Parte 1.
Para evidenciar el resultado se debe probar de manera local 

## ¿Cómo realizar la prueba funcional?
- Ingresamos a la carpeta donde deseamos clonar el proyecto y ejecutamos el comando ```git clone https://github.com/jpvillaa/proyecto_obligaciones.git```
- Posterior a esto en la carpeta generada al clonar el repositorio creamos el entorno virtual con el siguiente comando ```python -m virtualenv venv_proyecto_obligaciones```
- Activamos el entorno virtual ```venv_proyecto_obligaciones\Scripts\activate.bat```
- Ejecutamos el siguiente comando para instalar las librerías necesarias ```pip install -r requirements.txt```
- Para ejecutar el programa ```uvicorn main:app --reload``` - con esto se ejecutaran los pasos indicados en el desarrollo, donde genera la base de datos y entrega los resultados de la parte 1 y 2 en la carpeta resultados; el archivo obligaciones entrega como queda la tabla obligaciones con las transformaciones y los otros archivos obligaciones_clientes entrega el valor total de las deudas por cliente cuando tiene un numero de obligaciones mayor o igual a 2.
- Para probar la API ingresa ```http://127.0.0.1:8000/docs#/``` donde se pueden ver ambos metodos GET para probar las peticiones. 
![Imagen de metodos GET API](/src/peticiones_API.png)
![Peticion 1 API](/src/peticion_1_API.png)
![Peticion 2 API](/src/peticion_2_API.png)
Si se desea probar de la otra forma se puede ingresar asi: 
- ```http://127.0.0.1:8000/productos_clientes/{num_documento}``` 
- ```http://127.0.0.1:8000/valor_total_clientes/{num_documento}```
