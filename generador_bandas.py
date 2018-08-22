import numpy as np
import pandas as pd

workfile = pd.read_csv('totalWorkFile.csv')
sucursales_activas = pd.read_csv('SucursalesActivas.csv')
margenes = pd.read_csv('Margenes.csv')

def generar_bandas(lambda1, lambda2, lambda3, promedio_stock, sigma_stock,
margen, costo_remesa=3.52, costo_interes=0.025):
    """
    Genera las recomendaciones de cotas
    inferiores (L) y superiores (U), junto
    al saldo óptimo (Z) de dinero
    a mantener en cada sucursal, dado
    un set de parámetros "lambda".
    """
    L = lambda1 * sigma_stock + promedio_stock
    Z = L + lambda2 * ((3 * costo_remesa * sigma_stock ** 2) /
    (4 * costo_interes)) ** (1 / 3)
    U = 3 * Z * lambda3 - 2 * L

    return L, Z, U

def contar_remesas(saldo_apertura, L, Z, U):
    """
    Para un set de cotas L y U,
    cuenta el número de remesas que se hubieran
    realizado en un año en particular, de haberse
    aplicado estos límites.
    """
    num_remesas = 0
    for j in range(len(saldo_apertura)):
        saldo = saldo_apertura[j]
        if saldo < L:
            saldo = Z
            num_remesas += 1
        if saldo > U:
            saldo = Z
            num_remesas += 1
    return num_remesas

# Espacio de parámetros a explorar
lambda1_list = np.linspace(-20, 20, 50)
lambda2_list = np.linspace(-20, 20, 50)
lambda3_list = np.linspace(-20, 20, 50)

# Lista en donde se guardarán la bandas óptimos para
# cada sucursal
bandas_total = []

# Loop sobre todas las sucursales activas
cod_sucursal = sucursales_activas['Sucursal'].values
for i in cod_sucursal:
    print('Calculando bandas para sucursal: ' + str(i), end='\r')
    # Filtrar datos, no considerar años 2017 ni 2018
    df = workfile.loc[(workfile['Sucursal'] == i)
                    & (workfile['Year'] != 2017)
                    & (workfile['Year'] != 2018)]

    bandas_sucursal = []

    # Calcular promedio y desviación estándar del saldo diario,
    # para usar en cálculo de bandas óptimas
    apertura = df['SaldoApertura'].values
    UF = df['UF'].values
    apertura_UF = apertura / UF
    promedio_stock = np.mean(apertura_UF)
    sigma_stock = np.std(apertura_UF)

    # Margen de dinero máximo que está asegurado en cada
    # sucursal. Se usará para calcular la banda inferior óptima
    margen = margenes.loc[margenes['Oficina'] == i]['Margen']
    if margen.empty:
        continue
    else: margen = margen.values

    # Loop sobre todas las combinaciones de lambdas del
    # espacio de parámetros
    for lambda1 in lambda1_list:
        for lambda2 in lambda2_list:
            for lambda3 in lambda3_list:

                # Calcular las bandas óptimas para esta combinación de lambdas
                L, Z, U = generar_bandas(lambda1=lambda1, lambda2=lambda2, lambda3=lambda3,
                promedio_stock=promedio_stock, sigma_stock=sigma_stock, margen=margen)

                # Relaciones y restricciones que deben cumplir las bandas óptimas
                restricciones = (L < Z < U) & (L > 0) & (Z - L < U - Z) & (U < 1.3 * margen)

                # Si la combinación de lambdas cumple las restricciones, calcular
                # el número de remesas que habría que realizar en el año de prueba
                # (2017), de aplicarse estas bandas óptimas
                if restricciones:
                    df_horizonte = workfile.loc[(workfile['Sucursal'] == i)
                                    & (workfile['Year'] != 2017)]
                    apertura_horizonte = df_horizonte['SaldoApertura'] / df_horizonte['UF']
                    num_remesas = contar_remesas(apertura_horizonte.values, L, Z, U)
                    bandas_sucursal.append([lambda1, lambda2, lambda3, L, Z, U, num_remesas])

    # De todas las posibles combinaciones de lambdas que minimizan el
    # número de remesas, escoger una al azar
    if not bandas_sucursal: continue
    bandas_sucursal = np.asarray(bandas_sucursal)
    bandas_sucursal = bandas_sucursal[np.where(bandas_sucursal == np.min(bandas_sucursal[:, -1]))[0]]
    if len(bandas_sucursal > 1):
        bandas_sucursal = bandas_sucursal[np.random.randint(len(bandas_sucursal))]

    bandas_total.append(bandas_sucursal)

# Guardar bandas óptimas para cada sucursal en un Pandas DataFrame
# y guardar a un archivo csv
df_bandas = pd.DataFrame(np.asarray(bandas_total),
            columns=['lambda1', 'lambda2', 'lambda3', 'L', 'Z', 'U', 'num_remesas'])
            
outfile_name = 'bandas_sucursales.csv'
df_bandas.to_csv(outfile_name, index=False)
