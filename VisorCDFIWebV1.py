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
        "RegimenFiscalEmisor": regimen_fiscal_emisor,  # Agregado debajo de Rfc Emisor
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

def main():
    st.title("Visor de CFDI")

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
