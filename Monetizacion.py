import http.server
import json
import urllib.parse
import urllib.request

API_BASE_URL = "https://api.exchangeratesapi.io/latest"

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
        url = f"{API_BASE_URL}?base={from_currency}"
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                if "rates" not in data:
                    return None
                exchange_rate = data["rates"].get(to_currency)
                if exchange_rate is None:
                    return None
                converted_amount = amount * exchange_rate
                return converted_amount
        except Exception as e:
            print(f"Error: {e}")
            return None

def run(server_class=http.server.HTTPServer, handler_class=CurrencyConverter, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__":
    run()
