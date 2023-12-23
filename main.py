import os
from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, Filters
import requests
from datetime import datetime, timedelta
import mysql.connector

# Estados para la conversación
FECHA, MONTO_EFECTIVO, MONTO_TRANSFERENCIA, MONTO_PUNTO = range(4)

# Estados para la conversación de gastos
FECHA_GASTO, DETALLE_GASTO, CONFIRMAR_GASTO = range(3, 6)

# Estado para el resumen
FECHA_RESUMEN = 6

# Token de tu bot
TOKEN = os.getenv('TOKEN')
if not TOKEN:
        raise ValueError("No se encontró el token del bot de Telegram. Asegúrate de configurarlo como una variable de entorno.")

DB_CONFIG = {
    'host': '170.239.85.238',
    'port': '3306',
    'user': 'lrequena',
    'password': '18594LCra..',
    'database': 'delivery'
}

def start(update, context):
    update.message.reply_text(
        "Bienvenido al bot de registro de ventas. Envía /venta para registrar una venta.")
    return ConversationHandler.END

def venta(update, context):
    if check_exit(update.message.text):
        return cancel(update, context)
    update.message.reply_text('Ingresa la fecha de la venta (DD/MM):')
    return FECHA

def check_exit(message):
    return message.lower() in ['exit', 'fin']

def fecha(update, context):
    if check_exit(update.message.text):
        return cancel(update, context)
    fecha_texto = update.message.text
    try:
        fecha_dt = datetime.strptime(fecha_texto + '/' + str(datetime.now().year), '%d/%m/%Y')
        context.user_data['fecha'] = fecha_dt.strftime('%Y-%m-%d')
        context.user_data['fecha_texto'] = fecha_texto
        update.message.reply_text('Ingresa el monto de la venta en efectivo:')
        return MONTO_EFECTIVO
    except ValueError:
        update.message.reply_text('Por favor, ingresa una fecha válida en formato DD/MM.')
        return FECHA

def monto_efectivo(update, context):
    if check_exit(update.message.text):
        return cancel(update, context)
    context.user_data['monto_efectivo'] = update.message.text
    update.message.reply_text('Ingresa el monto de la venta en transferencia:')
    return MONTO_TRANSFERENCIA

def monto_transferencia(update, context):
    if check_exit(update.message.text):
        return cancel(update, context)
    context.user_data['monto_transferencia'] = update.message.text
    update.message.reply_text('Ingresa el monto de la venta en punto:')
    return MONTO_PUNTO


def monto_punto(update, context):
    if check_exit(update.message.text):
        return cancel(update, context)

    context.user_data['monto_punto'] = update.message.text

    # Preparar el mensaje de resumen
    resumen = f"Fecha {context.user_data['fecha_texto']}\n"
    for tipo, monto in [('Efectivo', 'monto_efectivo'), ('Transferencia', 'monto_transferencia'), ('Punto', 'monto_punto')]:
        resumen += f"- {tipo}: {context.user_data[monto]}\n"

    # Registrar las ventas
    for tipo, monto in [('efectivo', 'monto_efectivo'), ('transferencia', 'monto_transferencia'), ('punto', 'monto_punto')]:
        if context.user_data[monto]:
            id_centro_costo = {'efectivo': 1, 'transferencia': 3, 'punto': 5}[tipo]
            payload = {
                "fecha": context.user_data['fecha'],
                "monto": context.user_data[monto],
                "id_centro_costo": id_centro_costo,
                "id_tipo_movimiento": 1,  # Venta
                "concepto": tipo.capitalize()
            }
            response = requests.post('http://rypsystems.space:5000/movimiento', json=payload)
            if response.status_code != 200:
                update.message.reply_text(f'Hubo un error al registrar la venta en {tipo}.')

    update.message.reply_text('Todas las ventas han sido registradas.\n' + resumen)
    return ConversationHandler.END

def gasto(update, context):
    if check_exit(update.message.text):
        return cancel(update, context)

    update.message.reply_text('Ingresa la fecha del gasto (DD/MM):')
    return FECHA_GASTO

def fecha_gasto(update, context):
    if check_exit(update.message.text):
        return cancel(update, context)

    fecha_texto = update.message.text
    try:
        fecha_dt = datetime.strptime(fecha_texto + '/' + str(datetime.now().year), '%d/%m/%Y')
        context.user_data['fecha_gasto'] = fecha_dt.strftime('%Y-%m-%d')
        update.message.reply_text('Ingresa el gasto con el formato "monto descripción":\nEjemplo: 5000 pago yngrid')
        return DETALLE_GASTO
    except ValueError:
        update.message.reply_text('Por favor, ingresa una fecha válida en formato DD/MM.')
        return FECHA_GASTO

def detalle_gasto(update, context):
    if check_exit(update.message.text):
        return cancel(update, context)

    gasto_texto = update.message.text
    try:
        monto, descripcion = gasto_texto.split(maxsplit=1)
        monto = float(monto)  # Convertir a número
        payload = {
            "fecha": context.user_data['fecha_gasto'],
            "monto": monto,
            "id_centro_costo": "9",
            "id_tipo_movimiento": "2",
            "concepto": descripcion,
            "tipo_egreso": 1
        }
        response = requests.post('http://rypsystems.space:5000/movimiento', json=payload)
        if response.status_code == 200:
            update.message.reply_text('Gasto registrado. ¿Deseas agregar otro gasto? Envía 1 para continuar o 2 para finalizar.')
            return CONFIRMAR_GASTO
        else:
            update.message.reply_text('Hubo un error al registrar el gasto.')
            return DETALLE_GASTO
    except ValueError:
        update.message.reply_text('Formato incorrecto. Usa "monto descripción".\nEjemplo: 5000 pago yngrid')
        return DETALLE_GASTO

def confirmar_gasto(update, context):
    if check_exit(update.message.text):
        return cancel(update, context)

    eleccion = update.message.text
    if eleccion == "1":
        update.message.reply_text('Ingresa el siguiente gasto con el formato "monto descripción":')
        return DETALLE_GASTO
    elif eleccion == "2":
        update.message.reply_text('Registro de gastos finalizado.')
        return ConversationHandler.END
    else:
        update.message.reply_text('Por favor, envía 1 para continuar o 2 para finalizar.')
        return CONFIRMAR_GASTO

def resumen(update, context):
    if check_exit(update.message.text):
        return cancel(update, context)

    update.message.reply_text('Ingresa la fecha del lunes de la semana que deseas resumir (DD/MM):')
    return FECHA_RESUMEN

def fecha_resumen(update, context):
    if check_exit(update.message.text):
        return cancel(update, context)

    fecha_texto = update.message.text
    try:
        fecha_inicio = datetime.strptime(fecha_texto + '/' + str(datetime.now().year), '%d/%m/%Y')
        fecha_fin = fecha_inicio + timedelta(days=6)  # Sumar 6 días para obtener el domingo

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        consulta = """
            SELECT id_tipo_movimiento, SUM(monto)
            FROM movimiento
            WHERE fecha BETWEEN %s AND %s
            GROUP BY id_tipo_movimiento;
        """
        cursor.execute(consulta, (fecha_inicio, fecha_fin))
        resultados = cursor.fetchall()

        ventas, gastos = 0, 0
        for tipo_mov, monto in resultados:
            if tipo_mov == 1:
                ventas += monto
            elif tipo_mov == 2:
                gastos += monto

        profit = ventas - gastos
        regalias = round(profit / 3)

        resumen_msg = f"Para la semana seleccionada el resumen es el siguiente\n- Ventas = {ventas}\n- Gastos = {gastos}\n- Profit = {profit}\n- Regalías = {regalias}"
        update.message.reply_text(resumen_msg)

        cursor.close()
        conn.close()

        return ConversationHandler.END
    except ValueError:
        update.message.reply_text('Por favor, ingresa una fecha válida en formato DD/MM.')
        return FECHA_RESUMEN


def cancel(update, context):
    update.message.reply_text('Operación cancelada.')
    return ConversationHandler.END


def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('venta', venta)],
        states={
            FECHA: [MessageHandler(Filters.text, fecha)],
            MONTO_EFECTIVO: [MessageHandler(Filters.text, monto_efectivo)],
            MONTO_TRANSFERENCIA: [MessageHandler(Filters.text, monto_transferencia)],
            MONTO_PUNTO: [MessageHandler(Filters.text, monto_punto)],
        },
        fallbacks=[CommandHandler('cancelar', cancel)]
    )

    dp.add_handler(conv_handler)
    
    conv_handler_gastos = ConversationHandler(
            entry_points=[CommandHandler('gasto', gasto)],
            states={
                FECHA_GASTO: [MessageHandler(Filters.text, fecha_gasto)],
                DETALLE_GASTO: [MessageHandler(Filters.text, detalle_gasto)],
                CONFIRMAR_GASTO: [MessageHandler(Filters.text, confirmar_gasto)],
            },
            fallbacks=[CommandHandler('cancelar', cancel)]
        )
    
    dp.add_handler(conv_handler_gastos)

    conv_handler_resumen = ConversationHandler(
        entry_points=[CommandHandler('resumen', resumen)],
        states={
            FECHA_RESUMEN: [MessageHandler(Filters.text, fecha_resumen)]
        },
        fallbacks=[CommandHandler('cancelar', cancel)]
    )

    dp.add_handler(conv_handler_resumen)


    dp.add_handler(CommandHandler('start', start))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()