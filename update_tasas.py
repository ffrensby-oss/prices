import os
import json
import base64
import random
import requests




def handler(request):
    GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN")
    GITHUB_REPO   = os.environ.get("GITHUB_REPO")
    TASAS_API_KEY = os.environ.get("TASAS_API_KEY")

    # Validar que las variables estén configuradas
    if not GITHUB_TOKEN or not GITHUB_REPO or not TASAS_API_KEY:
        return {
            "statusCode": 500,
            "body": "Error: faltan variables de entorno (GITHUB_TOKEN, GITHUB_REPO, TASAS_API_KEY)"
        }

    endpoint_tasas = "https://tasas.eltoque.com/v1/trmi"
    headers_tasas = {
        "Authorization": f"Bearer {TASAS_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # 1. Obtener las tasas de El Toque
        res = requests.get(endpoint_tasas, headers=headers_tasas, timeout=10)
        res.raise_for_status()
        tasas = res.json().get("tasas", {})

        # 2. Estructurar el nuevo contenido del JSON
        nuevo_contenido = {
            "id": random.randint(1, 100),
            "USD": tasas.get("USD", 0),
            "ECU": tasas.get("ECU", 0)
        }
        json_string = json.dumps(nuevo_contenido, indent=4)

        # 3. Buscar si el archivo ya existe en GitHub para obtener su 'sha'
        url_github = f"https://api.github.com/repos/{GITHUB_REPO}/contents/response.json"
        headers_github = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

        get_file = requests.get(url_github, headers=headers_github, timeout=10)
        sha = ""
        if get_file.status_code == 200:
            sha = get_file.json().get("sha", "")

        # 4. Codificar el contenido a Base64 (requisito de la API de GitHub)
        contenido_base64 = base64.b64encode(json_string.encode("utf-8")).decode("utf-8")

        # 5. Hacer el commit automático en GitHub
        payload = {
            "message": "🤖 actualización automática de tasas (Cron 7h)",
            "content": contenido_base64,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha  # Necesario para actualizar un archivo existente

        put_file = requests.put(url_github, headers=headers_github, json=payload, timeout=10)
        put_file.raise_for_status()

        return {
            "statusCode": 200,
            "body": json.dumps({
                "mensaje": "response.json actualizado en GitHub correctamente.",
                "datos": nuevo_contenido
            })
        }

    except requests.exceptions.HTTPError as e:
        return {
            "statusCode": e.response.status_code if e.response else 500,
            "body": f"Error HTTP: {str(e)}"
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Error inesperado: {str(e)}"
        }
