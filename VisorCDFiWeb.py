import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd

# Cargar catálogos desde archivos subidos
@st.cache_data
def load_catalogs(regimen_file, uso_cfdi_file, forma_pago_file, metodo_pago_file, clave_prod_serv_file):
    try:
        regimen_fiscal_df = pd.read_excel(regimen_file, engine='openpyxl')
        uso_cfdi_df = pd.read_excel(uso_cfdi_file, engine='openpyxl')
        forma_pago_df = pd.read_excel(forma_pago_file, engine='openpyxl')
        metodo_pago_df = pd.read_excel(metodo_pago_file, engine='openpyxl')
        clave_prod_serv_df = pd.read_excel(clave_prod_serv_file, engine='openpyxl')
    except Exception as e:
        st.error(f"Error al cargar los archivos de catálogos: {e}")
        return None, None, None, None, None
    return regimen_fiscal_df, uso_cfdi_df, forma_pago_df, metodo_pago_df, clave_prod_serv_df

def get_description(df, column_key, key, column_desc):
    if df is not None and column_key in df.columns and column_desc in df.columns:
        result = df[df[column_key].astype(str) == key]
        if not result.empty:
            return result.iloc[0][column_desc]
    return 'No disponible'

def parse_xml(file_path, catalogs):
    namespaces = {'cfdi': 'http://www.sat.gob.mx/cfd/4'}
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        emisor = root.find('.//cfdi:Emisor', namespaces)
        receptor = root.find('.//cfdi:Receptor', namespaces)
        comprobante = root

        if emisor is not None and receptor is not None and comprobante is not None:
            emisor_nombre = emisor.get('Nombre', 'No disponible')
            fecha = comprobante.get('Fecha', 'No disponible')
            folio = comprobante.get('Folio', 'No disponible')

            receptor_domicilio_fiscal = receptor.get('DomicilioFiscalReceptor', 'No disponible')
            receptor_nombre = receptor.get('Nombre', 'No disponible')
            receptor_rfc = receptor.get('Rfc', 'No disponible')
            receptor_regimen = receptor.get('RegimenFiscalReceptor', 'No disponible')
            receptor_uso_cfdi = receptor.get('UsoCFDI', 'No disponible')
            receptor_forma_pago = comprobante.get('FormaPago', 'No disponible')
            receptor_metodo_pago = comprobante.get('MetodoPago', 'No disponible')
            receptor_moneda = comprobante.get('Moneda', 'No disponible')
            tipo_cambio = comprobante.get('TipoCambio', 'No disponible')
            subtotal = comprobante.get('SubTotal', 'No disponible')
            total = comprobante.get('Total', 'No disponible')

            regimen_descripcion = get_description(catalogs['regimen_fiscal_df'], 'c_RegimenFiscal', receptor_regimen, 'Descripción')
            uso_cfdi_descripcion = get_description(catalogs['uso_cfdi_df'], 'c_UsoCFDI', receptor_uso_cfdi, 'Descripción')
            forma_pago_descripcion = get_description(catalogs['forma_pago_df'], 'c_FormaPago', receptor_forma_pago, 'Descripción')
            metodo_pago_descripcion = get_description(catalogs['metodo_pago_df'], 'c_MetodoPago', receptor_metodo_pago, 'Descripción')

            st.subheader(f"CFDI: {file_path}")
            st.write(f"**Emisor Nombre:** {emisor_nombre}")
            st.write(f"**Fecha:** {fecha}")
            st.write(f"**Folio:** {folio}")
            st.write(f"**Domicilio Fiscal Receptor:** {receptor_domicilio_fiscal}")
            st.write(f"**Nombre Receptor:** {receptor_nombre}")
            st.write(f"**RFC Receptor:** {receptor_rfc}")
            st.write(f"**Régimen Fiscal Receptor:** {receptor_regimen} ({regimen_descripcion})")
            st.write(f"**Uso CFDI:** {receptor_uso_cfdi} ({uso_cfdi_descripcion})")
            st.write(f"**Forma de Pago:** {receptor_forma_pago} ({forma_pago_descripcion})")
            st.write(f"**Método de Pago:** {receptor_metodo_pago} ({metodo_pago_descripcion})")
            st.write(f"**Moneda:** {receptor_moneda}")
            st.write(f"**Tipo de Cambio:** {tipo_cambio}")
            st.write(f"**SubTotal:** {subtotal}")
            st.write(f"**Total:** {total}")

            st.subheader("Claves del Producto del SAT")
            conceptos = root.findall('.//cfdi:Concepto', namespaces)
            for concepto in conceptos:
                clave_prod_serv = concepto.get('ClaveProdServ', 'No disponible')
                descripcion = concepto.get('Descripcion', 'No disponible')
                clave_prod_serv_descripcion = get_description(catalogs['clave_prod_serv_df'], 'c_ClaveProdServ', clave_prod_serv, 'DescripciónClaveProdServ')
                st.write(f"**Clave Producto/Servicio:** {clave_prod_serv} ({clave_prod_serv_descripcion})")
                st.write(f"**Descripción Producto/Servicio:** {descripcion}")
        else:
            st.error("No se encontraron los nodos necesarios en el archivo.")
    except ET.ParseError:
        st.error(f"No se pudo parsear el archivo {file_path}")

def main():
    st.title("Visor de Archivos XML CFDI")

    st.subheader("Carga los archivos de catálogos (.xlsx)")
    regimen_file = st.file_uploader("Cargar c_RegimenFiscal.xlsx", type="xlsx")
    uso_cfdi_file = st.file_uploader("Cargar c_UsoCFDI.xlsx", type="xlsx")
    forma_pago_file = st.file_uploader("Cargar c_FormaPago.xlsx", type="xlsx")
    metodo_pago_file = st.file_uploader("Cargar c_MetodoPago.xlsx", type="xlsx")
    clave_prod_serv_file = st.file_uploader("Cargar c_ClaveProdServ.xlsx", type="xlsx")

    if regimen_file and uso_cfdi_file and forma_pago_file and metodo_pago_file and clave_prod_serv_file:
        catalogs = load_catalogs(regimen_file, uso_cfdi_file, forma_pago_file, metodo_pago_file, clave_prod_serv_file)
        if catalogs[0] is None:
            st.stop()

        uploaded_files = st.file_uploader("Cargar archivos XML", accept_multiple_files=True, type="xml")

        if uploaded_files:
            for uploaded_file in uploaded_files:
                parse_xml(uploaded_file, {
                    'regimen_fiscal_df': catalogs[0],
                    'uso_cfdi_df': catalogs[1],
                    'forma_pago_df': catalogs[2],
                    'metodo_pago_df': catalogs[3],
                    'clave_prod_serv_df': catalogs[4],
                })

if __name__ == "__main__":
    main()
