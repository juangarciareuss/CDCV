import os
import json
import django
from django.core.exceptions import FieldDoesNotExist

# 1. Configurar Django para que funcione en este script
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings') # Asegúrate que 'config' sea el nombre de tu carpeta de settings
django.setup()

from django.apps import apps

def validar_integridad():
    archivo = 'datos_iniciales.json'
    errores = []
    
    print(f"🕵️‍♂️ Iniciando validación pre-vuelo para: {archivo}")

    # PASO 1: Validar Codificación y Sintaxis JSON
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("✅ PASO 1: El archivo es un JSON válido y legible (UTF-8).")
    except UnicodeDecodeError:
        print("❌ ERROR CRÍTICO: El archivo tiene mala codificación (Probablemente UTF-16 o BOM).")
        print("   Solución: Ejecuta el comando de dumpdata con --output")
        return
    except json.JSONDecodeError as e:
        print(f"❌ ERROR CRÍTICO: Sintaxis JSON inválida. Detalle: {e}")
        return

    # PASO 2: Validar que los campos del JSON existan en el Código (Modelos)
    print("⏳ PASO 2: Verificando consistencia con los Modelos de Django...")
    
    for indice, entry in enumerate(data):
        model_name = entry.get('model')
        fields = entry.get('fields', {})
        pk = entry.get('pk')

        try:
            # Obtenemos el modelo real desde tu código
            Model = apps.get_model(model_name)
        except LookupError:
            errores.append(f"Registro #{indice} (PK {pk}): El modelo '{model_name}' no existe en tu código.")
            continue

        # Revisamos campo por campo
        for field_name in fields.keys():
            try:
                # Intentamos obtener el campo del modelo
                Model._meta.get_field(field_name)
            except FieldDoesNotExist:
                # Si entramos aquí, es porque el JSON tiene un campo que borraste del código
                errores.append(f"❌ ERROR FATAL en {model_name} (ID: {pk}): El JSON intenta insertar el campo '{field_name}', pero ese campo YA NO EXISTE en tu modelo.")

    # REPORTE FINAL
    print("-" * 50)
    if errores:
        print(f"💥 SE ENCONTRARON {len(errores)} ERRORES BLOQUEANTES:")
        for error in errores:
            print(error)
        print("\n⛔ NO SUBAS A RENDER. Tu deploy fallará.")
    else:
        print("🚀 TODO PERFECTO. Tu archivo JSON está sincronizado con tu código.")
        print("✅ Puedes hacer git push con confianza.")

if __name__ == '__main__':
    validar_integridad()