import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from telegram import InputFile
import mysql.connector

# Estados de la conversación
RECIBIR_DATOS, RECIBIR_CODIGO = range(2)
RECIBIR_DATOS_OTRO, RECIBIR_CODIGO_OTRO = range(2, 4)
RECIBIR_DATOS_PM, RECIBIR_CODIGO_PM = range(4, 6)
RECIBIR_ID_TRANSACCION = range(6, 7)  # Nuevo estado para recibir ID de transacción

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
ultimo_id_transaccion_pm = None

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

        # Insertar la transacción en la tabla con estado "pendiente" y tipo_transaccion 'T'
        query = """
        INSERT INTO transaccion (cliente, tipo_operacion, cedula, cuenta, nombre, monto, estado, tipo_transaccion)
        VALUES (%s, %s, %s, %s, %s, %s, 'pendiente', 'T')
        """
        cursor.execute(query, (cliente, '0102', cedula, cuenta, nombre_persona, monto))
        conn.commit()

        # Obtener el ID de la última transacción insertada
        ultimo_id_transaccion = cursor.lastrowid

        # Confirmación de la transacción y solicitud del código de autorización
        update.message.reply_text(f"Transacción {ultimo_id_transaccion} registrada correctamente con estado 'pendiente'.\n"
                                  "Por favor, ingresa el código de autorización o escribe 'exit', 'cancelar', o 'terminar' para cancelar la transacción.")
    except mysql.connector.Error as err:
        update.message.reply_text(f"Error al registrar la transacción: {err}")
    finally:
        cursor.close()
        conn.close()

    return RECIBIR_CODIGO

def recibir_codigo(update, context):
    global ultimo_id_transaccion
    codigo_autorizacion = update.message.text.lower()

    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        if codigo_autorizacion in ['exit', 'cancelar', 'terminar']:
            # Actualizar la transacción a estado 'cancelada'
            query = """
            UPDATE transaccion
            SET estado = 'cancelada'
            WHERE id = %s
            """
            cursor.execute(query, (ultimo_id_transaccion,))
            update.message.reply_text("La transacción ha sido cancelada.")
        else:
            # Actualizar la transacción con el código de autorización y cambiar a 'autorizado'
            query = """
            UPDATE transaccion
            SET codigo_autorizacion = %s, estado = 'autorizado'
            WHERE id = %s
            """
            cursor.execute(query, (codigo_autorizacion, ultimo_id_transaccion))
            update.message.reply_text(f"Código de autorización '{codigo_autorizacion}' agregado a la transacción.")

        conn.commit()

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

        # Insertar la transacción en la tabla con estado "pendiente" y tipo_transaccion 'T'
        query = """
        INSERT INTO transaccion (cliente, tipo_operacion, cedula, cuenta, nombre, monto, estado, tipo_transaccion)
        VALUES (%s, %s, %s, %s, %s, %s, 'pendiente', 'T')
        """
        cursor.execute(query, (cliente, codigo_banco, cedula, cuenta, nombre_receptor, monto))
        conn.commit()

        # Obtener el ID de la última transacción insertada
        ultimo_id_transaccion_otro = cursor.lastrowid

        # Confirmación de la transacción y solicitud del código de autorización
        update.message.reply_text(f"Transacción {ultimo_id_transaccion_otro} registrada correctamente con estado 'pendiente'.\n"
                                  "Por favor, ingresa el código de autorización o escribe 'exit', 'cancelar', o 'terminar' para cancelar la transacción.")
    except mysql.connector.Error as err:
        update.message.reply_text(f"Error al registrar la transacción: {err}")
    finally:
        cursor.close()
        conn.close()

    return RECIBIR_CODIGO_OTRO

def recibir_codigo_otro(update, context):
    global ultimo_id_transaccion_otro
    codigo_autorizacion = update.message.text.lower()

    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        if codigo_autorizacion in ['exit', 'cancelar', 'terminar']:
            # Actualizar la transacción a estado 'cancelada'
            query = """
            UPDATE transaccion
            SET estado = 'cancelada'
            WHERE id = %s
            """
            cursor.execute(query, (ultimo_id_transaccion_otro,))
            update.message.reply_text("La transacción ha sido cancelada.")
        else:
            # Actualizar la transacción con el código de autorización y cambiar a 'autorizado'
            query = """
            UPDATE transaccion
            SET codigo_autorizacion = %s, estado = 'autorizado'
            WHERE id = %s
            """
            cursor.execute(query, (codigo_autorizacion, ultimo_id_transaccion_otro))
            update.message.reply_text(f"Código de autorización '{codigo_autorizacion}' agregado a la transacción.")

        conn.commit()

    except mysql.connector.Error as err:
        update.message.reply_text(f"Error al actualizar la transacción: {err}")
    finally:
        cursor.close()
        conn.close()

    return ConversationHandler.END

# Función para iniciar el comando /pm (con tipo_transaccion 'P')
def pm(update, context):
    update.message.reply_text("Por favor, envía los datos en el siguiente formato, cada dato en una línea:\n"
                              "1. Nombre del cliente\n"
                              "2. Código del banco\n"
                              "3. Número de cuenta\n"
                              "4. Cédula\n"
                              "5. Nombre del receptor\n"
                              "6. Monto")
    return RECIBIR_DATOS_PM

def recibir_datos_pm(update, context):
    global ultimo_id_transaccion_pm
    # Recibir los datos del mensaje y separarlos por líneas
    datos = update.message.text.split('\n')

    # Verificar que haya exactamente 6 líneas de datos
    if len(datos) != 6:
        update.message.reply_text("Formato incorrecto. Asegúrate de enviar 6 líneas en el formato solicitado.")
        return RECIBIR_DATOS_PM

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

        # Insertar la transacción en la tabla con estado "pendiente" y tipo_transaccion 'P'
        query = """
        INSERT INTO transaccion (cliente, tipo_operacion, cedula, cuenta, nombre, monto, estado, tipo_transaccion)
        VALUES (%s, %s, %s, %s, %s, %s, 'pendiente', 'P')
        """
        cursor.execute(query, (cliente, codigo_banco, cedula, cuenta, nombre_receptor, monto))
        conn.commit()

        # Obtener el ID de la última transacción insertada
        ultimo_id_transaccion_pm = cursor.lastrowid

        # Confirmación de la transacción y solicitud del código de autorización
        update.message.reply_text(f"Transacción {ultimo_id_transaccion_pm} registrada correctamente con estado 'pendiente'.\n"
                                  "Por favor, ingresa el código de autorización o escribe 'exit', 'cancelar', o 'terminar' para cancelar la transacción.")
    except mysql.connector.Error as err:
        update.message.reply_text(f"Error al registrar la transacción: {err}")
    finally:
        cursor.close()
        conn.close()

    return RECIBIR_CODIGO_PM

def recibir_codigo_pm(update, context):
    global ultimo_id_transaccion_pm
    codigo_autorizacion = update.message.text.lower()

    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        if codigo_autorizacion in ['exit', 'cancelar', 'terminar']:
            # Actualizar la transacción a estado 'cancelada'
            query = """
            UPDATE transaccion
            SET estado = 'cancelada'
            WHERE id = %s
            """
            cursor.execute(query, (ultimo_id_transaccion_pm,))
            update.message.reply_text("La transacción ha sido cancelada.")
        else:
            # Actualizar la transacción con el código de autorización y cambiar a 'autorizado'
            query = """
            UPDATE transaccion
            SET codigo_autorizacion = %s, estado = 'autorizado'
            WHERE id = %s
            """
            cursor.execute(query, (codigo_autorizacion, ultimo_id_transaccion_pm))
            update.message.reply_text(f"Código de autorización '{codigo_autorizacion}' agregado a la transacción.")

        conn.commit()

    except mysql.connector.Error as err:
        update.message.reply_text(f"Error al actualizar la transacción: {err}")
    finally:
        cursor.close()
        conn.close()

    return ConversationHandler.END

# Función para capturar una imagen
def capture(update, context):
    update.message.reply_text("Por favor, ingresa el ID de la transacción para capturar la imagen:")
    return RECIBIR_ID_TRANSACCION

def recibir_id_transaccion(update, context):
    transaction_id = update.message.text.strip()

    if not transaction_id.isdigit():
        update.message.reply_text("Por favor, ingresa un ID de transacción válido.")
        return RECIBIR_ID_TRANSACCION

    image = get_image_from_db(transaction_id)

    if image:
        image_filename = f"{transaction_id}.png"
        with open(image_filename, 'wb') as file:
            file.write(image)

        with open(image_filename, 'rb') as img:
            update.message.reply_photo(photo=InputFile(img))

        os.remove(image_filename)
    else:
        update.message.reply_text("No hay imagen para este ID de transacción.")

    return ConversationHandler.END

def get_image_from_db(transaction_id):
    """
    Recupera la imagen de la transacción desde la base de datos.
    """
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        query = "SELECT imagen FROM transaccion WHERE id = %s"
        cursor.execute(query, (transaction_id,))
        result = cursor.fetchone()

        if result and result[0]:
            return result[0]  # Retornar la imagen en formato binario
        else:
            return None  # No hay imagen para este ID
    except mysql.connector.Error as err:
        print(f"Error al recuperar la imagen: {err}")
        return None
    finally:
        cursor.close()
        conn.close()

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

    # Manejo de la conversación para el comando /otro
    conv_handler_otro = ConversationHandler(
        entry_points=[CommandHandler('otro', otro)],
        states={
            RECIBIR_DATOS_OTRO: [MessageHandler(Filters.text, recibir_datos_otro)],
            RECIBIR_CODIGO_OTRO: [MessageHandler(Filters.text, recibir_codigo_otro)],
        },
        fallbacks=[CommandHandler('cancelar', cancel)]
    )

    # Manejo de la conversación para el comando /pm
    conv_handler_pm = ConversationHandler(
        entry_points=[CommandHandler('pm', pm)],
        states={
            RECIBIR_DATOS_PM: [MessageHandler(Filters.text, recibir_datos_pm)],
            RECIBIR_CODIGO_PM: [MessageHandler(Filters.text, recibir_codigo_pm)],
        },
        fallbacks=[CommandHandler('cancelar', cancel)]
    )

    # Manejo de la conversación para el comando /capture
    conv_handler_capture = ConversationHandler(
        entry_points=[CommandHandler('capture', capture)],
        states={
            RECIBIR_ID_TRANSACCION: [MessageHandler(Filters.text, recibir_id_transaccion)],
        },
        fallbacks=[CommandHandler('cancelar', cancel)]
    )

    dp.add_handler(conv_handler_bdv)
    dp.add_handler(conv_handler_otro)
    dp.add_handler(conv_handler_pm)
    dp.add_handler(conv_handler_capture)

    # Comando /start
    dp.add_handler(CommandHandler('start', lambda update, context: update.message.reply_text(
        "Bienvenido! Usa /bdv, /otro, /pm o /capture para interactuar con las transacciones.")))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
