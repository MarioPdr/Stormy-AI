import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from openai import OpenAI

# ==========================================
# CONFIGURAÇÕES
# ==========================================

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN não encontrado no .env")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY não encontrado no .env")


# ==========================================
# DISCORD
# ==========================================

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ==========================================
# GROQ
# ==========================================

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)


# ==========================================
# PERSONALIDADE
# ==========================================

SYSTEM_PROMPT = """
Seu nome é Stormy.

Você é um assistente de Discord inteligente.

Você conversa naturalmente em português do Brasil.

Responda de forma clara e direta.
Não seja excessivamente formal.

Nunca invente informações.

Quando receber resultados de pesquisa da internet,
use essas informações para responder.

"""


# ==========================================
# DETECTAR SE PRECISA DE INTERNET
# ==========================================

def precisa_pesquisa(pergunta):

    pergunta = pergunta.lower().strip()

    palavras_web = [

        # Tempo
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

        # Notícias
        "notícia",
        "notícias",
        "news",

        # Atualizações
        "update",
        "updates",
        "patch",
        "patch notes",
        "atualização",
        "atualizações",

        # Pesquisa
        "pesquise",
        "pesquisa",
        "procure",
        "buscar",
        "busque",
        "pesquisar",
        "internet",
        "na web",
        "na internet",

        # Preços
        "preço",
        "preço atual",
        "quanto custa",
        "quanto está",
        "valor atual",

        # Jogos
        "servidor",
        "servidores",
        "evento atual",
        "evento novo",

        # Datas
        "quando foi lançado",
        "quando lançou",
        "data de lançamento",

        # Mercado
        "dólar",
        "dolar",
        "euro",
        "bitcoin",
        "btc",

        # Redes / empresas
        "kog anunciou",
        "kog anunciou",
        "google anunciou",
        "discord anunciou",

        # Ranking / números que mudam
        "ranking atual",
        "placar",
        "resultado",
        "resultados"
    ]

    for palavra in palavras_web:

        if palavra in pergunta:
            return True

    return False


# ==========================================
# HISTÓRICO
# ==========================================

async def historico(canal, limit=10):

    messages_list = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    mensagens = []

    async for message in canal.history(limit=limit):

        if not message.content:
            continue

        # Ignorar bots
        if message.author.bot and message.author.id != bot.user.id:
            continue

        conteudo = message.content.strip()

        # Remover !stormy
        if conteudo.startswith("!stormy"):
            conteudo = conteudo[len("!stormy"):].strip()

        if not conteudo:
            continue

        if message.author.id == bot.user.id:
            role = "assistant"
        else:
            role = "user"

        mensagens.append({
            "role": role,
            "content": conteudo
        })

    # Ordem cronológica
    mensagens.reverse()

    messages_list.extend(mensagens)

    return messages_list


# ==========================================
# GROQ NORMAL
# ==========================================

def ask_groq(messages):

    try:

        print("\n===================================")
        print("🤖 GROQ NORMAL")
        print("===================================")

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )

        content = response.choices[0].message.content

        print("Modelo:", response.model)
        print("Resposta:", repr(content))

        if not content:
            return None

        content = content.strip()

        if not content:
            return None

        print("✅ Groq respondeu!")

        return content

    except Exception as e:

        print("\n❌ ERRO GROQ:")
        print(repr(e))

        return None


# ==========================================
# GROQ COM PESQUISA WEB
# ==========================================

def ask_groq_web(messages):

    try:

        print("\n===================================")
        print("🌐 GROQ COM WEB SEARCH")
        print("===================================")

        response = client.chat.completions.create(
            model="groq/compound-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )

        content = response.choices[0].message.content

        print("Modelo:", response.model)
        print("Resposta:", repr(content))

        # Verificar ferramentas
        message = response.choices[0].message

        if hasattr(message, "executed_tools"):
            print("\n🔎 FERRAMENTAS UTILIZADAS:")
            print(message.executed_tools)

        if not content:
            return None

        content = content.strip()

        if not content:
            return None

        print("✅ Pesquisa + IA responderam!")

        return content

    except Exception as e:

        print("\n❌ ERRO GROQ WEB:")
        print(repr(e))

        return None


# ==========================================
# SISTEMA PRINCIPAL
# ==========================================

def perguntar_ia(messages, pergunta):

    # ======================================
    # VERIFICAR SE PRECISA DA INTERNET
    # ======================================

    usar_web = precisa_pesquisa(pergunta)

    if usar_web:

        print("\n🌐 Pesquisa na internet necessária.")

        resposta = ask_groq_web(messages)

        if resposta:
            return resposta

        # Se Web Search falhar,
        # tenta Groq normal
        print(
            "⚠️ Web Search falhou. "
            "Tentando Groq normal..."
        )

        resposta = ask_groq(messages)

        if resposta:
            return resposta

    else:

        print("\n💬 Pergunta comum.")
        print("🌐 Web Search NÃO será utilizada.")

        resposta = ask_groq(messages)

        if resposta:
            return resposta

    # ======================================
    # ERRO
    # ======================================

    return (
        "⚠️ Não consegui obter uma resposta "
        "da IA neste momento."
    )


# ==========================================
# BOT ONLINE
# ==========================================

@bot.event
async def on_ready():

    print("")
    print("===================================")
    print("          STORMY ONLINE")
    print("===================================")
    print(f"Nome: {bot.user}")
    print(f"ID: {bot.user.id}")
    print("-----------------------------------")
    print("Groq GPT-OSS: 🟢")
    print("Web Search: 🟢")
    print("===================================")
    print("")


# ==========================================
# COMANDO !STORMY
# ==========================================

@bot.command(name="stormy")
async def stormy_cmd(ctx, *, pergunta: str = None):

    if not pergunta:

        await ctx.reply(
            "Olá! 👋\n\n"
            "Digite uma pergunta depois do comando.\n\n"
            "Exemplo:\n"
            "`!stormy qual foi o último update do Elsword KR?`"
        )

        return

    async with ctx.typing():

        try:

            # Histórico
            messages = await historico(
                ctx.channel,
                limit=10
            )

            # Pergunta atual
            messages.append({
                "role": "user",
                "content": pergunta.strip()
            })

            print("\n")
            print("===================================")
            print("PERGUNTA RECEBIDA")
            print("===================================")
            print(pergunta)
            print("===================================")

            # IA
            resposta = perguntar_ia(
                messages,
                pergunta
            )

            # Limite do Discord
            if len(resposta) > 2000:
                resposta = resposta[:1990] + "..."

            # Segurança
            if not resposta.strip():

                resposta = (
                    "⚠️ Não consegui gerar uma resposta."
                )

            await ctx.reply(resposta)

        except Exception as e:

            print("\n")
            print("===================================")
            print("❌ ERRO NO BOT")
            print("===================================")
            print(repr(e))
            print("===================================")

            await ctx.reply(
                "⚠️ Ocorreu um erro ao processar "
                "sua pergunta."
            )


# ==========================================
# MENSAGENS
# ==========================================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    await bot.process_commands(message)


# ==========================================
# INICIAR
# ==========================================

bot.run(DISCORD_BOT_TOKEN)