from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename
from flask_cors import CORS 

from azureOpenaiClient import send_message, client_open_ai, send_message_file, analyze_intent, extract_invoice_data, clear_history, process_intent
from documentIntelligent import myDocumentIntelligent

 
app = Flask(__name__)
CORS(app) 
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
 
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
 
client = client_open_ai()
 
conversation_history = {}
 
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        message = request.form.get('message')
        user_id = request.form.get('user_id', 'default_user')
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        image_path = './uploads/' + filename
        data_text = myDocumentIntelligent(image_path)
        

        init_chat(user_id) #inicializar el chat con user id, la primera vez que se crea el chat

        conversation_history[user_id].append({"role": "user", "content": 'Te envio la informacion de la factura: '+ data_text})
        conversation_history[user_id + '_data_text']=data_text


        process_intent(message, client, user_id, conversation_history)

        response = send_message_file(client, conversation_history[user_id])
            

        conversation_history[user_id].append({"role": "assistant", "content": response})

        print('response: ' + response)

        return jsonify({'message': response, 'response': filename}), 200

    return jsonify({'error': 'File type not allowed'}), 400


@app.route('/message', methods=['POST'])
def post_message():
    data = request.json
    message = data['message']
    user_id = data.get('user_id', 'default_user')

    
    init_chat(user_id) #inicializar el chat con user id, la primera vez que se crea el chat

        # Aquí no necesitas agregar el `data_text`, solo procesar el mensaje del usuario
    process_intent(message, client, user_id, conversation_history)

        # Limpiar el historial para mantenerlo en un máximo de 10 mensajes
        # clear_history(user_id, conversation_history)

    
    response = send_message(client, conversation_history[user_id])

    
    conversation_history[user_id].append({"role": "assistant", "content": response})

    print('arreglo ', conversation_history[user_id])

    return jsonify({'message': response}), 200

def init_chat(user_id):
    if user_id not in conversation_history:
        user_id_data_text = user_id + '_data_text'
        conversation_history[user_id] = []
        conversation_history[user_id_data_text] = ''

    if len(conversation_history[user_id]) == 0:
        conversation_history[user_id].append({
            "role": "system",
            "content": "Eres un asistente que ayuda con la interpretación y extraccion de datos de factura, el cual te estoy enviando en un formato de texto. Responde todas las preguntas que se realicen sobre esta información. Los datos superiores son de la empresa y los inferiores son del cliente."
        })

if __name__ == '__main__':
    app.run(debug=True)
