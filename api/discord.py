import os
import json
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler

from openai import OpenAI
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError


# ============================================================
# CONFIGURAÇÕES
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DISCORD_APPLICATION_ID = os.getenv("DISCORD_APPLICATION_ID")
DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY")


if not GROQ_API_KEY:
    print("⚠️ GROQ_API_KEY não configurada.")

if not DISCORD_APPLICATION_ID:
    print("⚠️ DISCORD_APPLICATION_ID não configurada.")

if not DISCORD_PUBLIC_KEY:
    print("⚠️ DISCORD_PUBLIC_KEY não configurada.")


# Cliente Groq usando API compatível com OpenAI
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)


# ============================================================
# PERSONALIDADE DO STORMY
# ============================================================

SYSTEM_PROMPT = """
Seu nome é Stormy.

Você é um assistente de Discord inteligente, prestativo,
bem-humorado e natural.

Você fala português do Brasil.

Seja amigável e responda de maneira clara.

Não invente informações.

Quando a pergunta exigir informações atuais,
recentes ou disponíveis na internet, utilize a
pesquisa na internet quando ela estiver disponível.

Se você pesquisar na internet, dê preferência a
informações recentes e confiáveis.

Não diga que você pesquisou na internet se isso não
for necessário.

Não fique explicando seu funcionamento interno.
"""


# ============================================================
# DECIDIR SE PRECISA DE INTERNET
# ============================================================

def precisa_pesquisa(pergunta: str) -> bool:

    pergunta = pergunta.lower()

    palavras = [
        "hoje",
        "agora",
        "atualmente",
        "atual",
        "recente",
        "recentemente",

        "último",
        "última",
        "últimos",
        "últimas",

        "notícia",
        "notícias",

        "update",
        "updates",

        "patch",
        "patch notes",

        "atualização",
        "atualizações",

        "versão atual",

        "pesquise",
        "pesquisar",
        "pesquisa",

        "procure",
        "procurar",

        "buscar",
        "busque",

        "internet",
        "na internet",
        "na web",

        "site",
        "sites",

        "preço atual",
        "quanto custa",
        "quanto está",

        "dólar",
        "dolar",
        "euro",
        "bitcoin",

        "servidor",
        "servidores",

        "elsword kr",
        "elsword koreia",
        "elsword korea",

        "quando foi",
        "quando aconteceu",

        "lançamento",
        "lançou",

        "2026"
    ]

    return any(
        palavra in pergunta
        for palavra in palavras
    )


# ============================================================
# CONSULTAR GROQ
# ============================================================

def perguntar_groq(pergunta: str) -> str:

    pesquisar = precisa_pesquisa(pergunta)

    if pesquisar:

        # Groq Compound Mini possui pesquisa web integrada
        model = "groq/compound-mini"

    else:

        model = "openai/gpt-oss-20b"


    print(f"🤖 Modelo escolhido: {model}")
    print(f"💬 Pergunta: {pergunta}")


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


    content = response.choices[0].message.content


    if not content:

        return "⚠️ A IA não retornou nenhuma resposta."


    return content.strip()


# ============================================================
# ENVIAR RESPOSTA PARA DISCORD
# ============================================================

def enviar_resposta_discord(
    application_id: str,
    interaction_token: str,
    conteudo: str
):

    url = (
        f"https://discord.com/api/v10/"
        f"webhooks/{application_id}/{interaction_token}"
    )


    # Discord possui limite de tamanho de mensagem.
    # Vamos dividir respostas muito grandes.
    partes = []

    limite = 1900

    while len(conteudo) > limite:

        partes.append(
            conteudo[:limite]
        )

        conteudo = conteudo[limite:]


    partes.append(conteudo)


    # Primeira mensagem edita a resposta deferida
    primeira = partes[0]

    payload = json.dumps(
        {
            "content": primeira
        }
    ).encode("utf-8")


    request = urllib.request.Request(

        url,

        data=payload,

        headers={
            "Content-Type": "application/json"
        },

        method="PATCH"
    )


    try:

        with urllib.request.urlopen(
            request,
            timeout=15
        ) as response:

            print(
                "✅ Resposta enviada:",
                response.status
            )


    except urllib.error.HTTPError as e:

        print(
            "❌ Erro ao editar resposta:",
            e.code,
            e.read().decode(
                "utf-8",
                errors="ignore"
            )
        )

        return


    # Se houver mais partes, envia como mensagens adicionais
    if len(partes) > 1:

        for parte in partes[1:]:

            payload = json.dumps(
                {
                    "content": parte
                }
            ).encode("utf-8")


            request = urllib.request.Request(

                url,

                data=payload,

                headers={
                    "Content-Type": "application/json"
                },

                method="POST"
            )


            try:

                with urllib.request.urlopen(
                    request,
                    timeout=15
                ) as response:

                    print(
                        "✅ Parte adicional enviada:",
                        response.status
                    )


            except urllib.error.HTTPError as e:

                print(
                    "❌ Erro ao enviar parte:",
                    e.code
                )


# ============================================================
# VALIDAR ASSINATURA DO DISCORD
# ============================================================

def validar_assinatura(
    body: bytes,
    signature: str,
    timestamp: str
) -> bool:

    if not DISCORD_PUBLIC_KEY:
        return False

    if not signature:
        return False

    if not timestamp:
        return False


    try:

        verify_key = VerifyKey(
            bytes.fromhex(
                DISCORD_PUBLIC_KEY
            )
        )


        mensagem = (
            timestamp.encode("utf-8")
            + body
        )


        verify_key.verify(
            mensagem,
            bytes.fromhex(signature)
        )


        return True


    except (
        BadSignatureError,
        ValueError
    ):

        return False


# ============================================================
# VERCEL HANDLER
# ============================================================

class handler(BaseHTTPRequestHandler):

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    def do_GET(self):

        resposta = {
            "status": "online",
            "bot": "Stormy AI",
            "service": "Vercel",
            "endpoint": "Discord Interactions"
        }


        self.enviar_json(
            resposta,
            200
        )


    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    def do_POST(self):

        try:

            # ================================================
            # LER BODY ORIGINAL
            # ================================================

            content_length = int(
                self.headers.get(
                    "Content-Length",
                    "0"
                )
            )


            body = self.rfile.read(
                content_length
            )


            # ================================================
            # HEADERS DO DISCORD
            # ================================================

            signature = self.headers.get(
                "X-Signature-Ed25519"
            )

            timestamp = self.headers.get(
                "X-Signature-Timestamp"
            )


            # ================================================
            # VALIDAR ASSINATURA
            # ================================================

            if not validar_assinatura(
                body,
                signature,
                timestamp
            ):

                print(
                    "❌ Assinatura inválida."
                )


                self.enviar_json(
                    {
                        "erro":
                        "Invalid request signature"
                    },
                    401
                )


                return


            # ================================================
            # TRANSFORMAR JSON
            # ================================================

            data = json.loads(
                body.decode("utf-8")
            )


            interaction_type = data.get(
                "type"
            )


            print(
                "📩 Interaction recebida:",
                interaction_type
            )


            # ================================================
            # PING DO DISCORD
            # ================================================

            # Discord envia type 1 para verificar o endpoint.
            if interaction_type == 1:

                self.enviar_json(
                    {
                        "type": 1
                    },
                    200
                )

                return


            # ================================================
            # SLASH COMMAND
            # ================================================

            if interaction_type == 2:

                dados_comando = data.get(
                    "data",
                    {}
                )


                nome_comando = dados_comando.get(
                    "name"
                )


                # --------------------------------------------
                # /stormy
                # --------------------------------------------

                if nome_comando == "stormy":

                    options = dados_comando.get(
                        "options",
                        []
                    )


                    pergunta = None


                    for option in options:

                        if option.get(
                            "name"
                        ) == "pergunta":

                            pergunta = option.get(
                                "value"
                            )

                            break


                    if not pergunta:

                        self.enviar_json(
                            {
                                "type": 4,
                                "data": {
                                    "content":
                                    "❓ Você precisa escrever uma pergunta."
                                }
                            },
                            200
                        )

                        return


                    # ----------------------------------------
                    # PEGAR TOKEN DA INTERACTION
                    # ----------------------------------------

                    interaction_token = data.get(
                        "token"
                    )


                    application_id = data.get(
                        "application_id"
                    )


                    if not interaction_token:

                        self.enviar_json(
                            {
                                "type": 4,
                                "data": {
                                    "content":
                                    "⚠️ Não consegui obter o token da interação."
                                }
                            },
                            200
                        )

                        return


                    # ----------------------------------------
                    # RESPONDER IMEDIATAMENTE
                    # ----------------------------------------

                    # Type 5 = DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
                    #
                    # Isso permite que a IA tenha tempo para
                    # responder sem o Discord considerar a
                    # Interaction expirada.
                    self.enviar_json(
                        {
                            "type": 5
                        },
                        200
                    )


                    # ----------------------------------------
                    # CONSULTAR IA
                    # ----------------------------------------

                    try:

                        resposta = perguntar_groq(
                            pergunta
                        )


                    except Exception as e:

                        print(
                            "❌ ERRO GROQ:",
                            repr(e)
                        )


                        resposta = (
                            "⚠️ Ocorreu um erro ao consultar "
                            "a inteligência artificial."
                        )


                    # ----------------------------------------
                    # ENVIAR RESULTADO
                    # ----------------------------------------

                    enviar_resposta_discord(
                        application_id,
                        interaction_token,
                        resposta
                    )


                    return


            # ================================================
            # TIPO NÃO SUPORTADO
            # ================================================

            self.enviar_json(
                {
                    "erro":
                    "Interaction type not supported"
                },
                400
            )


        except Exception as e:

            print(
                "❌ ERRO GERAL:",
                repr(e)
            )


            self.enviar_json(
                {
                    "erro":
                    "Internal server error",
                    "detalhes":
                    str(e)
                },
                500
            )


    # ========================================================
    # ENVIAR JSON
    # ========================================================

    def enviar_json(
        self,
        data,
        status=200
    ):

        resposta = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")


        self.send_response(
            status
        )


        self.send_header(
            "Content-Type",
            "application/json"
        )


        self.send_header(
            "Content-Length",
            str(len(resposta))
        )


        self.end_headers()


        self.wfile.write(
            resposta
        )