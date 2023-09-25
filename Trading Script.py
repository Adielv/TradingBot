import time
import hashlib
import hmac
import requests
from tabulate import tabulate

# Configura tu API Key y API Secret aquí
api_key = 'gLq96rEqMIjoi7INAwvCqZ3pk0cZ9PUAeVH5Dgjkw6tDsk8d9QIHsgItzyPCA3tX'
api_secret = '9I8fkZcupmRkS10sNL2z1r99Cuvz3AVnKDctmX4loJ3NYXBYSyCowsX3qQ3dIX1i'

def generate_signature(data):
    return hmac.new(api_secret.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()

def get_data_from_binance(endpoint):
    base_url = 'https://fapi.binance.com'
    url = f'{base_url}{endpoint}'

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud HTTP: {e}")
        return None

def get_tokens_in_min_max(days):
    while True:
        endpoint_tickers = '/fapi/v1/ticker/24hr'
        endpoint_funding = '/fapi/v1/fundingRate'

        data_tickers = get_data_from_binance(endpoint_tickers)
        data_funding = get_data_from_binance(endpoint_funding)

        if data_tickers is None or data_funding is None:
            continue

        current_timestamp = int(time.time() * 1000)
        time_limit = current_timestamp - (days * 24 * 60 * 60 * 1000)

        funding_rates = {item['symbol']: f"{float(item['fundingRate']) * 100:.2f}%" for item in data_funding}
        token_data_min = []
        token_data_max = []
        volumen_minimo = 100000  # Ajusta este valor según tus necesidades

        for item in data_tickers:
            if all(key in item for key in ('lowPrice', 'lastPrice', 'closeTime', 'priceChangePercent', 'volume')):
                low_price = float(item['lowPrice'])
                last_price = float(item['lastPrice'])
                price_change_percent = float(item['priceChangePercent'].rstrip('%'))
                timestamp = int(item['closeTime'])
                volume = float(item['volume'])
                quantity_bought = 0
                quantity_sold = 0

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

        token_data_min.sort(key=lambda x: float(x[1].rstrip('%')))
        token_data_max.sort(key=lambda x: float(x[1].rstrip('%')), reverse=True)

        headers = ["Símbolo", "Porcentaje de Cambio", "Precio Actual", "Cantidad Comprada", "Cantidad Vendida", "Volumen Operado", "Tasa de Financiamiento"]
        tablefmt = "pretty"

        print("\033c")
        print("Tokens con Mínimos Históricos:")
        print(tabulate(token_data_min[:10], headers, tablefmt=tablefmt))
        print("\n")
        print("Tokens con Máximos Históricos:")
        print(tabulate(token_data_max[:70], headers, tablefmt=tablefmt))
        time.sleep(5)

def get_order_book(symbol, limit):
    while True:
        endpoint_order_book = f'/fapi/v1/depth?symbol={symbol}&limit={limit}'
        order_book_data = get_data_from_binance(endpoint_order_book)

        if order_book_data is None:
            continue

        bids = order_book_data.get('bids', [])
        asks = order_book_data.get('asks', [])
        tablefmt = "pretty"

        # Ordena las listas de bids y asks en función del tamaño de las órdenes
        bids.sort(key=lambda x: float(x[1]), reverse=True)
        asks.sort(key=lambda x: float(x[1]), reverse=True)

        print("\033c")
        print(f"Libro de Órdenes para el par {symbol} (Limit: {limit}):\n")

        # Muestra las órdenes de compra (bids)
        print("Órdenes de Compra (BID):")
        print(tabulate(bids, headers=["Precio (BID)", "Cantidad (BID)"], tablefmt=tablefmt))
        print("\n")

        # Muestra las órdenes de venta (asks)
        print("Órdenes de Venta (ASK):")
        print(tabulate(asks, headers=["Precio (ASK)", "Cantidad (ASK)"], tablefmt=tablefmt))
        time.sleep(5)

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
