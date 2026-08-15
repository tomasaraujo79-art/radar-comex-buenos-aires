# Automatizacion cloud del Radar COMEX

Esta variante corre aunque la PC este apagada usando GitHub Actions y publica un sitio estatico en GitHub Pages.

Repositorio:

- https://github.com/tomasaraujo79-art/radar-comex-buenos-aires

Sitio publico:

- https://tomasaraujo79-art.github.io/radar-comex-buenos-aires/

## Que queda automatizado

- Horario: todos los dias a las 08:00 de Buenos Aires.
- Ejecucion: GitHub Actions en la nube.
- Publicacion: GitHub Pages.
- Resultado: un sitio publico con botones `Postularme en el aviso`.

## Pasos para activarlo

1. Ir a `Actions > Radar COMEX cloud`.
2. Ejecutar `Run workflow` si queres forzar una actualizacion manual.

Despues de eso, GitHub lo corre solo todos los dias a las 08:00 aunque tu PC este apagada.

## Archivo clave

El workflow esta en `.github/workflows/radar-comex-cloud.yml`.

## Prueba local opcional

```powershell
cd C:\Users\PCBEAT\OneDrive\Documentos\ChatGPT\yo\radar_comex
.\scripts\export_cloud_site.ps1
```

Eso genera `cloud_site/index.html`, el mismo sitio que GitHub Pages publica.
