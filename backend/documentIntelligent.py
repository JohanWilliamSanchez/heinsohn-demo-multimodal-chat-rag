import os
from openai import AzureOpenAI
from langchain_community.document_loaders import  AzureAIDocumentIntelligenceLoader
from decouple import config

def myDocumentIntelligent(image_path):
    loader = AzureAIDocumentIntelligenceLoader(
        file_path=image_path,
        api_key= config('DOCUMENT_API_KEY'),
        api_endpoint= config('DOCUMENT_API_ENDPOINT'),
        api_model="prebuilt-layout",
        api_version="2024-02-29-preview",
        mode="markdown"
    )
     # Cargar el contenido del documento
    document_content = loader.load()

    # Si el contenido viene en formato de markdown, simplemente lo retornamos
    if isinstance(document_content, str):
        return document_content  # Asumimos que es markdown y lo devolvemos como texto

    # Si `document_content` es un objeto complejo, lo transformamos a texto
    # Aquí podrías añadir lógica para extraer contenido dependiendo de su estructura
    return str(document_content)  # Convertir a texto cualquier otro formato no esperado