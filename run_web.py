"""
Arranque del servidor web.

Uso:
    python run_web.py

Luego abre http://127.0.0.1:8000 en el navegador.
"""
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("Shorts Generator - Servidor Web")
    print("=" * 60)
    print("Abre http://127.0.0.1:8000 en tu navegador")
    print("Pulsa Ctrl+C para detener")
    print("=" * 60)
    uvicorn.run(
        "web.server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )
