import os
import discord

from discord.ext import commands
from dotenv import load_dotenv
from groq import Groq


# ============================================================
# CONFIGURAÇÃO
# ============================================================

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


if not DISCORD_BOT_TOKEN:
    raise ValueError(
        "❌ DISCORD_BOT_TOKEN não encontrado no .env"
    )

if not GROQ_API_KEY:
    raise ValueError(
        "❌ GROQ_API_KEY não encontrado no .env"
    )


# ============================================================
# DISCORD
# ============================================================

intents = discord.Intents.default()

intents.messages = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ============================================================
# GROQ
# ============================================================

client = Groq(
    api_key=GROQ_API_KEY
)


# ============================================================
# PERSONALIDADE
# ============================================================

SYSTEM_PROMPT = """
Seu nome é Stormy.

Você é uma assistente de Discord inteligente.

Você conversa naturalmente em português do Brasil.

Responda de forma clara, natural e direta.

Não seja excessivamente formal.

Nunca invente informações.

IMPORTANTE:

Quando a pergunta envolver informações atuais,
recentes, notícias, resultados, jogos, eventos,
preços, atualizações, lançamentos, pessoas,
empresas, servidores ou qualquer informação
que possa ter mudado, pesquise na internet.

Quando uma pesquisa na internet for fornecida,
use os resultados encontrados como fonte principal.

Não contradiga os resultados atuais da pesquisa
com conhecimento antigo do modelo.

Se a pesquisa mostrar que algo aconteceu,
considere a informação encontrada na pesquisa.

Se houver conflito entre conhecimento antigo
e informação encontrada na internet,
confie na informação mais recente encontrada.

Não invente datas, números, resultados ou nomes.

Responda sempre em português do Brasil.
"""


# ============================================================
# DETECTAR SE PRECISA DE PESQUISA
# ============================================================

def precisa_pesquisa(pergunta):

    pergunta = pergunta.lower().strip()

    termos_web = [

        # ----------------------------------------------------
        # ATUALIDADE
        # ----------------------------------------------------

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

        "mais recente",
        "recentes",

        # ----------------------------------------------------
        # PESQUISA
        # ----------------------------------------------------

        "pesquise",
        "pesquisa",
        "pesquisar",
        "procure",
        "procurar",
        "buscar",
        "busque",

        "internet",
        "na internet",
        "web",
        "na web",

        # ----------------------------------------------------
        # NOTÍCIAS
        # ----------------------------------------------------

        "notícia",
        "notícias",
        "news",

        # ----------------------------------------------------
        # JOGOS
        # ----------------------------------------------------

        "elsword",
        "elsword kr",
        "elsword korea",
        "elsword coreia",

        "kog",

        "servidor",
        "servidores",
        "server",
        "servers",

        "evento",
        "eventos",

        "patch",
        "patch notes",

        "update",
        "updates",

        "atualização",
        "atualizações",

        "manutenção",
        "maintenance",

        "changelog",

        # ----------------------------------------------------
        # RESULTADOS
        # ----------------------------------------------------

        "quem ganhou",
        "quem venceu",
        "quem ganhou a",
        "quem venceu a",

        "quem foi campeão",
        "quem foi campeã",

        "campeão",
        "campeã",

        "vencedor",
        "vencedora",

        "resultado",
        "resultados",

        "placar",

        "ranking",
        "classificação",

        # ----------------------------------------------------
        # ESPORTES
        # ----------------------------------------------------

        "copa do mundo",
        "copa",

        "mundial",

        "champions",
        "champions league",

        "libertadores",

        "brasileirão",

        "nba",
        "nfl",
        "ufc",

        "jogo de hoje",
        "jogo de ontem",

        # ----------------------------------------------------
        # DATAS
        # ----------------------------------------------------

        "quando aconteceu",
        "quando aconteceu",

        "quando lançou",
        "quando lançou",

        "quando foi lançado",
        "data de lançamento",

        # ----------------------------------------------------
        # PREÇOS
        # ----------------------------------------------------

        "preço",
        "preço atual",

        "quanto custa",
        "quanto está",

        "valor atual",

        # ----------------------------------------------------
        # MOEDAS
        # ----------------------------------------------------

        "dólar",
        "dolar",

        "euro",

        "bitcoin",
        "btc",

        "ethereum",
        "eth",

        # ----------------------------------------------------
        # EMPRESAS
        # ----------------------------------------------------

        "google",
        "openai",
        "discord",
        "groq",

        # ----------------------------------------------------
        # REDES
        # ----------------------------------------------------

        "twitter",
        "instagram",
        "reddit",

        # ----------------------------------------------------
        # SITES
        # ----------------------------------------------------

        "site",
        "link",
        "url",

        # ----------------------------------------------------
        # ANOS
        # ----------------------------------------------------

        "2024",
        "2025",
        "2026",
        "2027",
        "2028",
        "2029",
        "2030"
    ]


    for termo in termos_web:

        if termo in pergunta:
            return True


    return False


# ============================================================
# HISTÓRICO
# ============================================================

async def historico(canal, limit=10):

    mensagens = []

    async for message in canal.history(limit=limit):

        if not message.content:
            continue


        # Ignorar bots que não sejam a Stormy
        if message.author.bot:

            if not bot.user:
                continue

            if message.author.id != bot.user.id:
                continue


        conteudo = message.content.strip()


        # Remover !stormy
        if conteudo.lower().startswith("!stormy"):

            conteudo = conteudo[7:].strip()


        if not conteudo:
            continue


        if bot.user and message.author.id == bot.user.id:

            role = "assistant"

        else:

            role = "user"


        mensagens.append({
            "role": role,
            "content": conteudo
        })


    # Discord entrega do mais recente para o antigo
    mensagens.reverse()


    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]


    messages.extend(mensagens)


    return messages


# ============================================================
# GROQ NORMAL
# ============================================================

def ask_groq(messages):

    try:

        print()
        print("===================================")
        print("💬 GROQ NORMAL")
        print("===================================")


        response = client.chat.completions.create(

            model="openai/gpt-oss-20b",

            messages=messages,

            temperature=0.7,

            max_completion_tokens=1000
        )


        resposta = response.choices[0].message.content


        print("Modelo:", response.model)

        print(
            "Resposta:",
            repr(resposta)
        )


        if not resposta:
            return None


        resposta = resposta.strip()


        if not resposta:
            return None


        print("✅ Groq respondeu!")


        return resposta


    except Exception as e:

        print()
        print("❌ ERRO GROQ NORMAL:")
        print(repr(e))

        return None


# ============================================================
# GROQ + BROWSER SEARCH
# ============================================================

def ask_groq_web(messages):

    try:

        print()
        print("===================================")
        print("🌐 GROQ + BROWSER SEARCH")
        print("===================================")

        print(
            "🔎 Pesquisa na internet será obrigatória."
        )


        response = client.chat.completions.create(

            model="openai/gpt-oss-20b",

            messages=messages,

            temperature=1,

            max_completion_tokens=2000,

            top_p=1,

            stream=False,

            tool_choice="required",

            tools=[
                {
                    "type": "browser_search"
                }
            ]
        )


        message = response.choices[0].message


        resposta = message.content


        print()
        print("===================================")
        print("🔎 RESULTADO DA PESQUISA")
        print("===================================")


        print(
            repr(resposta)
        )


        # ----------------------------------------------------
        # FERRAMENTAS
        # ----------------------------------------------------

        if hasattr(message, "executed_tools"):

            print()
            print("🛠️ FERRAMENTAS UTILIZADAS:")

            print(
                message.executed_tools
            )


        # ----------------------------------------------------

        if not resposta:

            print(
                "❌ Pesquisa não retornou texto."
            )

            return None


        resposta = resposta.strip()


        if not resposta:

            return None


        print()
        print("✅ PESQUISA + RESPOSTA CONCLUÍDAS!")


        return resposta


    except Exception as e:

        print()
        print("===================================")
        print("❌ ERRO BROWSER SEARCH")
        print("===================================")

        print(
            repr(e)
        )

        return None


# ============================================================
# SISTEMA PRINCIPAL
# ============================================================

def perguntar_ia(messages, pergunta):

    usar_web = precisa_pesquisa(
        pergunta
    )


    # ========================================================
    # INTERNET
    # ========================================================

    if usar_web:

        print()
        print("🌐 PERGUNTA ATUAL.")
        print("🔎 INTERNET NECESSÁRIA.")


        resposta = ask_groq_web(
            messages
        )


        if resposta:

            return resposta


        # ----------------------------------------------------
        # FALLBACK
        # ----------------------------------------------------

        print()
        print(
            "⚠️ Browser Search falhou."
        )

        print(
            "🔄 Tentando Groq normal..."
        )


        resposta = ask_groq(
            messages
        )


        if resposta:

            return resposta


    # ========================================================
    # SEM INTERNET
    # ========================================================

    else:

        print()
        print("💬 PERGUNTA NORMAL.")
        print(
            "🌐 Pesquisa não necessária."
        )


        resposta = ask_groq(
            messages
        )


        if resposta:

            return resposta


    # ========================================================
    # ERRO
    # ========================================================

    return (
        "⚠️ Não consegui obter uma resposta "
        "da IA neste momento."
    )


# ============================================================
# BOT ONLINE
# ============================================================

@bot.event
async def on_ready():

    print()
    print("===================================")
    print("          STORMY ONLINE")
    print("===================================")

    print(
        f"Nome: {bot.user}"
    )

    print(
        f"ID: {bot.user.id}"
    )

    print("-----------------------------------")

    print(
        "Groq GPT-OSS: 🟢"
    )

    print(
        "Browser Search: 🟢"
    )

    print("===================================")
    print()


# ============================================================
# COMANDO !STORMY
# ============================================================

@bot.command(name="stormy")
async def stormy_cmd(
    ctx,
    *,
    pergunta: str = None
):

    # ========================================================
    # SEM PERGUNTA
    # ========================================================

    if not pergunta:

        await ctx.reply(

            "Olá! 👋\n\n"

            "Digite uma pergunta depois "
            "do comando.\n\n"

            "Exemplo:\n"

            "`!stormy quem ganhou a Copa "
            "do Mundo de 2026?`"
        )

        return


    # ========================================================
    # PROCESSANDO
    # ========================================================

    async with ctx.typing():

        try:

            # ------------------------------------------------
            # HISTÓRICO
            # ------------------------------------------------

            messages = await historico(
                ctx.channel,
                limit=10
            )


            # ------------------------------------------------
            # PERGUNTA ATUAL
            # ------------------------------------------------

            messages.append({

                "role": "user",

                "content": pergunta.strip()
            })


            # ------------------------------------------------
            # LOG
            # ------------------------------------------------

            print()
            print("===================================")
            print("📩 PERGUNTA RECEBIDA")
            print("===================================")

            print(pergunta)

            print("===================================")


            # ------------------------------------------------
            # IA
            # ------------------------------------------------

            resposta = perguntar_ia(

                messages,

                pergunta
            )


            # ------------------------------------------------
            # SEGURANÇA
            # ------------------------------------------------

            if not resposta:

                resposta = (
                    "⚠️ Não consegui gerar "
                    "uma resposta."
                )


            resposta = resposta.strip()


            # ------------------------------------------------
            # LIMITE DO DISCORD
            # ------------------------------------------------

            if len(resposta) > 2000:

                resposta = (
                    resposta[:1990]
                    + "..."
                )


            # ------------------------------------------------
            # RESPONDER
            # ------------------------------------------------

            await ctx.reply(
                resposta
            )


        except Exception as e:

            print()
            print("===================================")
            print("❌ ERRO NO BOT")
            print("===================================")

            print(
                repr(e)
            )

            print("===================================")


            try:

                await ctx.reply(
                    "⚠️ Ocorreu um erro "
                    "ao processar sua pergunta."
                )

            except Exception:

                pass


# ============================================================
# MENSAGENS
# ============================================================

@bot.event
async def on_message(message):

    if message.author.bot:
        return


    await bot.process_commands(
        message
    )


# ============================================================
# INICIAR
# ============================================================

print()
print("🚀 Iniciando Stormy...")
print()

bot.run(
    DISCORD_BOT_TOKEN
)