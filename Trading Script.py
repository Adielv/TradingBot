import time
import hashlib
import hmac
import requests
from tabulate import tabulate

# Configura tu API Key y API Secret aquí
api_key = ''
api_secret = ''

def generate_signature(data):
    return hmac.new(api_secret.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()

def get_tokens_in_min_max(days):
    while True:
        # URL base y endpoints para los datos de Binance
        base_url = 'https://fapi.binance.com'
        endpoint_tickers = '/fapi/v1/ticker/24hr'
        endpoint_funding = '/fapi/v1/fundingRate'

        try:
            # Realizar solicitudes HTTP para datos de tickers y tasas de financiamiento
            response_tickers = requests.get(base_url + endpoint_tickers)
            response_funding = requests.get(base_url + endpoint_funding)
            response_tickers.raise_for_status()
            response_funding.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud HTTP: {e}")
            continue

        # Convertir los datos en formato JSON
        data_tickers = response_tickers.json()
        data_funding = response_funding.json()

        # Obtener la marca de tiempo actual y el límite de tiempo
        current_timestamp = int(time.time() * 1000)
        time_limit = current_timestamp - (days * 24 * 60 * 60 * 1000)

        # Crear un diccionario de tasas de financiamiento por símbolo
        funding_rates = {item['symbol']: f"{float(item['fundingRate']) * 100:.2f}%" for item in data_funding}

        # Lista para almacenar datos de tokens con mínimos y máximos históricos
        token_data_min = []
        token_data_max = []

        # Definir un umbral de volumen mínimo (ajusta este valor según tus necesidades)
        volumen_minimo = 100000  # Por ejemplo, 100,000 BTC

        # Iterar a través de los datos de tickers
        for item in data_tickers:
            # Verificar si los datos necesarios están presentes en el ticker
            if all(key in item for key in ('lowPrice', 'lastPrice', 'closeTime', 'priceChangePercent', 'volume')):
                # Obtener valores clave
                low_price = float(item['lowPrice'])
                last_price = float(item['lastPrice'])
                price_change_percent = float(item['priceChangePercent'].rstrip('%'))  # Eliminar el símbolo "%"
                timestamp = int(item['closeTime'])
                volume = float(item['volume'])

                # Calcular la cantidad comprada y vendida
                quantity_bought = 0
                quantity_sold = 0

                # Verificar si el precio bajo es menor que el precio actual, el cambio de precio es negativo,
                # y el volumen operado supera el umbral mínimo
                if low_price < last_price and price_change_percent < 0 and timestamp > time_limit and volume > volumen_minimo:
                    quantity_bought = last_price
                    token_data_min.append([
                        item['symbol'],
                        f"{price_change_percent:.2f}%",
                        "{:,.2f}".format(last_price),
                        "{:,.2f}".format(quantity_bought),
                        "{:,.2f}".format(quantity_sold),
                        "{:,.2f}".format(volume),
                        funding_rates.get(item['symbol'], "N/A")
                    ])

                # Verificar si el precio alto es mayor que el precio actual, el cambio de precio es positivo,
                # y el volumen operado supera el umbral mínimo
                if float(item['highPrice']) > last_price and price_change_percent > 0 and timestamp > time_limit and volume > volumen_minimo:
                    quantity_sold = last_price
                    token_data_max.append([
                        item['symbol'],
                        f"{price_change_percent:.2f}%",
                        "{:,.2f}".format(last_price),
                        "{:,.2f}".format(quantity_bought),
                        "{:,.2f}".format(quantity_sold),
                        "{:,.2f}".format(volume),
                        funding_rates.get(item['symbol'], "N/A")
                    ])

        # Ordenar los datos por cambio de precio (tanto mínimos como máximos)
        token_data_min.sort(key=lambda x: float(x[1].rstrip('%')))
        token_data_max.sort(key=lambda x: float(x[1].rstrip('%')), reverse=True)

        # Encabezados de la tabla
        headers = ["Símbolo", "Porcentaje de Cambio", "Precio Actual", "Cantidad Comprada", "Cantidad Vendida", "Volumen Operado", "Tasa de Financiamiento"]

        # Establecer formato de tabla para una mejor presentación
        tablefmt = "pretty"

        # Limpiar la pantalla antes de imprimir
        print("\033c")

        # Mostrar la tabla de tokens con mínimos históricos
        print("Tokens con Mínimos Históricos:")
        print(tabulate(token_data_min[:10], headers, tablefmt=tablefmt))
        print("\n")

        # Mostrar la tabla de tokens con máximos históricos
        print("Tokens con Máximos Históricos:")
        print(tabulate(token_data_max[:50], headers, tablefmt=tablefmt))

        # Esperar 0.01 segundos antes de la próxima actualización
        time.sleep(0.01)

def get_order_book(symbol, limit):
    while True:
        # URL base y endpoint para el libro de órdenes
        base_url = 'https://fapi.binance.com'
        endpoint_order_book = f'/fapi/v1/depth?symbol={symbol}&limit={limit}'

        try:
            # Realizar solicitud HTTP para el libro de órdenes
            response_order_book = requests.get(base_url + endpoint_order_book)
            response_order_book.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud HTTP: {e}")
            continue

        # Obtener datos del libro de órdenes en formato JSON
        order_book_data = response_order_book.json()

        # Mostrar el libro de órdenes
        bids = order_book_data.get('bids', [])
        asks = order_book_data.get('asks', [])

        tablefmt = "pretty"  # Establecer formato de tabla

        # Limpiar la pantalla antes de imprimir
        print("\033c")

        print(f"Libro de Órdenes para el par {symbol} (Limit: {limit}):\n")
        print(tabulate(bids, headers=["Precio (BID)", "Cantidad (BID)"], tablefmt=tablefmt))
        print("\n")
        print(tabulate(asks, headers=["Precio (ASK)", "Cantidad (ASK)"], tablefmt=tablefmt))

        # Esperar 1 segundo antes de la próxima actualización
        time.sleep(15)

def main():
    while True:
        print("1. Obtener Tokens con Mínimos y Máximos Históricos")
        print("2. Ver el Libro de Órdenes para un Par de Criptomonedas")
        print("3. Salir")
        seleccion = input("Selecciona una opción: ")

        if seleccion == '1':
            num_days = int(input("Ingresa el número de días: "))
            get_tokens_in_min_max(num_days)
        elif seleccion == '2':
            symbol_to_view = input("Ingresa el símbolo del par de criptomonedas para ver el libro de órdenes (por ejemplo, 'BTCUSDT'): ")
            limit = input("Ingresa la cantidad de precios que deseas ver en el libro de órdenes: ")
            try:
                limit = int(limit)
                get_order_book(symbol_to_view, limit)
            except ValueError:
                print("El límite debe ser un número entero.")
        elif seleccion == '3':
            break
        else:
            print("Opción no válida. Por favor, selecciona una opción válida.")

if __name__ == "__main__":
    main()
