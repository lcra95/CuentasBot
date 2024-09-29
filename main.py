import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import mysql.connector

# Estados de la conversación
RECIBIR_DATOS, RECIBIR_CODIGO = range(2)
RECIBIR_DATOS_OTRO, RECIBIR_CODIGO_OTRO = range(2, 4)

# Token de tu bot
TOKEN = os.getenv('TOKEN')
if not TOKEN:
    raise ValueError("No se encontró el token del bot de Telegram. Asegúrate de configurarlo como una variable de entorno.")

# Configuración de la base de datos
DB_CONFIG = {
    'host': '45.236.129.192',
    'port': '3306',
    'user': 'lrequena',
    'password': '18594LCra..',
    'database': 'remesas_control'
}

# Variables globales para almacenar el ID de las transacciones insertadas
ultimo_id_transaccion = None
ultimo_id_transaccion_otro = None

# Función para iniciar el comando /bdv
def bdv(update, context):
    update.message.reply_text("Por favor, envía los datos en el siguiente formato, cada dato en una línea:\n"
                              "1. Nombre del cliente\n"
                              "2. Número de cuenta\n"
                              "3. Cédula\n"
                              "4. Nombre de la persona\n"
                              "5. Monto")
    return RECIBIR_DATOS

def recibir_datos(update, context):
    global ultimo_id_transaccion
    # Recibir los datos del mensaje y separarlos por líneas
    datos = update.message.text.split('\n')

    # Verificar que haya exactamente 5 líneas de datos
    if len(datos) != 5:
        update.message.reply_text("Formato incorrecto. Asegúrate de enviar 5 líneas en el formato solicitado.")
        return RECIBIR_DATOS

    cliente = datos[0]
    cuenta = datos[1]
    cedula = datos[2]
    nombre_persona = datos[3]
    monto = str(datos[4] + '00')

    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Insertar la transacción en la tabla con estado "pendiente"
        query = """
        INSERT INTO transaccion (cliente, tipo_operacion, cedula, cuenta, nombre, monto, estado)
        VALUES (%s, %s, %s, %s, %s, %s, 'pendiente')
        """
        cursor.execute(query, (cliente, '0102', cedula, cuenta, nombre_persona, monto))
        conn.commit()

        # Obtener el ID de la última transacción insertada
        ultimo_id_transaccion = cursor.lastrowid

        # Confirmación de la transacción y solicitud del código de autorización
        update.message.reply_text("Transacción registrada correctamente con estado 'pendiente'.\n"
                                  "Por favor, ingresa el código de autorización.")
    except mysql.connector.Error as err:
        update.message.reply_text(f"Error al registrar la transacción: {err}")
    finally:
        cursor.close()
        conn.close()

    return RECIBIR_CODIGO

def recibir_codigo(update, context):
    global ultimo_id_transaccion
    codigo_autorizacion = update.message.text

    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Actualizar la transacción con el código de autorización
        query = """
        UPDATE transaccion
        SET codigo_autorizacion = %s, estado = 'autorizado'
        WHERE id = %s
        """
        cursor.execute(query, (codigo_autorizacion, ultimo_id_transaccion))
        conn.commit()

        # Confirmación de que el código fue agregado
        update.message.reply_text(f"Código de autorización '{codigo_autorizacion}' agregado a la transacción.")
    except mysql.connector.Error as err:
        update.message.reply_text(f"Error al actualizar la transacción: {err}")
    finally:
        cursor.close()
        conn.close()

    return ConversationHandler.END

# Función para iniciar el comando /otro
def otro(update, context):
    update.message.reply_text("Por favor, envía los datos en el siguiente formato, cada dato en una línea:\n"
                              "1. Nombre del cliente\n"
                              "2. Código del banco\n"
                              "3. Número de cuenta\n"
                              "4. Cédula\n"
                              "5. Nombre del receptor\n"
                              "6. Monto")
    return RECIBIR_DATOS_OTRO

def recibir_datos_otro(update, context):
    global ultimo_id_transaccion_otro
    # Recibir los datos del mensaje y separarlos por líneas
    datos = update.message.text.split('\n')

    # Verificar que haya exactamente 6 líneas de datos
    if len(datos) != 6:
        update.message.reply_text("Formato incorrecto. Asegúrate de enviar 6 líneas en el formato solicitado.")
        return RECIBIR_DATOS_OTRO

    cliente = datos[0]
    codigo_banco = datos[1]  # Usaremos esto como tipo_operacion
    cuenta = datos[2]
    cedula = datos[3]
    nombre_receptor = datos[4]
    monto = str(datos[5] + '00')

    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Insertar la transacción en la tabla con estado "pendiente"
        query = """
        INSERT INTO transaccion (cliente, tipo_operacion, cedula, cuenta, nombre, monto, estado)
        VALUES (%s, %s, %s, %s, %s, %s, 'pendiente')
        """
        cursor.execute(query, (cliente, codigo_banco, cedula, cuenta, nombre_receptor, monto))
        conn.commit()

        # Obtener el ID de la última transacción insertada
        ultimo_id_transaccion_otro = cursor.lastrowid

        # Confirmación de la transacción y solicitud del código de autorización
        update.message.reply_text("Transacción registrada correctamente con estado 'pendiente'.\n"
                                  "Por favor, ingresa el código de autorización.")
    except mysql.connector.Error as err:
        update.message.reply_text(f"Error al registrar la transacción: {err}")
    finally:
        cursor.close()
        conn.close()

    return RECIBIR_CODIGO_OTRO

def recibir_codigo_otro(update, context):
    global ultimo_id_transaccion_otro
    codigo_autorizacion = update.message.text

    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Actualizar la transacción con el código de autorización
        query = """
        UPDATE transaccion
        SET codigo_autorizacion = %s, estado = 'autorizado'
        WHERE id = %s
        """
        cursor.execute(query, (codigo_autorizacion, ultimo_id_transaccion_otro))
        conn.commit()

        # Confirmación de que el código fue agregado
        update.message.reply_text(f"Código de autorización '{codigo_autorizacion}' agregado a la transacción.")
    except mysql.connector.Error as err:
        update.message.reply_text(f"Error al actualizar la transacción: {err}")
    finally:
        cursor.close()
        conn.close()

    return ConversationHandler.END

def cancel(update, context):
    update.message.reply_text("Operación cancelada.")
    return ConversationHandler.END

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Manejo de la conversación para el comando /bdv
    conv_handler_bdv = ConversationHandler(
        entry_points=[CommandHandler('bdv', bdv)],
        states={
            RECIBIR_DATOS: [MessageHandler(Filters.text, recibir_datos)],
            RECIBIR_CODIGO: [MessageHandler(Filters.text, recibir_codigo)],
        },
        fallbacks=[CommandHandler('cancelar', cancel)]
    )

    dp.add_handler(conv_handler_bdv)

    # Manejo de la conversación para el comando /otro
    conv_handler_otro = ConversationHandler(
        entry_points=[CommandHandler('otro', otro)],
        states={
            RECIBIR_DATOS_OTRO: [MessageHandler(Filters.text, recibir_datos_otro)],
            RECIBIR_CODIGO_OTRO: [MessageHandler(Filters.text, recibir_codigo_otro)],
        },
        fallbacks=[CommandHandler('cancelar', cancel)]
    )

    dp.add_handler(conv_handler_otro)

    # Comando /start
    dp.add_handler(CommandHandler('start', lambda update, context: update.message.reply_text("Bienvenido! Usa /bdv o /otro para registrar una transacción.")))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
