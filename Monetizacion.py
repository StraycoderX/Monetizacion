import http.server
import json
import urllib.parse
import urllib.request
import urllib.error

API_BASE_URL = "https://openexchangerates.org/api/latest.json?app_id=8b0407458ab24c849cb91be32f3999bf"

class CurrencyConverter(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        amount = data.get("amount")
        from_currency = data.get("from_currency")
        to_currency = data.get("to_currency")

        if amount is None or from_currency is None or to_currency is None:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Faltan parámetros en la solicitud"}).encode())
            return

        converted_amount = self.convert_currency(amount, from_currency, to_currency)

        if converted_amount is None:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "No se pudo realizar la conversión de moneda"}).encode())
            return

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response_data = {
            "converted_amount": converted_amount,
            "from_currency": from_currency,
            "to_currency": to_currency
        }
        self.wfile.write(json.dumps(response_data).encode())

    def convert_currency(self, amount, from_currency, to_currency):
        url = f"{API_BASE_URL}&base={from_currency}&symbols={to_currency}"
        try:
            with urllib.request.urlopen(url) as response:
                if response.getcode() != 200:
                    print(f"Error al obtener tasas de cambio. Código de estado: {response.getcode()}")
                    return None
                
                data = json.loads(response.read().decode())
                if "error" in data:
                    print(f"Error en la respuesta de la API: {data['error']['message']}")
                    return None

                if "rates" not in data or to_currency not in data["rates"]:
                    print("No se encontraron tasas de cambio en la respuesta.")
                    return None
                    
                exchange_rate = data["rates"][to_currency]
                converted_amount = amount * exchange_rate
                return converted_amount
        except urllib.error.HTTPError as e:
            print(f"Error HTTP al acceder a la API: {e}")
        except urllib.error.URLError as e:
            print(f"Error de URL al acceder a la API: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")
        
        return None

def run(server_class=http.server.HTTPServer, handler_class=CurrencyConverter, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__":
    run()
