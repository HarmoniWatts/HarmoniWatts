/**
 * Glosario de términos tarifarios (regulación colombiana, CREG 119/2007) que
 * muestran los botones informativos del módulo de tarifas y del dashboard.
 */
export interface TerminoGlosario {
  titulo: string;
  texto: string;
}

export const GLOSARIO = {
  tarifaActual: {
    titulo: 'Tarifa actual',
    texto:
      'Precio de cada kWh en la hora en curso según la franja horaria vigente. Multiplica tu consumo de esa hora por este valor para saber cuánto te cuesta.',
  },
  tipoTarifa: {
    titulo: 'Tipo de tarifa (A, B, C, D)',
    texto:
      'La comercializadora publica varias tarifas según el subsidio que aplica. ' +
      'A: tarifa plena, sin subsidio (estratos 4 a 6, usuarios no residenciales y el consumo de estratos 1 a 3 que supera la subsistencia). ' +
      'B: estrato 3 dentro del consumo de subsistencia. C: estrato 2. D: estrato 1. ' +
      'Entre más bajo el estrato, mayor el subsidio y menor el precio.',
  },
  estrato: {
    titulo: 'Estrato socioeconómico',
    texto:
      'Clasificación de 1 a 6 de tu vivienda. Determina si recibes subsidio (estratos 1, 2 y 3) o pagas tarifa plena; los estratos 5 y 6 pueden pagar además una contribución.',
  },
  subsistencia: {
    titulo: 'Consumo de subsistencia',
    texto:
      'Energía básica mensual que se subsidia a los estratos 1, 2 y 3: 130 kWh/mes en municipios a 1000 m.s.n.m. o más y 173 kWh/mes por debajo (en clima cálido se necesita más energía). El consumo por encima se cobra con tarifa plena.',
  },
  nivelTension: {
    titulo: 'Nivel de tensión',
    texto:
      'Voltaje al que está conectada la vivienda. Los hogares suelen estar en Nivel 1 (baja tensión). N1_1: los transformadores y redes son del operador de red; N1_2 o N1_2_1_3: parte de los activos son del usuario; "50 %": propiedad compartida.',
  },
  comercializadora: {
    titulo: 'Comercializadora',
    texto:
      'Empresa que te vende la energía, publica las tarifas y te factura. En HarmoniWatts las tarifas son de ENERTOTAL S.A. E.S.P.',
  },
  operadorRed: {
    titulo: 'Operador de red',
    texto:
      'Empresa dueña de las redes de distribución de tu región (por ejemplo Enel, EPM, EMCALI o Afinia). Lleva la energía hasta tu vivienda y cobra por usar su red; por eso la tarifa cambia de una región a otra.',
  },
  ciudad: {
    titulo: 'Ciudad y mercado',
    texto:
      'El municipio de la vivienda define su mercado de comercialización: la zona atendida por un mismo operador de red, donde aplica una misma tarifa.',
  },
  franjas: {
    titulo: 'Franjas horarias',
    texto:
      'El día se divide en franjas (F1, F2…) con precio distinto. Valle: horas de baja demanda, el precio más bajo. Media: demanda intermedia. Punta: horas de mayor demanda del sistema, el precio más alto. Mover consumo de punta a valle reduce tu factura.',
  },
  graficoPrecios: {
    titulo: 'Precios por franja — 24 h',
    texto:
      'Precio del kWh en cada hora del día, coloreado por tipo de hora. El eje empieza cerca del precio mínimo para que se noten las diferencias entre franjas, que suelen ser pequeñas.',
  },
  periodo: {
    titulo: 'Período y versión',
    texto:
      'Las tarifas se publican cada mes. Si la comercializadora corrige una publicación, sale una versión nueva (v2, v3…) que reemplaza a la anterior.',
  },
  costoUnitario: {
    titulo: 'Costo unitario (CU) o monomía',
    texto:
      'Precio único del kWh sin distinguir la hora. Es la suma de los componentes: generación + transmisión + distribución + comercialización + pérdidas + restricciones.',
  },
  rangoDia: {
    titulo: 'Rango del día',
    texto: 'Diferencia entre la hora más barata y la más cara del día, en COP/kWh y en porcentaje.',
  },
  componentes: {
    titulo: 'Componentes del costo',
    texto:
      'Partes que forman el precio de la energía según la CREG. Pasa el cursor o toca el botón de cada componente para ver qué representa.',
  },
  Gm: {
    titulo: 'Generación (G)',
    texto: 'Costo de comprar la energía a las plantas generadoras (hidroeléctricas, térmicas, solares…). Suele ser el componente más grande.',
  },
  Tm: {
    titulo: 'Transmisión (T)',
    texto: 'Uso del Sistema de Transmisión Nacional: las líneas de alta tensión que llevan la energía desde las plantas hasta las regiones.',
  },
  Dm: {
    titulo: 'Distribución (D)',
    texto: 'Uso de las redes locales del operador de red (subestaciones, postes, transformadores) hasta tu vivienda.',
  },
  Cm: {
    titulo: 'Comercialización (C)',
    texto: 'Costo de la comercializadora por atenderte: medición, facturación, recaudo y atención al cliente.',
  },
  PRm: {
    titulo: 'Pérdidas (PR)',
    texto: 'Energía que se pierde en el camino (calentamiento de redes, conexiones ilegales) y que la regulación reconoce dentro de la tarifa.',
  },
  Rm: {
    titulo: 'Restricciones (R)',
    texto: 'Costos para mantener la seguridad del sistema eléctrico, por ejemplo encender plantas más costosas cuando hay limitaciones en la red.',
  },
  Cfmj: {
    titulo: 'Cargo fijo (Cf)',
    texto: 'Valor mensual fijo de comercialización que se cobra por factura, independiente de cuánta energía consumas (COP/factura, no COP/kWh).',
  },
  COT: {
    titulo: 'Costo opción tarifaria (COT)',
    texto: 'Cobro para recuperar alzas de tarifa que se aplazaron en años anteriores (opción tarifaria) y se pagan de forma gradual.',
  },
  calendario: {
    titulo: 'Calendario de tarifas',
    texto:
      'Tarifas publicadas mes a mes. Cada mes muestra el precio promedio del día y el rango mínimo–máximo en COP/kWh. Haz clic en un mes publicado para ver su detalle; los meses sin publicar aparecen punteados.',
  },
  numeroContrato: {
    titulo: 'Número de contrato',
    texto:
      'Identificador de tu servicio con la comercializadora (también llamado número de cuenta o NIU). Aparece en la factura de energía.',
  },
  costoEstimado: {
    titulo: 'Costo estimado',
    texto:
      'Consumo de cada hora multiplicado por el precio de esa hora según la tarifa de tu vivienda. No incluye el cargo fijo, impuestos ni otros cobros de la factura.',
  },
} satisfies Record<string, TerminoGlosario>;

export type TerminoClave = keyof typeof GLOSARIO;
