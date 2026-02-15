# Clipboard History

Por  [gera Kessler](http://gera.ar)

Con la inestimable colaboración de Héctor Benítez.

Este complemento permite gestionar un historial del portapapeles persistiéndolo en una base de datos local, lo que permite conservar los textos aún cuando el sistema se reinicia.
Añade comandos para la exploración del historial, funciones de búsqueda, conteo, favoritos, backup, y visualización de los elementos.
A parte de la interacción a través de la capa de comandos con funciones avanzadas, se puede utilizar una versión gráfica sencilla para quienes no quieran compicaciones.

Al instalarlo por primera vez e iniciar NVDA, se crea el archivo "clipboard_history" que contiene la base de datos. Este archivo se aloja en la raíz de la carpeta nvda en los directorios de la configuración del usuario.
También se crea un escuchador (listener) para capturar los cambios del portapapeles, y actualizar la base de datos cuando haya contenido de texto nuevo.
El historial no guarda duplicaciones para evitar un crecimiento innecesario de la base de datos. al copiar un texto existente, este se copia en la primera posición de la lista eliminando la anterior.

Hay 2 funciones asignables desde el diálogo gestos de entrada, categoría clipboardHistory. A saber

* Activar la capa de comandos
* Activar la interfaz gráfica

Nota importante:  
El historial del portapapeles puede conservar datos sensibles, por lo que es responsabilidad del usuario el eliminar el contenido antes de compartir una versión portable con copia de la configuración.

## Capa de comandos

Una vez activa la capa de comandos con el gesto asignado previamente, tenemos los siguientes grupos de atajos. Si se pulsa alguna tecla diferente a las listadas a continuación, se desactiva la capa de comandos y las teclas vuelven a su funcionalidad por defecto.

### Movimiento en la lista

* Flecha arriba; anterior elemento de la lista
* Flecha abajo; siguiente elemento de la lista
* Inicio; primer elemento de la lista
* fin; último elemento de la lista

### Funcionalidades que afectan al elemento enfocado en la lista

* Retroceso; en la lista general elimina el elemento. En favoritos lo desmarca como tal
* Flecha derecha; copia el texto al portapapeles y lo desplaza al comienzo de la lista general
* Flecha izquierda; abre el texto en una ventana de NVDA para su posterior revisión
* v; Pega el texto en la ventana con el foco
* c; verbaliza el número de caracteres excluyendo los espacios, los espacios en blanco, las palabras y las líneas
* f; marca o desmarca el elemento como favorito

### Funciones de búsqueda

* b; activa la ventana para buscar elementos en la lista
* f3; avanza a la siguiente coincidencia  del texto buscado
* g; activa la ventana para enfocar el elemento por número de orden

### Otras funcionalidades

* f1; muestra una ventana de NVDA con la lista de los atajos de la capa de comandos
* tab; conmuta entre la lista general y la de favoritos
* e; verbaliza si es favorito, el número de índice del elemento actual y el número total de la lista
* s; muestra el  diálogo de configuración del complemento
* z; muestra el diálogo de eliminación de elementos de la lista
* escape; desactiva la capa de comandos

## Búsqueda de elementos

Para buscar algún texto del historial por palabras, tan solo hay que pulsar la letra b con la capa de comandos activa.
Esto abre el diálogo de búsqueda donde al escribir alguna palabra o frase y pulsar intro, se realizará la búsqueda.
Si se encuentra un resultado se verbaliza el texto y su número de orden. Si pulsamos f3, se vuelve a realizar la búsqueda con el mismo contenido, avanzando hasta el siguiente resultado en el caso de encontrar otra coincidencia.

## Favoritos

La tecla tabulador cambia el enfoque entre la lista general y la lista de favoritos. Cuando esta última está activa, la tecla de retroceso quita el estado favorito del elemento, y a este de la lista.
En la lista general, la letra f conmuta el estado favorito y lo añade o quita de la lista de favoritos.
Las funciones de copia, visualización, búsqueda, pegado, verbalización de orden, y cerrado de ventana  cumplen la misma función en ambas listas.

## Ventana de configuración

Al pulsar la letra s con la capa de comandos activa, o control + p en la versión gráfica,  se muestra la interfaz de configuración.
En ella puede modificarse lo siguiente:

### Número de cadenas a guardar

Aquí se puede especificar hasta cuantos elementos se van a guardar en la base de datos. Cuando se supere este número, se van eliminando las entradas antiguas desde la última.
Si al configurar un número máximo de elementos la base de datos contiene una cantidad mayor a ese valor, cuando se ingresen nuevos datos se eliminarán las entradas antiguas pero manteniendo el número actual de elementos para que el usuario pueda seleccionar cuales eliminar.

### Sonidos

Activa o desactiva los sonidos del complemento

### Número de índice de los elementos

Si está activa esta casilla, al navegar por la lista de elementos se verbaliza el número de orden de los mismos.

### Exportar base de datos

Este botón activa el diálogo para guardar la base de datos en su estado actual para copia de seguridad de los datos alojados en ella, permitiendo la posterior importación desde otro NVDA con este complemento.

### Importar base de datos

Esta opción activa un diálogo  para buscar una base de datos exportada previamente para recuperar los elementos inexistentes en la base de datos actual.

## Interfaz gráfica

Una vez asignado el gesto, esta opción abre la interfaz gráfica que simplifica la navegación e interacción con el historial.
Los diferentes elementos almacenados aparecen en forma de lista, la cual puede recorrerse con flechas arriba y abajo.
Al tabular teniendo seleccionado algún elemento en la lista, el contenido se muestra en un cuadro de solo lectura.

La lista de elementos tiene los siguientes atajos disponibles:

* f1; verbaliza la posición y el total de elementos
* intro; copia el texto del elemento enfocado al portapapeles
* f5; refresca el contenido de la lista
* suprimir; elimina el elemento enfocado
* alt + suprimir; elimina el historial
* control + p; activa la ventana de configuración del complemento
* escape; cierra la interfaz
