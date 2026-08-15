# Radar COMEX Buenos Aires

Sistema local para buscar, clasificar y priorizar empleos de comercio exterior, importaciones, exportaciones, aduana y logistica internacional cerca de Belgrano.

## Que hace

- Recolecta avisos desde fuentes publicas accesibles: LinkedIn publico, paginas ATS/careers y una lista semilla de avisos reales que se revalidan en cada corrida.
- Detecta portales que bloquean automatizacion con login, CAPTCHA o Cloudflare y los informa como fuente limitada.
- Clasifica relevancia COMEX, experiencia requerida y seniority de entrada.
- Estima distancia y tiempo desde Belgrano, CABA, con coordenadas locales.
- Puntua compatibilidad con el CV de Victoria: RRII, comercio internacional, ingles avanzado, Office, tareas administrativas, documentacion, organizacion y atencion bilingue.
- Guarda todo en SQLite, genera reporte Markdown y expone dashboard web.

## Uso rapido

```powershell
cd C:\Users\PCBEAT\OneDrive\Documentos\ChatGPT\yo\radar_comex
.\scripts\run_daily.ps1
.\scripts\start_dashboard.ps1
```

Dashboard:

- API: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:5173`

## Automatizacion diaria

Para registrar una tarea de Windows a las 09:00:

```powershell
cd C:\Users\PCBEAT\OneDrive\Documentos\ChatGPT\yo\radar_comex
.\scripts\register_windows_task.ps1
```

## Configuracion

Copiar `.env.example` a `.env` si se quieren activar integraciones:

- `OPENROUTESERVICE_API_KEY`: rutas reales en vez de estimacion local.
- SMTP: notificaciones por email.
- Telegram bot: notificaciones por chat.

Los filtros principales estan en `config.yaml`: queries, fuentes, ubicaciones, score minimo y maximo de viaje.

## Limitaciones honestas

Algunos portales de empleo, como Bumeran e Indeed, pueden bloquear solicitudes automatizadas. El radar no intenta evadir CAPTCHA ni login; registra la limitacion y sigue con fuentes publicas/ATS.
