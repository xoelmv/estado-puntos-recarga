# estado-puntos-recarga

Fotos periódicas del estado en tiempo real (libre / ocupada / fuera de servicio) de las
estaciones de recarga de España que publica [Electromaps](https://www.electromaps.com).

- `estado.py`: toma una foto y la guarda como `estado/AAAA-MM-DDTHHMMSSZ.csv.gz`
  (`instante_utc, site_id, potencia, estado`; códigos en la cabecera del script).
- `.github/workflows/estado.yml`: una foto cada 30 minutos con GitHub Actions.
- Las fotos se guardan en la rama [`datos`](../../tree/datos).

```
pip install requests
python3 estado.py --dir estado
```
