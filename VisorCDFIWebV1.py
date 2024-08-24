import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
import sqlite3

def parse_cfdi(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    ns = {
        'cfdi': 'http://www.sat.gob.mx/cfd/4'
    }

    moneda = root.attrib.get('Moneda', '')
    tipo_cambio = float(root.attrib.get('TipoCambio', '1'))

    subtotal = float(root.attrib.get('SubTotal', '0'))
    total_impuestos_trasladados = float(root.find('cfdi:Impuestos', ns).attrib.get('TotalImpuestosTrasladados', '0'))
    total = float(root.attrib.get('Total', '0'))

    # Conexión a la base de datos SQLite utilizando una ruta relativa
    conn = sqlite3.connect('ClaveProdSat.db')
    cursor = conn.cursor()

    conceptos = root.findall('cfdi:Conceptos/cfdi:Concepto', ns)
    conceptos_data = []

    for concepto in conceptos:
        clave_prod_serv = concepto.attrib.get('ClaveProdServ', 'N/A')
        descripcion = concepto.attrib.get('Descripcion', 'N/A')
        clave_unidad = concepto.attrib.get('ClaveUnidad', 'N/A')
        
        cursor.execute("SELECT Descripcion FROM c_ClaveProdServ WHERE ClaveProdServ = ?", (clave_prod_serv,))
        resultado = cursor.fetchone()
        descripcion_sat = resultado[0] if resultado else 'N/A'
        
        conceptos_data.append({
            "Clave": clave_prod_serv,
            "Descripcion": descripcion,
            "ClaveUnidad": clave_unidad,
            "DescripcionSAT": descripcion_sat
        })

    conn.close()

    # Obtener RegimenFiscal del Emisor
    regimen_fiscal_emisor = root.find('cfdi:Emisor', ns).attrib.get('RegimenFiscal', 'N/A')

    data = {
        "Nombre Archivo": xml_file.name,
        "Rfc2": root.find('cfdi:Receptor', ns).attrib.get('Rfc', ''),
        "Nombre Receptor": root.find('cfdi:Receptor', ns).attrib.get('Nombre', ''),
        "Serie": root.attrib.get('Serie', ''),
        "Folio": root.attrib.get('Folio', ''),
        "Fecha": root.attrib.get('Fecha', ''),
        "Nombre Emisor": root.find('cfdi:Emisor', ns).attrib.get('Nombre', ''),
        "Rfc Emisor": root.find('cfdi:Emisor', ns).attrib.get('Rfc', ''),
        "RegimenFiscalEmisor": regimen_fiscal_emisor,
        "MetodoPago": root.attrib.get('MetodoPago', ''),
        "FormaPago": root.attrib.get('FormaPago', ''),
        "UsoCFDI": root.find('cfdi:Receptor', ns).attrib.get('UsoCFDI', ''),
        "Moneda": moneda,
        "TipoCambio": tipo_cambio,
        "SubTotal": format_currency(subtotal),
        "TotalImpuestosTrasladados": format_currency(total_impuestos_trasladados),
        "Total": format_currency(total),
    }

    if moneda == "USD":
        data["SubTotal en MXN"] = format_currency(subtotal * tipo_cambio)
        data["TotalImpuestosTrasladados en MXN"] = format_currency(total_impuestos_trasladados * tipo_cambio)
        data["Total en MXN"] = format_currency(total * tipo_cambio)

    return data, conceptos_data

def format_currency(value):
    try:
        return "${:,.2f}".format(value)
    except (ValueError, TypeError):
        return value

def search_clave_prod_serv(query, search_type):
    conn = sqlite3.connect('ClaveProdSat.db')
    cursor = conn.cursor()

    if not query:
        cursor.execute("SELECT ClaveProdServ, Descripcion FROM c_ClaveProdServ")
    elif search_type == "Clave":
        cursor.execute("SELECT ClaveProdServ, Descripcion FROM c_ClaveProdServ WHERE ClaveProdServ = ?", (query,))
    else:
        cursor.execute("SELECT ClaveProdServ, Descripcion FROM c_ClaveProdServ WHERE Descripcion LIKE ?", ('%' + query + '%',))

    results = cursor.fetchall()
    conn.close()

    return results

def search_uso_cfdi(query, search_type):
    conn = sqlite3.connect('c_UsoCFDI.db')
    cursor = conn.cursor()

    if not query:
        cursor.execute("SELECT c_UsoCFDI, Descripcion FROM c_UsoCFDI")
    elif search_type == "Clave":
        cursor.execute("SELECT c_UsoCFDI, Descripcion FROM c_UsoCFDI WHERE c_UsoCFDI = ?", (query,))
    else:
        cursor.execute("SELECT c_UsoCFDI, Descripcion FROM c_UsoCFDI WHERE Descripcion LIKE ?", ('%' + query + '%',))

    results = cursor.fetchall()
    conn.close()

    return results

def search_forma_pago(query, search_type):
    conn = sqlite3.connect('c_FormaPago.db')
    cursor = conn.cursor()

    if not query:
        cursor.execute("SELECT c_FormaPago, Descripcion FROM c_FormaPago")
    elif search_type == "Clave":
        cursor.execute("SELECT c_FormaPago, Descripcion FROM c_FormaPago WHERE c_FormaPago = ?", (query,))
    else:
        cursor.execute("SELECT c_FormaPago, Descripcion FROM c_FormaPago WHERE Descripcion LIKE ?", ('%' + query + '%',))

    results = cursor.fetchall()
    conn.close()

    return results

def search_regimen_fiscal(query, search_type):
    conn = sqlite3.connect('c_RegimenFiscal.db')
    cursor = conn.cursor()

    if not query:
        cursor.execute("SELECT c_RegimenFiscal, Descripcion FROM c_RegimenFiscal")
    elif search_type == "Clave":
        cursor.execute("SELECT c_RegimenFiscal, Descripcion FROM c_RegimenFiscal WHERE c_RegimenFiscal = ?", (query,))
    else:
        cursor.execute("SELECT c_RegimenFiscal, Descripcion FROM c_RegimenFiscal WHERE Descripcion LIKE ?", ('%' + query + '%',))

    results = cursor.fetchall()
    conn.close()

    return results

def main():
    st.title("Visor de CFDI y Buscador de ClaveProdServ/UsoCFDI/Forma de Pago/Régimen Fiscal")

    st.markdown(
        """
        <style>
        .dataframe td.col1 {
            min-width: 300px;
            max-width: 300px;
            word-wrap: break-word;
        }
        </style>
        """, unsafe_allow_html=True
    )

    # Sidebar para la búsqueda de ClaveProdServ, UsoCFDI, Forma de Pago y Régimen Fiscal
    with st.sidebar:
        st.write("### Búsquedas en ClaveProdServ, UsoCFDI, Forma de Pago y Régimen Fiscal")

        with st.expander("Desplegar Búsqueda ClaveProdServ"):
            search_query = st.text_input("Ingresa la clave o una descripción para buscar en el catálogo de ClaveProdServ:")
            search_type = st.radio("Tipo de búsqueda:", ('Clave', 'Descripción'))

            if st.button("Buscar ClaveProdServ"):
                results = search_clave_prod_serv(search_query, search_type)
                if results:
                    df_results = pd.DataFrame(results, columns=["ClaveProdServ", "Descripción"])
                    st.write("### Resultados de la búsqueda:")
                    st.table(df_results)
                else:
                    st.warning("No se encontraron resultados para la búsqueda en ClaveProdServ.")

        with st.expander("Desplegar Búsqueda UsoCFDI"):
            search_query_cfdi = st.text_input("Ingresa la clave o una descripción para buscar en el catálogo de UsoCFDI:")
            search_type_cfdi = st.radio("Tipo de búsqueda UsoCFDI:", ('Clave', 'Descripción'))

            if st.button("Buscar UsoCFDI"):
                results_cfdi = search_uso_cfdi(search_query_cfdi, search_type_cfdi)
                if results_cfdi:
                    df_results_cfdi = pd.DataFrame(results_cfdi, columns=["c_UsoCFDI", "Descripción"])
                    st.write("### Resultados de la búsqueda en UsoCFDI:")
                    st.table(df_results_cfdi)
                else:
                    st.warning("No se encontraron resultados para la búsqueda en UsoCFDI.")

        with st.expander("Desplegar Búsqueda Forma de Pago"):
            search_query_fp = st.text_input("Ingresa la clave o una descripción para buscar en el catálogo de Forma de Pago:")
            search_type_fp = st.radio("Tipo de búsqueda Forma de Pago:", ('Clave', 'Descripción'))

            if st.button("Buscar Forma de Pago"):
                results_fp = search_forma_pago(search_query_fp, search_type_fp)
                if results_fp:
                    df_results_fp = pd.DataFrame(results_fp, columns=["c_FormaPago", "Descripción"])
                    st.write("### Resultados de la búsqueda en Forma de Pago:")
                    st.table(df_results_fp)
                else:
                    st.warning("No se encontraron resultados para la búsqueda en Forma de Pago.")

        with st.expander("Desplegar Búsqueda Régimen Fiscal"):
            search_query_rf = st.text_input("Ingresa la clave o una descripción para buscar en el catálogo de Régimen Fiscal:")
            search_type_rf = st.radio("Tipo de búsqueda Régimen Fiscal:", ('Clave', 'Descripción'))

            if st.button("Buscar Régimen Fiscal"):
                results_rf = search_regimen_fiscal(search_query_rf, search_type_rf)
                if results_rf:
                    df_results_rf = pd.DataFrame(results_rf, columns=["c_RegimenFiscal", "Descripción"])
                    st.write("### Resultados de la búsqueda en Régimen Fiscal:")
                    st.table(df_results_rf)
                else:
                    st.warning("No se encontraron resultados para la búsqueda en Régimen Fiscal.")

    # Sección para cargar y visualizar CFDI
    uploaded_file = st.file_uploader("Carga tu archivo XML de CFDI", type="xml")

    if uploaded_file is not None:
        try:
            data, conceptos_data = parse_cfdi(uploaded_file)

            st.write("### Datos extraídos del CFDI:")
            df_data = pd.DataFrame(list(data.items()), columns=['Campo', 'Valor'])

            def highlight_rows(row):
                color = 'red' if row['Campo'] in ['MetodoPago', 'FormaPago', 'UsoCFDI', 'Fecha', 'RegimenFiscalEmisor', 'Rfc Emisor'] else ''
                return ['color: {}'.format(color) for _ in row]

            styled_df = df_data.style.apply(highlight_rows, axis=1)
            st.table(styled_df)

            if conceptos_data:
                st.write("### ClaveProdServ, ClaveUnidad, Descripción y DescripcionSAT:")
                df_conceptos = pd.DataFrame(conceptos_data)
                st.table(df_conceptos)

        except Exception as e:
            st.error(f"Error al procesar el archivo XML: {e}")

if __name__ == "__main__":
    main()
