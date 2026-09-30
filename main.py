import discord
from discord.ext import commands
import os

# Configuração dos intents necessários
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="$", intents=intents)

# Nome exato do cargo
NOME_DO_CARGO = "putinha do skov"

@bot.event
async def on_ready():
    print(f"Bot conectado com sucesso como {bot.user}!")

@bot.command()
async def stps(ctx, membro: discord.Member = None):
    # Se não marcou ninguém, verifica se está respondendo a uma mensagem
    if membro is None:
        if ctx.message.reference and ctx.message.reference.message_id:
            msg_respondida = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            membro = msg_respondida.author
        else:
            await ctx.send("❌ Você precisa marcar alguém ou responder à mensagem de alguém para usar este comando!")
            return

    # Procura pelo cargo no servidor
    cargo = discord.utils.get(ctx.guild.roles, name=NOME_DO_CARGO)

    if cargo is None:
        await ctx.send(f"⚠️ O cargo **{NOME_DO_CARGO}** não existe neste servidor. Por favor, crie o cargo com esse nome exato primeiro!")
        return

    try:
        # Adiciona o cargo ao membro
        await membro.add_roles(cargo)
        await ctx.send(f"🔥 {membro.mention} agora recebeu o cargo **{cargo.name}**!")
    except discord.Forbidden:
        await ctx.send("❌ Eu não tenho permissão suficiente para dar esse cargo. Verifique se o meu cargo está **acima** do cargo que tento atribuir nas configurações do servidor!")
    except Exception as e:
        await ctx.send(f"❌ Ocorreu um erro ao atribuir o cargo: {e}")

# Puxa o Token da variável DISCORD_TOKEN configurada no Railway
bot.run(os.getenv("DISCORD_TOKEN"))
               
