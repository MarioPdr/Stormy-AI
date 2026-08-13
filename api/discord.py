import os
import json
from http.server import BaseHTTPRequestHandler

from openai import OpenAI


# ==========================================
# CONFIGURAÇÕES
# ==========================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)


# ==========================================
# PERSONALIDADE
# ==========================================

SYSTEM_PROMPT = """
Seu nome é Stormy.

Você é um assistente de Discord inteligente,
prestativo, amigável e bem-humorado.

Você fala português do Brasil.

Responda de maneira natural, clara e direta.

Não invente informações.

Quando receber informações provenientes
de pesquisa na internet, utilize essas
informações para responder.
"""


# ==========================================
# DETECTAR NECESSIDADE DE PESQUISA
# ==========================================

def precisa_pesquisa(pergunta):

    pergunta = pergunta.lower()

    palavras = [
        "hoje",
        "agora",
        "atualmente",
        "atual",
        "recente",
        "último",
        "última",
        "últimos",
        "últimas",
        "notícia",
        "notícias",
        "update",
        "patch",
        "atualização",
        "atualizações",
        "pesquise",
        "pesquisa",
        "procure",
        "buscar",
        "busque",
        "internet",
        "na web",
        "preço atual",
        "quanto custa",
        "quanto está",
        "dólar",
        "dolar",
        "euro",
        "bitcoin",
        "resultado",
        "resultados",
        "evento atual",
        "servidor",
        "servidores"
    ]

    return any(
        palavra in pergunta
        for palavra in palavras
    )


# ==========================================
# GROQ
# ==========================================

def perguntar_groq(pergunta):

    usar_web = precisa_pesquisa(pergunta)

    if usar_web:

        model = "groq/compound-mini"

    else:

        model = "openai/gpt-oss-20b"

    response = client.chat.completions.create(

        model=model,

        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": pergunta
            }
        ],

        temperature=0.7,

        max_tokens=1000
    )

    return response.choices[0].message.content


# ==========================================
# VERCEL FUNCTION
# ==========================================

class handler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.end_headers()

        resposta = {
            "status": "online",
            "bot": "Stormy AI"
        }

        self.wfile.write(
            json.dumps(resposta).encode()
        )


    def do_POST(self):

        try:

            content_length = int(
                self.headers.get(
                    "Content-Length",
                    0
                )
            )

            body = self.rfile.read(
                content_length
            )

            data = json.loads(
                body.decode("utf-8")
            )

            pergunta = data.get(
                "pergunta"
            )

            if not pergunta:

                self.enviar_json(
                    {
                        "erro":
                        "Pergunta não informada."
                    },
                    400
                )

                return

            resposta = perguntar_groq(
                pergunta
            )

            self.enviar_json(
                {
                    "resposta": resposta
                }
            )

        except Exception as e:

            print("ERRO:", repr(e))

            self.enviar_json(
                {
                    "erro":
                    "Erro interno.",
                    "detalhes":
                    str(e)
                },
                500
            )


    def enviar_json(
        self,
        data,
        status=200
    ):

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.end_headers()

        self.wfile.write(
            json.dumps(
                data,
                ensure_ascii=False
            ).encode("utf-8")
        )