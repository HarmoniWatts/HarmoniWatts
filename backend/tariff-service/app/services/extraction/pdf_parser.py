from datetime import date

import pdfplumber
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger

class PDFParser:
    """Parsea PDFs de tarifas para extraer datos estructurados"""
    
    def parsear(self, pdf: dict) -> List[Dict[str, Any]]:
        """
        Extrae tablas del PDF y las convierte en diccionarios.
        Retorna una lista de tarifas extraídas.
        """
        pdf_path = pdf["path"]
        fecha_doc = pdf["fecha"]
        titulo = pdf["titulo"]
        
        tarifas = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for num_pagina, pagina in enumerate(pdf.pages):
                logger.info(f"Procesando página {num_pagina + 1}")
                
                # Extraer tablas
                tablas = pagina.extract_tables()
                
                for tabla in tablas:
                    if self._es_tabla_tarifa(tabla):
                        tarifas.extend(self._parsear_tabla_tarifa(tabla, fecha_doc, titulo))
        
        logger.info(f"Extraídas {len(tarifas)} tarifas del PDF {pdf_path.name}")
        
        return tarifas
    
    def _es_tabla_tarifa(self, tabla: List[List[str]]) -> bool:
        """Verifica si una tabla contiene datos de tarifas"""
        if not tabla or len(tabla) < 2:
            return False
        
        # Buscar headers típicos de tarifas
        headers = [str(celda).lower() for celda in tabla[0] if celda]
        headers_texto = ' '.join(headers)
        
        palabras_clave = ['mercado', 'nivel', 'tarifa', 'f1', 'f2', 'cu', 'cs']
        return any(palabra in headers_texto for palabra in palabras_clave)
    
    def _parsear_tabla_tarifa(
        self, 
        tabla: List[List[str]], 
        fecha_doc: date,
        titulo: str
    ) -> List[Dict[str, Any]]:
        """Parsea una tabla específica de tarifas"""
        
        if not tabla or len(tabla) < 2:
            return []
        
        
        tarifas = []
        
        mercado_actual = ""
        nivel_tension = ""
        tipo_tarifa = ""
        niveles_mercado = {}
        niveles = []
        horas =  False
        CU_base = ""
        Tm = ""
        Rm = ""
        Cmfj = ""
        dicc_monomia = {}
        dicc_comp_cu = {}
       
        for fila in tabla:
            # print(f"\nProcesando fila: {fila}")
            
            #Buscar filas que contengan Tm y Rm
            for i in range(len(fila)):
                if fila[i] == 'Tm':
                    Tm = str(fila[i+1]).replace(' ', '').replace('\xa0', '')
                    Tm = self._safe_float(Tm) if (i+1 < len(fila) and fila[i+1]) else ""
                if fila[i]  == 'Rm':
                    Rm = str(fila[i+1]).replace(' ', '').replace('\xa0', '')
                    Rm = self._safe_float(Rm) if (i+1 < len(fila) and fila[i+1]) else ""
            
            
            # Buscar filas que contengan Cfmj
            if fila[0] and any(c in str(fila[0]) for c in ['Cfmj', 'Cfmj']):
                Cmfj = fila[0].split(' Cfmj')[1].strip()
                Cmfj = str(Cmfj).replace('.', '').replace(',', '').replace(' ', '')
                Cmfj = float(Cmfj)
            
            # Buscar filas que contengan nombres de mercado
            if fila[0] and any(mercado in str(fila[0]) for mercado in ['MERCADO', 'MCDO']):
                mercado_actual = fila[0].replace('MERCADO ', '').replace('MCDO ', '').split(' Cfmj')[0].strip()
                # print(f"\nmercado actual: {mercado_actual}")
                niveles = [] #reinicia nivels
                niveles_mercado[mercado_actual] = niveles
                horas = False
                continue
            
            # Buscar filas con datos de tarifas (que contienen nivel y tipo)
            if (fila[1] and any(nivel in str(fila[1]) for nivel in ['Nivel', 'N ']) and fila[2] in ['A', 'B', 'C', 'D']) or (nivel_tension != ""):
                #print("fila-1")
                if fila[1] and any(nivel in str(fila[1]) for nivel in ['Nivel', 'N ']):
                    nivel_tension = fila[1].strip()
                    niveles.append(nivel_tension)
                    dicc_monomia = {}
                if fila[2] in ['A', 'B', 'C', 'D']:
                    tipo_tarifa = fila[2]
                if fila[2] == 'Horas:':
                    tipo_tarifa = ""
                
                
                
                # Extraer valores de franjas F1-F8, componentes del CU y las monomias sencillas
                valores = []
                for i in range(3, 21):  # Columnas F1-F8, componentes del CU y las monomias sencillas
                    if i < len(fila) and fila[i] and str(fila[i]).strip():
                        # Limpiar el valor (remover espacios extraños)
                        valor = str(fila[i]).replace(' ', '').replace('\xa0', '')
                        valor = self._safe_float(valor)
                        valores.append(valor)
                    else:
                        valores.append(None)
                # print(f"mercado: {mercado_actual}, nivel: {nivel_tension}, tipo_tarifa: {tipo_tarifa}, valores: {valores}")
                
                franjas = valores[0:8] # Columnas F1-F8
                
                #Compenentes del CU: Gm, Cm, PR, Dm
                componentes_cu = valores[8:12]
                keys_componentes_cu = ['Gm', 'Cm', 'PR', 'Dm']
                if any(val != "N.A." and val is not None for val in componentes_cu):  # condición: al menos un valor distinto de 'N.A.'
                    dicc_comp_cu = dict(zip(keys_componentes_cu, componentes_cu))
                if Tm != "" and Rm != "":
                    dicc_comp_cu['Tm'] = Tm
                    dicc_comp_cu['Rm'] = Rm
                
                # print(f"mercado: {mercado_actual}, nivel: {nivel_tension}, tipo_tarifa: {tipo_tarifa}, valores: {valores}")   
                # if mercado_actual == "CALI" and nivel_tension == "Nivel 1.1" and tipo_tarifa == "B":
                #     print(f"\nmercado: {mercado_actual}, nivel: {nivel_tension}, tipo_tarifa: {tipo_tarifa}, valores: {valores}")
                #     print(f"componentes_cu: {componentes_cu}")
                #     print(f"dicc_comp_cu: {dicc_comp_cu}")
                #     print(f"cu_base: {CU_base}")
                #     print(f"valor 12: {valores[12]}")
                
                if valores[12] != 'N.A.' and valores[12] is not None:
                    CU_base = valor = self._safe_float(valores[12])
                    
                monomias = valores[13:17]
                keys_monomias = ['A', 'B', 'C', 'D']
                if any(val != "N.A." and val is not None for val in monomias):  # condición: al menos un valor distinto de 'N.A.'
                    dicc_monomia = dict(zip(keys_monomias, monomias))

            
            
            # Solo incluir si tenemos todos los datos esenciales
            if tipo_tarifa != "" and any(f != 'N.A.' for f in franjas) and CU_base != "" and dicc_monomia:
                CU_aplicado = dicc_monomia[tipo_tarifa] #Monomia sencilla aplicado según tipo de tarifa
                
                if CU_aplicado is None:
                    # print(f"Advertencia: CU_aplicado es None para tipo_tarifa {tipo_tarifa} en mercado {mercado_actual}, nivel {nivel_tension}\n")
                    # print(f"dicc_monomia: {dicc_monomia}")
                    for key, value in dicc_monomia.items():
                        if value is not None:
                            CU_aplicado = value
            
                tarifas.append({
                    'mercado': mercado_actual,
                    'nivel_tension': nivel_tension,
                    'tipo_tarifa': tipo_tarifa,
                    'mes': fecha_doc.month,
                    'anio': fecha_doc.year,
                    'valores_franja': {
                        'F1': franjas[0],
                        'F2': franjas[1],
                        'F3': franjas[2],
                        'F4': franjas[3],
                        'F5': franjas[4],
                        'F6': franjas[5],
                        'F7': franjas[6],
                        'F8': franjas[7],
                    },
                    'cu_base': CU_base,
                    'cu_aplicado': CU_aplicado,
                    'componentes_cu': dicc_comp_cu,
                    'Cmfj': Cmfj,
                })
        
        return tarifas
    
    # def _fila_a_tarifa(self, fila: List, fecha_doc: date, titulo: str) -> Dict[str, Any]:
    #     """Convierte una fila de la tabla en un diccionario de tarifa"""
       
       
    #     mercado_actual = ""
    #     nivel_tension = ""
    #     tipo_tarifa = ""
    #     niveles_mercado = {}
    #     niveles = []
    #     horas =  False
    #     CU_base = ""
    #     dicc_monomia = {}
        
    #     # Buscar filas que contengan nombres de mercado
    #     if fila[0] and any(mercado in str(fila[0]) for mercado in ['MERCADO', 'MCDO']):
    #         mercado_actual = fila[0].replace('MERCADO ', '').replace('MCDO ', '').split(' Cfmj')[0].strip()
    #         print(f"\nmercado actual: {mercado_actual}")
    #         niveles = [] #reinicia nivels
    #         niveles_mercado[mercado_actual] = niveles
    #         horas = False
    #         return None  # No es una fila de tarifa, solo indica el mercado
    #     print(f"--mercado actual: {mercado_actual}, fila: {fila}")
    #     # Buscar filas con datos de tarifas (que contienen nivel y tipo)
    #     if (fila[1] and any(nivel in str(fila[1]) for nivel in ['Nivel', 'N ']) and fila[2] in ['A', 'B', 'C', 'D']) or (nivel_tension != ""):
    #         #print("fila-1")
    #         if fila[1] and any(nivel in str(fila[1]) for nivel in ['Nivel', 'N ']):
    #             nivel_tension = fila[1].strip()
    #             niveles.append(nivel_tension)
    #             dicc_monomia = {}
    #         if fila[2] in ['A', 'B', 'C', 'D']:
    #             tipo_tarifa = fila[2]
    #         if fila[2] == 'Horas:':
    #             tipo_tarifa = ""
            
            
            
    #         # Extraer valores de franjas F1-F8, componentes del CU y las monomias sencillas
    #         valores = []
    #         for i in range(3, 21):  # Columnas F1-F8, componentes del CU y las monomias sencillas
    #             if i < len(fila) and fila[i] and str(fila[i]).strip():
    #                 # Limpiar el valor (remover espacios extraños)
    #                 valor = str(fila[i]).replace(' ', '').replace('\xa0', '')
    #                 valores.append(valor)
    #             else:
    #                 valores.append('N.A.')
    #         franjas = valores[0:8] # Columnas F1-F8
    #         if valores[12] != 'N.A.':
    #             CU_base = valores[12]
    #         monomias = valores[14:18]
    #         #print(monomias)

    #         keys_monomias = ['A', 'B', 'C', 'D']
    #         if any(val != "N.A." for val in monomias):  # condición: al menos un valor distinto de 'N.A.'
    #             dicc_monomia = dict(zip(keys_monomias, monomias))
        
            
    #     #     # Solo incluir si tenemos todos los datos esenciales
    #     #     if tipo_tarifa != "" and any(f != 'N.A.' for f in franjas) and CU_base != "" and dicc_monomia:
    #     #         CU_aplicado = dicc_monomia[tipo_tarifa] #Monomia sencilla aplicado según tipo de tarifa
    #     #         resultados_tarifas.append({
    #     #             'Mercado': mercado_actual,
    #     #             'Nivel de Tension': nivel_tension,
    #     #             'Tipo de Tarifa': tipo_tarifa,
    #     #             'Mes': mes,
    #     #             'Año': anio,
    #     #             'F1': franjas[0],
    #     #             'F2': franjas[1],
    #     #             'F3': franjas[2],
    #     #             'F4': franjas[3],
    #     #             'F5': franjas[4],
    #     #             'F6': franjas[5],
    #     #             'F7': franjas[6],
    #     #             'F8': franjas[7],
    #     #             'CU_Base': CU_base,
    #     #             'CU_Aplicado': CU_aplicado,
    #     #             'Unidad de Tarifa': '$/kWh',
    #     #             'CS(Kwh/mes)': CS
    #     #         })
    #     # if fila[2] == 'Horas:':
    #     #     horas = True
    #     # pattern_nivel_horas = r'\b(1\.1|1\.2|1\.3|2|3|4)\b(?:\s*[\*\-%]*\s*(?:-|–)\s*[\*\-%]*\s*(1\.1|1\.2|1\.3|2|3|4))?'
    #     # nivel_tension_hora = []
    #     # if horas and ((fila[1] and re.search(pattern_nivel_horas, fila[1], re.IGNORECASE)) or (fila[0] and re.search(pattern_nivel_horas, fila[0], re.IGNORECASE))):
    #     #     # patron = re.compile(rf'\b{re.escape(fila[1].strip())}\b')
    #     #     if fila[1]:
    #     #         valores = [v.strip() for v in fila[1].split(',')]
    #     #     else:
    #     #         valores = [v.strip() for v in fila[0].split(',')]
    #     #     patron = re.compile(rf"(?<![\d\.])({'|'.join(map(re.escape, valores))})(?![\d\.])")
    #     #     niveles_mercado_actual = niveles_mercado[mercado_actual]
    #     #     coincidencias = [nivel for nivel in niveles_mercado_actual if patron.search(nivel)]
    #     #     nivel_tension_hora = coincidencias
    #     #     #print(f"nivel_tension_hora: {nivel_tension_hora}")
    #     # elif horas and str(fila[1]) == 'Todos':
    #     #     nivel_tension_hora = niveles_mercado[mercado_actual]
    #     #     #print(f"nivel_tension_hora: {nivel_tension_hora}")

    #     # if len(nivel_tension_hora) != 0:
    #     #     for nivel in nivel_tension_hora:
    #     #         horas_franjas = []
    #     #         for i in range(3, 11):  # Columnas F1-F8
    #     #             if i < len(fila) and fila[i] and str(fila[i]).strip():
    #     #                 # Limpiar el valor (remover espacios extraños)
    #     #                 valor = str(fila[i]).replace(' ', '').replace('\xa0', '')
    #     #                 horas_franjas.append(valor)
    #     #             else:
    #     #                 horas_franjas.append('N.A.')

    #     #         # Solo incluir si tenemos todos los datos esenciales
    #     #         if any(f != 'N.A.' for f in horas_franjas):
    #     #             resultados_horas.append({
    #     #                 'Mercado': mercado_actual,
    #     #                 'Nivel de Tension': nivel,
    #     #                 'Mes': mes,
    #     #                 'Año': anio,
    #     #                 'F1': horas_franjas[0],
    #     #                 'F2': horas_franjas[1],
    #     #                 'F3': horas_franjas[2],
    #     #                 'F4': horas_franjas[3],
    #     #                 'F5': horas_franjas[4],
    #     #                 'F6': horas_franjas[5],
    #     #                 'F7': horas_franjas[6],
    #     #                 'F8': horas_franjas[7]
    #     #             })
        
        
    #     # Solo incluir si tenemos todos los datos esenciales
    #     if tipo_tarifa != "" and any(f != 'N.A.' for f in franjas) and CU_base != "" and dicc_monomia:
    #         CU_aplicado = dicc_monomia[tipo_tarifa] #Monomia sencilla aplicado según tipo de tarifa
        
    #         return {
    #             'mercado': mercado_actual,
    #             'nivel_tension': nivel_tension,
    #             'tipo_tarifa': tipo_tarifa,
    #             'mes': fecha_doc.month,
    #             'anio': fecha_doc.year,
    #             'valores_franja': {
    #                 'F1': franjas[0],
    #                 'F2': franjas[1],
    #                 'F3': franjas[2],
    #                 'F4': franjas[3],
    #                 'F5': franjas[4],
    #                 'F6': franjas[5],
    #                 'F7': franjas[6],
    #                 'F8': franjas[7],
    #             },
    #             'cu_base': CU_base,
    #             'cu_aplicado': CU_aplicado,
    #         }
    
    def _extraer_metadata_archivo(self, pdf_path: Path) -> Dict[str, Any]:
        """Extrae metadatos del nombre del archivo PDF"""
        # Ejemplo: "tarifas_octubre_2024.pdf" -> mes=10, anio=2024
        nombre = pdf_path.stem.lower()
        
        meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        metadata = {'mes': None, 'anio': None}
        
        for mes_nombre, mes_num in meses.items():
            if mes_nombre in nombre:
                metadata['mes'] = mes_num
                break
        
        # Buscar año (4 dígitos)
        import re
        match = re.search(r'\d{4}', nombre)
        if match:
            metadata['anio'] = int(match.group())
        
        return metadata
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Convierte un valor a float de forma segura"""
        if value is None or value == '' or str(value).upper() == 'N.A.':
            return None
        try:
            # Limpiar formato numérico (remover comas, puntos de miles)
            valor_str = str(value).strip()
            if ',' in valor_str and '.' in valor_str:
                # Formato COP: 1.010,84
                valor_str = valor_str.replace('.', '').replace(',', '.')
            elif ',' in valor_str:
                # Formato: 810,75
                valor_str = valor_str.replace(',', '.')
            return float(valor_str)
        except (ValueError, AttributeError):
            return None