import os
import discord
from discord import app_commands
from discord.ext import commands


class MeuBot(commands.Bot):

  def __init__(self):
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    super().__init__(command_prefix="$", intents=intents)

  async def setup_hook(self):
    # Sincroniza os comandos de barra (Slash Commands)
    await self.tree.sync()


bot = MeuBot()

# Configurações globais
NOME_DO_CARGO = "putinha do skov"
CANAL_FOTOS_ID = (
    None  # Guardará o ID do canal para onde as fotos serão enviadas
)


@bot.event
async def on_ready():
  print(f"Bot conectado com sucesso como {bot.user}!")


# ==========================================
# MONITORAMENTO E SALVAMENTO DE FOTOS
# ==========================================
@bot.event
async def on_message(message: discord.Message):
  global CANAL_FOTOS_ID

  # Ignora mensagens do próprio bot ou mensagens privadas (fora de servidores)
  if message.author.bot or not message.guild:
    return

  # Se o canal de fotos foi configurado e a mensagem tem arquivos anexados
  if CANAL_FOTOS_ID and message.attachments:
    canal_destino = message.guild.get_channel(CANAL_FOTOS_ID)

    # Evita salvar fotos que forem enviadas dentro do próprio canal de fotos
    if canal_destino and message.channel.id != CANAL_FOTOS_ID:
      for anexo in message.attachments:
        # Verifica se o anexo é uma imagem
        if anexo.content_type and "image" in anexo.content_type:
          embed = discord.Embed(
              title="📸 Foto Salva!",
              description=(
                  f"👤 **Enviado por:** {message.author.mention}\n📍 **Canal de"
                  f" origem:** {message.channel.mention}"
              ),
              color=discord.Color.blue(),
          )
          embed.set_image(url=anexo.url)
          await canal_destino.send(embed=embed)

  await bot.process_commands(message)


# ==========================================
# COMANDOS (SLASH COMMANDS)
# ==========================================


# 1. Comando /stps
@bot.tree.command(
    name="stps", description="Atribui o cargo ao membro selecionado."
)
@app_commands.describe(membro="Selecione o membro que receberá o cargo")
async def stps(interaction: discord.Interaction, membro: discord.Member):
  cargo = discord.utils.get(interaction.guild.roles, name=NOME_DO_CARGO)

  if cargo is None:
    await interaction.response.send_message(
        f"⚠️ O cargo **{NOME_DO_CARGO}** não foi encontrado no servidor!",
        ephemeral=True,
    )
    return

  try:
    await membro.add_roles(cargo)
    await interaction.response.send_message(
        f"🔥 O cargo **{cargo.name}** foi atribuído a {membro.mention} com"
        " sucesso!",
        ephemeral=True,
    )
  except discord.Forbidden:
    await interaction.response.send_message(
        "❌ Permissão insuficiente. Certifique-se de que o cargo do bot está"
        " acima do cargo a ser atribuído nas configurações do servidor.",
        ephemeral=True,
    )
  except Exception as e:
    await interaction.response.send_message(
        f"❌ Erro ao atribuir cargo: {e}", ephemeral=True
    )


# 2. Comando /vzr
@bot.tree.command(name="vzr", description="Bane um usuário do servidor.")
@app_commands.describe(
    membro="Selecione o membro a ser banido",
    motivo="Motivo do banimento (opcional)",
)
async def vzr(
    interaction: discord.Interaction,
    membro: discord.Member,
    motivo: str = "Nenhum motivo fornecido",
):
  if not interaction.user.guild_permissions.ban_members:
    await interaction.response.send_message(
        "❌ Você não tem permissão para banir membros!", ephemeral=True
    )
    return

  try:
    await membro.ban(reason=motivo)
    await interaction.response.send_message(
        f"🔨 O usuário **{membro.display_name}** ({membro.mention}) foi banido"
        " do servidor!",
        ephemeral=True,
    )
  except discord.Forbidden:
    await interaction.response.send_message(
        "❌ Eu não tenho permissão para banir este usuário. Verifique minha"
        " hierarquia de cargos.",
        ephemeral=True,
    )
  except Exception as e:
    await interaction.response.send_message(
        f"❌ Erro ao banir usuário: {e}", ephemeral=True
    )


# 3. Comando /slvrfts
@bot.tree.command(
    name="slvrfts",
    description=(
        "Define o canal para onde as fotos enviadas serão reencaminhadas."
    ),
)
@app_commands.describe(
    canal="Selecione o canal onde as fotos serão salvas/enviadas"
)
async def slvrfts(interaction: discord.Interaction, canal: discord.TextChannel):
  global CANAL_FOTOS_ID
  CANAL_FOTOS_ID = canal.id
  await interaction.response.send_message(
      f"✅ Canal de fotos definido para: {canal.mention}", ephemeral=True
  )


# 4. Comando /cmnds
@bot.tree.command(
    name="cmnds", description="Exibe a lista de comandos do bot."
)
async def cmnds(interaction: discord.Interaction):
  embed = discord.Embed(
      title="📜 Lista de Comandos do Bot",
      description="Abaixo estão os comandos disponíveis:",
      color=discord.Color.green(),
  )
  embed.add_field(
      name="/stps @membro",
      value="Atribui o cargo especial ao membro indicado.",
      inline=False,
  )
  embed.add_field(
      name="/vzr @membro [motivo]",
      value="Bane o membro selecionado do servidor.",
      inline=False,
  )
  embed.add_field(
      name="/slvrfts #canal",
      value="Define em qual canal o bot deve salvar/enviar as fotos recebidas.",
      inline=False,
  )
  embed.add_field(
      name="/cmnds", value="Mostra esta mensagem de ajuda.", inline=False
  )

  await interaction.response.send_message(embed=embed, ephemeral=True)


# Inicialização do Bot
bot.run(os.getenv("DISCORD_TOKEN"))
      
