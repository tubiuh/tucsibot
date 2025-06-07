print("--- PASO 1: Iniciando la prueba mínima. ---")

try:
    # Intentamos importar solo la pieza más importante de la librería
    from telegram.ext import Application
    print("--- PASO 2: ¡ÉXITO! La librería 'telegram' se pudo importar.")

except Exception as e:
    print("\n--- PASO 2: ¡FALLO! No se pudo importar la librería. ---")
    print(f"--- TIPO DE ERROR: {type(e).__name__} ---")
    print(f"--- MENSAJE: {e} ---")
    import traceback
    traceback.print_exc()

print("--- PASO 3: Fin de la prueba. ---")