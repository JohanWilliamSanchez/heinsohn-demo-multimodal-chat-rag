# heinsohn-demo-multimodal-chat-rag

## instalacion de ambiente

### Paso 1: Crear un entorno virtual
Navega al directorio de tu proyecto (el directorio donde tienes tu requirements.txt).

Ejecuta el siguiente comando para crear un entorno virtual en una carpeta llamada venv:

bash
Copiar código
python -m venv venv
Este comando crea un entorno virtual en una subcarpeta llamada venv dentro de tu directorio de proyecto. Puedes elegir otro nombre si prefieres.

### Paso 2: Activar el entorno virtual
En Windows:

bash
Copiar código
venv\Scripts\activate
En macOS y Linux:

bash
Copiar código
source venv/bin/activate
Después de activar el entorno virtual, deberías ver el nombre del entorno virtual (por ejemplo, (venv)) en tu terminal, indicando que el entorno está activo.

### Paso 3: Instalar las dependencias desde requirements.txt
Una vez que el entorno virtual esté activo, instala las dependencias usando pip:

bash
Copiar código
pip install -r requirements.txt
Esto instalará todas las dependencias listadas en el archivo requirements.txt en tu entorno virtual.

### Paso 4: Verificar las dependencias instaladas
Para confirmar que las dependencias se han instalado correctamente, puedes ejecutar:

bash
Copiar código
pip list
Paso 5: Desactivar el entorno virtual cuando hayas terminado
Para salir del entorno virtual, usa el comando:

bash
Copiar código
deactivate
Resumen de comandos
Crear el entorno virtual: python -m venv venv
Activar el entorno virtual:
Windows: venv\Scripts\activate
macOS/Linux: source venv/bin/activate
Instalar dependencias: pip install -r requirements.txt
Desactivar el entorno virtual: deactivate
Esta es una forma organizada de gestionar dependencias en Python y evitar conflictos con otras librerías en tu sistema.