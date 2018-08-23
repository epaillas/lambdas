import numpy as np
import pandas as pd

workfile = pd.read_csv('totalWorkFile.csv')
sucursales_activas = pd.read_csv('SucursalesActivas.csv')
margenes = pd.read_csv('Margenes.csv')

def generar_bandas(lambda1, lambda2, lambda3, apertura,
margen, costo_remesa=3.52, costo_interes=0.025):
    """
    Genera las recomendaciones de cotas
    inferiores (L) y superiores (U), junto
    al saldo óptimo (Z) de dinero
    a mantener en cada sucursal, dado
    un set de parámetros "lambda".
    """
    L = lambda1 * np.std(apertura) + np.mean(apertura)
    Z = L + lambda2 * ((3 * costo_remesa * np.std(apertura) ** 2) /
    (4 * costo_interes)) ** (1 / 3)
    U = 3 * Z * lambda3 - 2 * L

    return L, Z, U

def contar_remesas(flujo, apertura, L, Z, U):
    """
    Para un set de cotas L y U,
    cuenta el número de remesas que se hubieran
    realizado en un año en particular, de haberse
    aplicado estos límites.
    """
    num_remesas = 0
    saldo = apertura[0]
    for i in range(len(flujo)):
        saldo += flujo[i]
        if saldo < L:
            saldo = Z
            num_remesas += 1
        if saldo > U:
            saldo = Z
            num_remesas += 1
    return num_remesas

# Espacio de parámetros a explorar
lambda1 = np.random.normal(loc=1.0, scale=5.0, size=50)
lambda2 = np.random.normal(loc=1.0, scale=5.0, size=50)
lambda3 = np.random.normal(loc=1.0, scale=5.0, size=50)

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
    apertura = df['SaldoApertura'].values / df['UF'].values

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
                apertura=apertura, margen=margen)

                # Relaciones y restricciones que deben cumplir las bandas óptimas
                restricciones = (L < Z < U) & (L > 0) & (Z - L < U - Z) & (U < 1.3 * margen)

                # Si la combinación de lambdas cumple las restricciones, calcular
                # el número de remesas que habría que realizar en el año horizonte
                # (2017), de aplicarse estas bandas óptimas
                if restricciones:
                    df_horizonte = workfile.loc[(workfile['Sucursal'] == i) & (workfile['Year'] == 2017)]
                    apertura_horizonte = df_horizonte['SaldoApertura'].values / df_horizonte['UF'].values
                    flujo_horizonte = df_horizonte['SaldoApertura'].values / df_horizonte['UF'].values
                    num_remesas = contar_remesas(flujo=flujo_horizonte, apertura=apertura_horizonte, L=L, Z=Z, U=Z)
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
