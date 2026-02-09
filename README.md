# Monetizacion
Este código crea un servidor HTTP simple que puede realizar conversiones de moneda a partir de las solicitudes POST que recibe en el endpoint `/convert`.

## Configuración
Necesitas un API key de Open Exchange Rates y exportarlo como variable de entorno:

```bash
export OPENEXCHANGERATES_APP_ID="TU_API_KEY"
python Monetizacion.py
```
