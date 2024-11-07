from openai import AzureOpenAI
import os
import json
from decouple import config
import re

def extract_complaint_data(data_text):
    # Expresiones comunes para identificar quejas
    complaint_keywords = ["no funciona", "problema", "fallo", "defecto", "insatisfecho", "error", "no estoy contento", "mala experiencia"]

    # Búsqueda de palabras clave relacionadas con quejas
    detected_issues = [keyword for keyword in complaint_keywords if keyword in data_text.lower()]

    # Extracción del producto o servicio mencionado (si aplica)
    # Asume que los productos están precedidos por palabras como "con" o "de"
    product_match = re.search(r"(con|de)\s+(\w+)", data_text)
    product = product_match.group(2) if product_match else "Producto/servicio no especificado"

    # Construcción del resultado
    complaint_data = {
        "detected_issues": detected_issues if detected_issues else ["No se identificaron problemas claros"],
        "product_or_service": product
    }

    return complaint_data

def extract_specific_info(data_text):
    # Buscamos fechas, números, productos o servicios específicos
    date_match = re.findall(r"\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}", data_text)
    number_match = re.findall(r"\d+", data_text)

    # Intentamos extraer productos o servicios basados en un patrón similar al usado en quejas
    product_match = re.search(r"(información sobre|detalles de|quiero saber más sobre|datos de)\s+(\w+)", data_text)
    product_or_service = product_match.group(2) if product_match else "Producto/servicio no especificado"

    # Construimos el resultado
    specific_info_data = {
        "dates": date_match if date_match else ["No se encontraron fechas"],
        "numbers": number_match if number_match else ["No se encontraron números"],
        "product_or_service": product_or_service
    }

    return specific_info_data

def client_open_ai():


    endpoint = config('ENDPOINT_URL')

    subscription_key = config('AZURE_OPENAI_API_KEY')

    client = AzureOpenAI(
    azure_endpoint = endpoint,
    api_key = subscription_key,
    api_version = "2024-05-01-preview",
)
    return client

def send_message_file(client, messages):
    # Enviar la solicitud al modelo utilizando el historial completo de mensajes
    completion = client.chat.completions.create(
        model="multimodalchatopenia",
        messages=messages,
        max_tokens=2000,
        temperature=0.9
    )
    return completion.choices[0].message.content

def send_message(client, messages):
    # Enviar la solicitud al modelo utilizando el historial completo de mensajes
    deployment = config('DEPLOYMENT_NAME')
    search_endpoint = config('SEARCH_ENDPOINT')
    search_key = config('SEARCH_KEY')
    completion = client.chat.completions.create(
        model=deployment,
        messages=messages,
        max_tokens=2000,
        temperature=0,
        extra_body={
      "data_sources": [{
          "type": "azure_search",
          "parameters": {
            "endpoint": f"{search_endpoint}",
            "index_name": "indicebusquedafragmentado",
            "semantic_configuration": "default",
            "query_type": "vector_semantic_hybrid",
            "fields_mapping": {},
            "in_scope": True,
            "role_information": "You are an AI assistant that helps people find information.",
            "filter": None,
            "strictness": 3,
            "top_n_documents": 5,
            "authentication": {
              "type": "api_key",
              "key": f"{search_key}"
            },
            "embedding_dependency": {
              "type": "deployment_name",
              "deployment_name": "multimodalembedingv2segunvideo"
            }
          }
        }]
    }
    )
    return completion.choices[0].message.content


def obtener_palabra_clave(client, user_message):
    # Prompts para generar la palabra clave desde el mensaje del usuario
    messages = [

        # {"role": "user", "content": f"Extrae una palabra clave relacionada con el siguiente mensaje del usuario: {user_message} solo devuelve las palabras claves sin ningun texto adicional"}
        {"role": "user", "content": f"""Extrae una palabra clave relacionada con el siguiente mensaje del usuario: {user_message} Devuelve el resultado en el siguiente formato, sin añadir texto adicional:
        entidad: [palabra clave principal] acción: [verbo o frase corta que indique la intención] keywords: [lista de 3-5 palabras clave separadas por comas]"""}
    ]

    # Obtener la respuesta de GPT
    keyword = send_message(client, messages)

    # Tomar solo la palabra clave sin explicaciones adicionales
    keyword = keyword.strip()

    return keyword

# analizar intencion
def analyze_intent(message, client):
    prompt = f"""
    Analiza cuidadosamente el siguiente mensaje y clasifica la intención principal del usuario. Es CRUCIAL que elijas una de las siguientes categorías y respondas ÚNICAMENTE con el número correspondiente.

    Categorías de intención:
    1. Consulta general: Preguntas o solicitudes de información general.
    2. Queja: Expresiones de insatisfacción o problemas con un servicio/producto.
    3. Envio de informacion para queja: Son los datos de la factura, como el numero, el nombre de la persona el monto y la descripcion del problema

    Instrucciones importantes:
    - Lee el mensaje completo antes de decidir.
    - Elige la categoría que mejor represente la intención principal.
    - Si hay duda entre varias categorías, elige la más específica.
    - DEBES responder SOLO con el número de la categoría elegida, sin texto adicional.
    - Si no estás seguro, elige la categoría 5 (Otro), pero SIEMPRE debes clasificar el mensaje.

    Mensaje del usuario: "{message}"

    Clasificación (responde solo con el número):
    """


    result = send_message(client, [{"role": "user", "content": prompt}])

    return int(result[0])
# Extraer datos de factura
def extract_invoice_data(message,client):
    prompt = f"""
    Por favor, extrae la siguiente información clave de la factura proporcionada. Es importante que respondas en un formato JSON estructurado:

    - Número de factura: El identificador único de la factura.
    - Fecha de emisión: La fecha en que se emitió la factura.
    - Monto total: El importe total a pagar, incluyendo impuestos y otros cargos.
    - Nombre del cliente: El nombre completo o razón social del cliente al que se le ha emitido la factura.
    - Concepto: Descripción del/los producto(s) o servicio(s) facturado(s).
    - Fecha de vencimiento: La fecha límite de pago, si está disponible.
    - Detalle de impuestos: Información sobre los impuestos aplicados, como IVA, GST, etc., si corresponde.
    - Moneda: La divisa en la que se emitió la factura.
    - Número de orden de compra (si aplica): El número de la orden de compra asociada, si está disponible.

    Mensaje: "{message}"

    Responde con un JSON que contenga todas estas claves, y si algún dato no está presente en la factura, indícalo explícitamente como "No disponible".
"""


    respuesta = send_message(client, [{"role": "user", "content": prompt}])
    return json.loads(respuesta)

def clear_history(user_id, conversation_history):
    """
    Mantiene los mensajes importantes en el historial, incluidos `data_text` y el último `contexto`,
    y elimina los más antiguos cuando el historial supera los 10 mensajes.
    Reemplaza el mensaje de `data_text` y el contexto anterior con el más reciente.
    """
    important_history = []
    latest_data_text = None
    latest_context = None

    # Identificar mensajes importantes (del sistema, `data_text` y contexto)
    for msg in conversation_history[user_id]:
        if msg['role'] == 'system':
            important_history.append(msg)
        elif 'data_text' in msg['content']:
            latest_data_text = msg  # Guardar el último mensaje con `data_text`
        elif 'Contexto' in msg['content']:
            latest_context = msg  # Guardar el último mensaje con `Contexto`

    # Si hay un nuevo `data_text`, reemplazar el antiguo
    if latest_data_text:
        important_history = [msg for msg in important_history if 'data_text' not in msg['content']]
        important_history.append(latest_data_text)

    # Si hay un nuevo contexto, reemplazar el anterior
    if latest_context:
        important_history = [msg for msg in important_history if 'Contexto' not in msg['content']]
        important_history.append(latest_context)

    # Si el historial total excede de 10, eliminar los más antiguos, preservando los importantes
    if len(conversation_history[user_id]) > 10:
        # Calcular cuántos mensajes eliminar manteniendo los importantes
        excess_messages = len(conversation_history[user_id]) - 10
        # Filtrar y mantener solo los últimos mensajes no importantes después del recorte
        remaining_messages = [msg for msg in conversation_history[user_id] if msg not in important_history]
        conversation_history[user_id] = important_history + remaining_messages[-(10 - len(important_history)):]

def step_intention(intention):

    if(int(intention)==1):
        return 'Dame los pasos para consulta general'
    if(int(intention)==2):
        return 'Dame los pasos para queja'
    if(int(intention)==3):
        return 'Dame los pasos de problemas con factura'
    if(int(intention)==4):
        return 'Dame los pasos para solicitar informacion especifica'
    if(int(intention)==5):
        return 'Dame los pasos para una sugerencia de mejora'

def process_intent(message, client, user_id, conversation_history):
    user_id_data_text = user_id + '_data_text'
    # Buscar `data_text` en los mensajes de contexto
    data_text = ''
    # word_key = obtener_palabra_clave(client,message)
    # print('word ', message)
    for msg in conversation_history[user_id]:
        if msg['role'] == 'context':
            data_text = msg['content']
            break

    if not conversation_history[user_id_data_text]:
        data_text = 'El cliente no ha mandado factura. Solicite que le envie la imagen de la factura'
    else:
        # data_text = 'Teniendo encuenta la factura enviada anteriormente responder los datos que se estan solicitando'
        data_text = 'quien es juan pablo segundo'

    # Análisis de intención
    intention = analyze_intent(message, client)
    print(intention)
    # query_intention = ''
    # chunk = ''
    # # if intention != 6:
    #     # query_intention = step_intention(intention)
    # chunk = search_index_document(message)





    # consult_complete = f"""
    # Consulta del usuario: {message}
    # Instrucciones:
    # 1. A continuación se proporciona información relevante bajo la sección "Chunks".
    # 2. Utiliza esta información para elaborar una respuesta concisa y precisa a la consulta del usuario.
    # 3. La respuesta debe ser informativa pero breve, limitada a 2-3 oraciones.
    # 4. No menciones la existencia de los "Chunks" en tu respuesta.

    # Chunks: {chunk}

    # Por favor, responde a la consulta del usuario basándote en estas instrucciones.

    # """
    if intention == 1:  # Consulta general
        print(message)

        conversation_history[user_id].append({
            "role": "user",
            "content": 'El usuario ha realizado una consulta general con el siguiente mensaje: \n'+message
        })

    elif intention == 2:  # Queja
        print("El usuario tiene una queja. \n" + message )
        conversation_history[user_id].append({
            "role": "user",
            "content": "El usuario tiene una queja con el siguiente mensaje: \n" + message +".\n teniendo presente los pasos, solicita la informacion necesaria para contnuar con el tema si no te ha mandado informacion el usuario de la queja"
        })

    elif intention == 3:  # Enviar los datos
        specific_consult_complete = "El usuario esta mandando la siguiente informacion con la queja \n" + message +".\n indica que acabas de mandar un correo con esa infomraicon al gerente, espere en los proximos tres dias habiles y tendra una respuesta"

        conversation_history[user_id].append({
            "role": "user",
            "content": specific_consult_complete
        })

    # elif intention == 4:  # Solicitud de información específica

    #     specific_consult_complete = "El usuario ha solicitado información específica con el siguiente mensaje \n" + message
    #     print(specific_consult_complete)
    #     conversation_history[user_id].append({
    #         "role": "user",
    #         "content": specific_consult_complete
    #     })

    # elif intention == 5:  # Mejora

    #     specific_consult_complete = "El usuario desea solicitar una mejora. \n" + message
    #     print(specific_consult_complete)
    #     conversation_history[user_id].append({
    #         "role": "user",
    #         "content": specific_consult_complete
    #     })
    # elif intention == 6:  # Otros
    #     specific_consult_complete = "El usuario esta realizando una consulta tener presente:  \n" + message
    #     print(specific_consult_complete)

    #     conversation_history[user_id].append({
    #         "role": "user",
    #         "content": specific_consult_complete
    #     })
