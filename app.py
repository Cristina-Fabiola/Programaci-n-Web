import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime


st.set_page_config(
    page_title="Sistema de Ventas - Tienda de Ropa",
    page_icon="👗",
    layout="wide"
)

API_URL = "https://dummyjson.com/products?limit=0"
ARCHIVO_VENTAS = "ventas.csv"


st.cache_data(ttl=600)
def obtener_productos():
    """Obtiene todos los productos de DummyJSON."""

    try:
        respuesta = requests.get(API_URL, timeout=15)

        if respuesta.status_code == 200:
            datos = respuesta.json()
            return datos.get("products", [])

        st.error("No se pudieron obtener los productos de la API.")
        return []

    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión con la API: {e}")
        return []


def crear_catalogo_ropa(productos):

    productos_filtrados = []

    categorias_permitidas = [
        "womens-dresses",
        "womens-shoes",
        "womens-bags",
        "womens-jewellery",
        "womens-watches"
    ]

    palabras_ropa = [
        "dress",
        "dresses",
        "gown",
        "skirt",
        "corset",
        "suit",
        "clothing",
        "shirt",
        "shoe",
        "shoes",
        "bag",
        "jewellery",
        "jewelry",
        "watch"
    ]

    for producto in productos:

        categoria = str(producto.get("category", "")).lower()
        titulo = str(producto.get("title", "")).lower()
        descripcion = str(producto.get("description", "")).lower()

        pertenece_categoria = categoria in categorias_permitidas

        contiene_palabra = any(
            palabra in titulo or palabra in descripcion
            for palabra in palabras_ropa
        )

        if pertenece_categoria or contiene_palabra:
            productos_filtrados.append(producto)

    return productos_filtrados


def guardar_venta(nombre, correo, carrito, total):
    """Guarda la venta en un archivo CSV."""

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    registros = []

    for producto in carrito:
        subtotal = producto["precio"] * producto["cantidad"]

        registros.append({
            "Fecha": fecha,
            "Cliente": nombre,
            "Correo": correo,
            "Producto": producto["nombre"],
            "Cantidad": producto["cantidad"],
            "Precio": producto["precio"],
            "Subtotal": subtotal,
            "Total Venta": total
        })

    nuevo_df = pd.DataFrame(registros)

    if os.path.exists(ARCHIVO_VENTAS):
        df_anterior = pd.read_csv(ARCHIVO_VENTAS)
        df_final = pd.concat(
            [df_anterior, nuevo_df],
            ignore_index=True
        )
    else:
        df_final = nuevo_df

    df_final.to_csv(
        ARCHIVO_VENTAS,
        index=False,
        encoding="utf-8-sig"
    )


def cargar_ventas():
    """Carga las ventas guardadas."""

    if os.path.exists(ARCHIVO_VENTAS):
        try:
            return pd.read_csv(ARCHIVO_VENTAS)
        except:
            return pd.DataFrame()

    return pd.DataFrame()


def nombre_categoria(categoria):
    """Convierte el nombre de categoría a español."""

    categorias = {
        "womens-dresses": "👗 Vestidos",
        "womens-shoes": "👠 Zapatos",
        "womens-bags": "👜 Bolsas",
        "womens-jewellery": "💍 Joyería",
        "womens-watches": "⌚ Relojes",
        "mens-shirts": "👕 Camisas",
        "mens-shoes": "👞 Zapatos de hombre",
        "mens-watches": "⌚ Relojes de hombre"
    }

    return categorias.get(categoria, categoria)



if "carrito" not in st.session_state:
    st.session_state.carrito = []



todos_productos = obtener_productos()

productos = crear_catalogo_ropa(todos_productos)




st.title("👗 SISTEMA DE VENTAS")
st.subheader("Tienda de Ropa y Accesorios")

st.markdown(
    """
    Catálogo conectado a **DummyJSON API**.
    
    Aquí puedes consultar productos, agregarlos al carrito,
    registrar clientes y guardar las ventas.
    """
)

st.divider()



opcion = st.sidebar.radio(
    "MENÚ PRINCIPAL",
    [
        "Inicio",
        "Catálogo",
        "Carrito",
        "Registrar venta",
        "Ventas",
        "Información"
    ]
)



if opcion == "Inicio":

    st.header(" Bienvenido al sistema")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Productos disponibles",
            len(productos)
        )

    with col2:
        st.metric(
            "Productos en carrito",
            sum(
                p["cantidad"]
                for p in st.session_state.carrito
            )
        )

    with col3:
        ventas = cargar_ventas()

        if not ventas.empty:
            total_ventas = ventas["Total Venta"].sum()
        else:
            total_ventas = 0

        st.metric(
            "Ventas registradas",
            f"${total_ventas:,.2f}"
        )

    st.divider()

    st.info(
        "El catálogo utiliza productos disponibles "
        "en la API de DummyJSON."
    )

    st.write("### Categorías disponibles")

    categorias = {}

    for producto in productos:
        categoria = producto.get("category", "Otros")

        if categoria not in categorias:
            categorias[categoria] = 0

        categorias[categoria] += 1

    for categoria, cantidad in categorias.items():
        st.write(
            f"**{nombre_categoria(categoria)}:** {cantidad} productos"
        )


elif opcion == "Catálogo":

    st.header("Catálogo de productos")

    if not productos:
        st.warning("No se encontraron productos.")
        st.stop()


    col1, col2, col3 = st.columns(3)

    with col1:

        categorias = sorted(
            list(
                set(
                    p.get("category", "Otros")
                    for p in productos
                )
            )
        )

        categoria_seleccionada = st.selectbox(
            "Categoría",
            ["Todas"] + categorias,
            format_func=lambda x:
                "Todas" if x == "Todas"
                else nombre_categoria(x)
        )

    with col2:

        precios = [
            float(p.get("price", 0))
            for p in productos
        ]

        precio_min = min(precios)
        precio_max = max(precios)

        rango_precio = st.slider(
            "Rango de precio",
            min_value=float(precio_min),
            max_value=float(precio_max),
            value=(float(precio_min), float(precio_max))
        )

    with col3:

        busqueda = st.text_input(
            "🔎 Buscar producto",
            placeholder="Ejemplo: dress, skirt, bag..."
        )



    productos_mostrados = []

    for producto in productos:

        categoria = producto.get(
            "category",
            ""
        )

        precio = float(
            producto.get(
                "price",
                0
            )
        )

        titulo = str(
            producto.get(
                "title",
                ""
            )
        )

        descripcion = str(
            producto.get(
                "description",
                ""
            )
        )

        # Filtro categoría
        if (
            categoria_seleccionada != "Todas"
            and categoria != categoria_seleccionada
        ):
            continue

        # Filtro precio
        if precio < rango_precio[0] or precio > rango_precio[1]:
            continue

        # Filtro búsqueda
        if busqueda:

            texto = (
                titulo +
                " " +
                descripcion
            ).lower()

            if busqueda.lower() not in texto:
                continue

        productos_mostrados.append(producto)

    st.write(
        f"### {len(productos_mostrados)} productos encontrados"
    )

  

    if not productos_mostrados:

        st.warning(
            "No se encontraron productos con esos filtros."
        )

    else:

        columnas = st.columns(4)

        for indice, producto in enumerate(productos_mostrados):

            with columnas[indice % 4]:

                st.image(
                    producto.get(
                        "thumbnail",
                        ""
                    ),
                    use_container_width=True
                )

                st.markdown(
                    f"### {producto.get('title', 'Producto')}"
                )

                st.write(
                    f"**Categoría:** "
                    f"{nombre_categoria(producto.get('category', ''))}"
                )

                st.write(
                    f"**${producto.get('price', 0):,.2f}**"
                )

                descuento = producto.get(
                    "discountPercentage",
                    0
                )

                st.write(
                    f"Descuento: {descuento:.2f}%"
                )

                st.write(
                    f"Rating: "
                    f"{producto.get('rating', 0):.2f}"
                )

                st.write(
                    f"Stock: "
                    f"{producto.get('stock', 0)}"
                )

                if st.button(
                    "Agregar al carrito",
                    key=f"agregar_{producto['id']}"
                ):

                    producto_carrito = {
                        "id": producto["id"],
                        "nombre": producto["title"],
                        "precio": float(producto["price"]),
                        "cantidad": 1,
                        "imagen": producto.get(
                            "thumbnail",
                            ""
                        )
                    }

                    # Buscar si ya existe
                    encontrado = False

                    for item in st.session_state.carrito:

                        if item["id"] == producto["id"]:

                            item["cantidad"] += 1
                            encontrado = True
                            break

                    if not encontrado:
                        st.session_state.carrito.append(
                            producto_carrito
                        )

                    st.success(
                        "Producto agregado al carrito."
                    )

                st.divider()



elif opcion == "Carrito":

    st.header("Carrito de compras")

    carrito = st.session_state.carrito

    if not carrito:

        st.info(
            "Tu carrito está vacío."
        )

    else:

        total = 0

        for indice, producto in enumerate(carrito):

            subtotal = (
                producto["precio"] *
                producto["cantidad"]
            )

            total += subtotal

            col1, col2, col3, col4 = st.columns(
                [1, 3, 1, 1]
            )

            with col1:

                st.image(
                    producto["imagen"],
                    width=100
                )

            with col2:

                st.write(
                    f"### {producto['nombre']}"
                )

                st.write(
                    f"Precio: "
                    f"${producto['precio']:,.2f}"
                )

            with col3:

                nueva_cantidad = st.number_input(
                    "Cantidad",
                    min_value=1,
                    value=producto["cantidad"],
                    key=f"cantidad_{producto['id']}"
                )

                producto["cantidad"] = nueva_cantidad

            with col4:

                st.write(
                    f"**Subtotal**"
                )

                st.write(
                    f"${subtotal:,.2f}"
                )

                if st.button(
                    "Eliminar",
                    key=f"eliminar_{producto['id']}"
                ):

                    st.session_state.carrito.pop(indice)

                    st.rerun()

            st.divider()

        st.subheader(
            f"TOTAL: ${total:,.2f}"
        )

        if st.button(
            "Vaciar carrito"
        ):

            st.session_state.carrito = []

            st.rerun()



elif opcion == " Registrar venta":

    st.header(" Registrar venta")

    if not st.session_state.carrito:

        st.warning(
            "Primero agrega productos al carrito."
        )

    else:

        st.write("###  Datos del cliente")

        nombre = st.text_input(
            "Nombre del cliente"
        )

        correo = st.text_input(
            "Correo electrónico"
        )

        st.write("### Productos")

        total = 0

        for producto in st.session_state.carrito:

            subtotal = (
                producto["precio"] *
                producto["cantidad"]
            )

            total += subtotal

            st.write(
                f"**{producto['nombre']}** "
                f"x {producto['cantidad']} "
                f"= ${subtotal:,.2f}"
            )

        st.divider()

        st.subheader(
            f"💰 TOTAL A PAGAR: ${total:,.2f}"
        )

        if st.button(
            " CONFIRMAR VENTA",
            type="primary"
        ):

            if not nombre.strip():

                st.error(
                    "Escribe el nombre del cliente."
                )

            elif not correo.strip():

                st.error(
                    "Escribe el correo del cliente."
                )

            else:

                guardar_venta(
                    nombre,
                    correo,
                    st.session_state.carrito,
                    total
                )

                st.session_state.carrito = []

                st.success(
                    " Venta registrada correctamente."
                )

                st.balloons()


elif opcion == "Ventas":

    st.header(" Registro de ventas")

    ventas = cargar_ventas()

    if ventas.empty:

        st.info(
            "Todavía no existen ventas registradas."
        )

    else:


        total_vendido = ventas["Total Venta"].sum()

        numero_ventas = ventas[
            "Fecha"
        ].nunique()

        productos_vendidos = ventas[
            "Cantidad"
        ].sum()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Total vendido",
                f"${total_vendido:,.2f}"
            )

        with col2:
            st.metric(
                "Ventas",
                numero_ventas
            )

        with col3:
            st.metric(
                "Productos vendidos",
                int(productos_vendidos)
            )

        st.divider()

        
        st.subheader(
            "Historial de ventas"
        )

        st.dataframe(
            ventas,
            use_container_width=True
        )


        st.subheader(
            "Ventas por producto"
        )

        ventas_producto = (
            ventas
            .groupby("Producto")["Subtotal"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        st.bar_chart(
            ventas_producto
        )

      



