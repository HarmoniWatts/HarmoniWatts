import pdfplumber
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger

class PDFParser:
    """Parsea PDFs de tarifas para extraer datos estructurados"""
    
    def parsear(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        Extrae tablas del PDF y las convierte en diccionarios.
        Retorna una lista de tarifas extraídas.
        """
        tarifas = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for num_pagina, pagina in enumerate(pdf.pages):
                logger.info(f"Procesando página {num_pagina + 1}")
                
                # Extraer tablas
                tablas = pagina.extract_tables()
                
                for tabla in tablas:
                    if self._es_tabla_tarifa(tabla):
                        tarifas.extend(self._parsear_tabla_tarifa(tabla, pdf_path))
        
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
        pdf_path: Path
    ) -> List[Dict[str, Any]]:
        """Parsea una tabla específica de tarifas"""
        if not tabla or len(tabla) < 2:
            return []
        
        # Convertir a DataFrame
        df = pd.DataFrame(tabla[1:], columns=tabla[0])
        
        # Limpiar datos
        df = df.dropna(how='all')
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        
        tarifas = []
        for _, row in df.iterrows():
            try:
                tarifa = self._fila_a_tarifa(row, pdf_path)
                if tarifa:
                    tarifas.append(tarifa)
            except Exception as e:
                logger.warning(f"Error parseando fila: {e}")
        
        return tarifas
    
    def _fila_a_tarifa(self, row: pd.Series, pdf_path: Path) -> Dict[str, Any]:
        """Convierte una fila del DataFrame en un diccionario de tarifa"""
        # Extraer metadatos del nombre del archivo
        metadata = self._extraer_metadata_archivo(pdf_path)
        
        return {
            'mercado': row.get('Mercado', '').strip(),
            'nivel_tension': row.get('Nivel de Tension', '').strip(),
            'tipo_tarifa': row.get('Tipo de Tarifa', '').strip(),
            'mes': metadata.get('mes'),
            'anio': metadata.get('anio'),
            'valores_franja': {
                'F1': self._safe_float(row.get('F1')),
                'F2': self._safe_float(row.get('F2')),
                'F3': self._safe_float(row.get('F3')),
                'F4': self._safe_float(row.get('F4')),
                'F5': self._safe_float(row.get('F5')),
                'F6': self._safe_float(row.get('F6')),
                'F7': self._safe_float(row.get('F7')),
                'F8': self._safe_float(row.get('F8')),
            },
            'cu_base': self._safe_float(row.get('CU_Base')),
            'cu_aplicado': self._safe_float(row.get('CU_Aplicado')),
            'cargo_consumo': self._safe_float(row.get('CS(Kwh/mes)')),
        }
    
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
            valor_str = str(value).replace(',', '').replace(' ', '')
            return float(valor_str)
        except (ValueError, AttributeError):
            return None