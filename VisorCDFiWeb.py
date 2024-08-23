import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd

# Cargar catálogos
@st.cache_data
def load_catalogs():
    regimen_fiscal_df = pd.read_excel('c_RegimenFiscal.xlsx', engine='openpyxl')
    uso_cfdi_df = pd.read_excel('c_UsoCFDI.xlsx', engine='openpyxl')
    forma_pago_df = pd.read_excel('c_FormaPago.xlsx', engine='openpyxl')
    metodo_pago_df = pd.read_excel('c_MetodoPago.xlsx', engine='openpyxl')
    clave_prod_serv_df = pd.read_excel('c_ClaveProdServ.xlsx', engine='openpyxl')
    return regimen_fiscal_df, uso_cfdi_df, forma_pago_df, metodo_pago_df, clave_prod_serv_df

def get_description(df, column, value):
    result = df[df[column].astype(str) == value]
    if not result.empty:
        return result.iloc[0]['Descripción']
    return 'No disponible'

def parse_xml(file, catalogs):
    namespaces = {'cfdi': 'http://www.sat.gob.mx/cfd/4'}
    regimen_fiscal_df, uso_cfdi_df, forma_pago_df, metodo_pago_df, clave_prod_serv_df = catalogs

    try:
        tree = ET.parse(file)
        root = tree.getroot()

        emisor = root.find('.//cfdi:Emisor', namespaces)
        receptor = root.find('.//cfdi:Receptor', namespaces)
        comprobante = root

        if emisor is not None and receptor is not None and comprobante is not None:
            data = {
                "Emisor Nombre": emisor.get('Nombre', 'No disponible'),
                "Fecha": comprobante.get('Fecha', 'No disponible'),
                "Folio": comprobante.get('Folio', 'No disponible'),
                "Domicilio Fiscal Receptor": receptor.get('DomicilioFiscalReceptor', 'No disponible'),
                "Nombre Receptor": receptor.get('Nombre', 'No disponible'),
                "RFC Receptor": receptor.get('Rfc', 'No disponible'),
                "Régimen Fiscal Receptor": get_description(regimen_fiscal_df, 'c_RegimenFiscal', receptor.get('RegimenFiscalReceptor', 'No disponible')),
                "Uso CFDI": get_description(uso_cfdi_df, 'c_UsoCFDI', receptor.get('UsoCFDI', 'No disponible')),
                "Forma de Pago": get_description(forma_pago_df, 'c_FormaPago', comprobante.get('FormaPago', 'No disponible')),
                "Método de Pago": get_description(metodo_pago_df, 'c_MetodoPago', comprobante.get('MetodoPago', 'No disponible')),
                "Moneda": comprobante.get('Moneda', 'No disponible'),
                "SubTotal": format_currency(comprobante.get('SubTotal', 'No disponible')),
                "Total": format_currency(comprobante.get('Total', 'No disponible'))
            }

            st.write("### Datos del CFDI")
            st.json(data)

            st.write("### Claves del Producto/Servicio")
            conceptos = root.findall('.//cfdi:Concepto', namespaces)
            for concepto in conceptos:
                clave_prod_serv = concepto.get('c_ClaveProdServ', 'No disponible')
                descripcion = concepto.get('DescripciónClaveProdServ', 'No disponible')
                st.write(f"**Clave Producto/Servicio:** {clave_prod_serv}")
                st.write(f"**Descripcion:** {get_description(clave_prod_serv_df, 'c_ClaveProdServ', clave_prod_serv)}")
                st.write(f"**Descripcion Producto/Servicio:** {descripcion}")
                st.write("---")

        else:
            st.error("No se encontraron los nodos necesarios en el archivo.")

    except ET.ParseError:
        st.error("No se pudo parsear el archivo.")

def format_currency(value):
    try:
        value = float(value)
        return "${:,.2f}".format(value)
    except ValueError:
        return value

# Streamlit app
st.title("Visor de Archivos XML CFDI")

uploaded_files = st.file_uploader("Sube archivos XML", accept_multiple_files=True, type="xml")

if uploaded_files:
    catalogs = load_catalogs()
    for uploaded_file in uploaded_files:
        st.subheader(f"Procesando archivo: {uploaded_file.name}")
        parse_xml(uploaded_file, catalogs)
