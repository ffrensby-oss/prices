from http.server import BaseHTTPRequestHandler
import os
import json
import base64
import random
import requests
# Viva cuba libre


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN")
        GITHUB_REPO   = os.environ.get("GITHUB_REPO")   # formato: "usuario/repo"
        TASAS_API_KEY = os.environ.get("TASAS_API_KEY")

        if not GITHUB_TOKEN or not GITHUB_REPO or not TASAS_API_KEY:
            self._respond(500, {"error": "Faltan variables de entorno (GITHUB_TOKEN, GITHUB_REPO, TASAS_API_KEY)"})
            return

        try:
            # 1. Obtener las tasas de El Toque
            res = requests.get(
                "https://tasas.eltoque.com/v1/trmi",
                headers={
                    "Authorization": f"Bearer {TASAS_API_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            res.raise_for_status()
            tasas = res.json().get("tasas", {})

            # 2. Estructurar el nuevo contenido
            nuevo_contenido = {
                "id": random.randint(1, 100),
                "USD": tasas.get("USD", 0),
                "ECU": tasas.get("ECU", 0)
            }
            json_string = json.dumps(nuevo_contenido, indent=4)

            # 3. Buscar sha del archivo existente en GitHub
            url_github = f"https://api.github.com/repos/{GITHUB_REPO}/contents/response.json"
            headers_github = {
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json"
            }

            get_file = requests.get(url_github, headers=headers_github, timeout=10)
            sha = get_file.json().get("sha", "") if get_file.status_code == 200 else ""

            # 4. Codificar a Base64 y hacer commit
            payload = {
                "message": "🤖 actualización automática de tasas (Cron 7h)",
                "content": base64.b64encode(json_string.encode("utf-8")).decode("utf-8"),
                "branch": "main"
            }
            if sha:
                payload["sha"] = sha

            put_file = requests.put(url_github, headers=headers_github, json=payload, timeout=10)
            put_file.raise_for_status()

            self._respond(200, {
                "mensaje": "response.json actualizado en GitHub correctamente.",
                "datos": nuevo_contenido
            })

        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response else 500
            self._respond(code, {"error": f"Error HTTP: {str(e)}"})
        except Exception as e:
            self._respond(500, {"error": f"Error inesperado: {str(e)}"})

    def _respond(self, status_code, body_dict):
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body_dict).encode("utf-8"))
