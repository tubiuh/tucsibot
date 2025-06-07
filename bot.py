import logging
import asyncio
import os
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import datetime
# import pytz

# --- CONFIGURACIÓN INICIAL ---

# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
# ▼▼▼ REEMPLAZA 'TU_TOKEN_AQUI' CON EL TOKEN REAL DE BOTFATHER ▼▼▼
# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
TOKEN = os.environ.get('TELEGRAM_TOKEN')
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

# Configura la zona horaria de Paraguay
# TIMEZONE = pytz.timezone('America/Asuncion')

# Configura el logging para ver errores en la consola
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- GESTIÓN DE DATOS ---
chat_data = {}

def inicializar_datos_chat(chat_id):
    """Inicializa o resetea los datos para un chat específico."""
    chat_data[chat_id] = {
        "total_recibido": 0,
        "total_enviado": 0,
        "historial_recibido": [],
        "historial_enviado": []
    }
    logger.info(f"Datos inicializados/reseteados para el chat {chat_id}")

# --- FORMATEO Y ENVÍO DE RESUMEN ---
def format_number(n):
    """Formatea un número con separador de miles de punto y sin decimales."""
    return f"{n:,.0f}".replace(",", ".")

async def enviar_resumen(chat_id: int, bot: Bot):
    """Construye y envía el mensaje de resumen formateado."""
    if chat_id not in chat_data:
        inicializar_datos_chat(chat_id)
    
    data = chat_data[chat_id]
    total_recibido = data["total_recibido"]
    total_enviado = data["total_enviado"]
    total_en_cuenta = total_recibido - total_enviado

    recibidos_list = "\n".join([f"✔ {format_number(monto)}" for monto in data["historial_recibido"][:5]])
    enviados_list = "\n".join([f"✔ {format_number(monto)}" for monto in data["historial_enviado"][:5]])

    # ... (código anterior)

    mensaje = (
        "----------------------------------------------------\n"
        f"• Dinero en cuenta: *{format_number(total_en_cuenta)}*\n"
        "----------------------------------------------------\n"
        f"• Dinero recibido: {format_number(total_recibido)}\n"
        f"• Dinero enviado: {format_number(total_enviado)}\n"
        "----------------------------------------------------\n"
        "- Recibido:\n"
        f"{recibidos_list}\n"
        "----------------------------------------------------\n"
        "- Enviado:\n"
        f"{enviados_list}\n"
        "----------------------------------------------------"
    )
    # ... (código siguiente)
    await bot.send_message(chat_id=chat_id, text=mensaje, parse_mode=ParseMode.MARKDOWN)

# --- COMANDOS DEL BOT ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /start."""
    chat_id = update.effective_chat.id
    if chat_id not in chat_data:
        inicializar_datos_chat(chat_id)
    mensaje_bienvenida = (
        "¡Hola! Soy tu bot de conteo financiero. 🤖\n\n"
        "Puedes usarme para llevar la cuenta en este grupo:\n\n"
        "➡️ Envía un número positivo para registrar un ingreso (ej: `+15000`).\n"
        "➡️ Envía un número negativo para registrar un egreso (ej: `-5000`).\n\n"
        "Comandos disponibles:\n"
        "✅ /resumen - Muestra el estado actual de la cuenta.\n"
        "🔄 /resetear - Reinicia todos los contadores a cero.\n\n"
        "Además, reseteo la cuenta automáticamente todos los días a la medianoche (hora de Paraguay)."
    )
    await update.message.reply_text(mensaje_bienvenida, parse_mode=ParseMode.MARKDOWN)

async def resumen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /resumen."""
    await enviar_resumen(update.effective_chat.id, context.bot)

async def resetear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /resetear."""
    chat_id = update.effective_chat.id
    inicializar_datos_chat(chat_id)
    await update.message.reply_text("✅ ¡Cuenta reseteada con éxito! Todos los contadores vuelven a cero.")

# --- PROCESAMIENTO DE MENSAJES DE TRANSACCIONES ---
async def procesar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lee mensajes de texto y los procesa como ingresos o egresos."""
    chat_id = update.effective_chat.id
    mensaje = update.message.text.strip()
    if chat_id not in chat_data:
        inicializar_datos_chat(chat_id)
    valor = 0
    es_transaccion = False
    try:
        valor_limpio = mensaje.replace('.', '').replace(',', '.')
        valor = int(float(valor_limpio))
    except ValueError:
        return
    if mensaje.startswith('+') and valor > 0:
        chat_data[chat_id]["total_recibido"] += valor
        chat_data[chat_id]["historial_recibido"].insert(0, valor)
        es_transaccion = True
    elif mensaje.startswith('-') and valor < 0:
        valor_absoluto = abs(valor)
        chat_data[chat_id]["total_enviado"] += valor_absoluto
        chat_data[chat_id]["historial_enviado"].insert(0, valor_absoluto)
        es_transaccion = True
    if es_transaccion:
        await enviar_resumen(chat_id, context.bot)

# --- TAREA PROGRAMADA DE RESETEO DIARIO ---
async def reseteo_diario(context: ContextTypes.DEFAULT_TYPE):
    """Función que se ejecuta diariamente para resetear todos los chats."""
    chat_ids_a_resetear = list(chat_data.keys())
    for chat_id in chat_ids_a_resetear:
        inicializar_datos_chat(chat_id)
        mensaje = "☀️ ¡Buenos días! He reseteado la cuenta para hoy. ¡A empezar de cero!"
        await context.bot.send_message(chat_id=chat_id, text=mensaje)
    logger.info(f"Reseteo diario completado para {len(chat_ids_a_resetear)} chats.")

# --- FUNCIÓN PRINCIPAL QUE EJECUTA EL BOT ---
def main():
    """Inicia y corre el bot."""
    if TOKEN == 'TU_TOKEN_AQUI' or not TOKEN:
        print("Error: Por favor, reemplaza 'TU_TOKEN_AQUI' en la línea 12 con tu token real.")
        return

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("resumen", resumen_command))
    application.add_handler(CommandHandler("resetear", resetear_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_mensaje))
    
    # job_queue = application.job_queue
    # hora_reseteo = datetime.time(hour=0, minute=0, second=0, tzinfo=TIMEZONE)
    # job_queue.run_daily(reseteo_diario, time=hora_reseteo, name="reseteo-diario")
    
    logger.info("Bot iniciado y escuchando...")
    application.run_polling()

if __name__ == '__main__':
    main()