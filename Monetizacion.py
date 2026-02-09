import http.server
import json
import os
import urllib.parse
import urllib.request
import urllib.error
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, getcontext

API_BASE_URL = "https://openexchangerates.org/api/latest.json?app_id=8b0407458ab24c849cb91be32f3999bf"

class CurrencyConverter(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.serve_file("static/index.html", "text/html; charset=utf-8")
            return

        if self.path.startswith("/static/"):
            file_path = self.path.lstrip("/")
            if file_path.endswith(".css"):
                content_type = "text/css; charset=utf-8"
            elif file_path.endswith(".js"):
                content_type = "application/javascript; charset=utf-8"
            else:
                content_type = "application/octet-stream"
            self.serve_file(file_path, content_type)
            return

        self.send_error(404, "Recurso no encontrado")

    def do_POST(self):
        if self.path != "/convert":
            self.send_error(404, "Recurso no encontrado")
            return

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data)
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "JSON inválido"}).encode())
            return

        amount = data.get("amount")
        from_currency = data.get("from_currency")
        to_currency = data.get("to_currency")

        if amount is None or from_currency is None or to_currency is None:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Faltan parámetros en la solicitud"}).encode())
            return

        try:
            amount_decimal = Decimal(str(amount))
        except (InvalidOperation, TypeError):
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "El monto debe ser un número válido"}).encode())
            return

        if amount_decimal <= 0:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "El monto debe ser mayor a cero"}).encode())
            return

        converted_amount, exchange_rate, error_message = self.convert_currency(
            amount_decimal,
            from_currency,
            to_currency
        )

        if converted_amount is None:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": error_message or "No se pudo realizar la conversión de moneda"
            }).encode())
            return

        quantized_amount = converted_amount.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        quantized_rate = exchange_rate.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response_data = {
            "converted_amount": str(quantized_amount),
            "from_currency": from_currency,
            "to_currency": to_currency,
            "exchange_rate": str(quantized_rate)
        }
        self.wfile.write(json.dumps(response_data).encode())

    def convert_currency(self, amount, from_currency, to_currency):
        getcontext().prec = 28
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return amount, Decimal("1"), None

        url = f"{API_BASE_URL}&symbols={from_currency},{to_currency}"
        try:
            with urllib.request.urlopen(url) as response:
                if response.getcode() != 200:
                    print(f"Error al obtener tasas de cambio. Código de estado: {response.getcode()}")
                    return None, None, "Error al obtener tasas de cambio."
                
                data = json.loads(response.read().decode())
                if "error" in data:
                    print(f"Error en la respuesta de la API: {data['error']['message']}")
                    return None, None, data["error"]["message"]

                if "rates" not in data or to_currency not in data["rates"]:
                    print("No se encontraron tasas de cambio en la respuesta.")
                    return None, None, "No se encontraron tasas de cambio en la respuesta."

                rates = data["rates"]
                if from_currency not in rates or to_currency not in rates:
                    print("No se encontraron todas las tasas solicitadas.")
                    return None, None, "No se encontraron todas las tasas solicitadas."

                from_rate = Decimal(str(rates[from_currency]))
                to_rate = Decimal(str(rates[to_currency]))

                if from_currency == "USD":
                    exchange_rate = to_rate
                elif to_currency == "USD":
                    exchange_rate = Decimal("1") / from_rate
                else:
                    exchange_rate = to_rate / from_rate

                converted_amount = amount * exchange_rate
                return converted_amount, exchange_rate, None
        except urllib.error.HTTPError as e:
            print(f"Error HTTP al acceder a la API: {e}")
            return None, None, "Error HTTP al acceder a la API."
        except urllib.error.URLError as e:
            print(f"Error de URL al acceder a la API: {e}")
            return None, None, "Error de URL al acceder a la API."
        except Exception as e:
            print(f"Error inesperado: {e}")
            return None, None, "Error inesperado al procesar la conversión."
        
        return None, None, "No se pudo realizar la conversión."

    def serve_file(self, file_path, content_type):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_dir, file_path)
        if not os.path.isfile(full_path):
            self.send_error(404, "Recurso no encontrado")
            return

        with open(full_path, "rb") as file_handle:
            content = file_handle.read()

        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

def run(server_class=http.server.HTTPServer, handler_class=CurrencyConverter, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__":
    run()
