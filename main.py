import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import imageio_ffmpeg

class MeuBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()

bot = MeuBot()

# Configurações globais
NOME_DO_CARGO = "putinha do skov"
CANAL_FOTOS_ID = None

# Configuração do YTDL forçando busca no SoundCloud (scsearch)
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'scsearch',
    'nocheckcertificate': True,
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

@bot.event
async def on_ready():
    print(f"Bot conectado com sucesso como {bot.user}!")

# ==========================================
# COMANDO DE MÚSICA (!tocar)
# ==========================================
@bot.command(name="tocar")
async def tocar(ctx, *, busca: str = None):
    if not busca:
        await ctx.send("❌ Você precisa indicar o nome ou link da música! Exemplo: `!tocar nome da musica`")
        return

    # Verifica se o usuário está em um canal de voz
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ Você precisa estar em um canal de voz para eu entrar!")
        return

    canal_voz = ctx.author.voice.channel
    voice_client = ctx.voice_client

    # Conecta ou move para o canal de voz
    try:
        if voice_client is None:
            voice_client = await canal_voz.connect(reconnect=True, timeout=20.0)
        elif voice_client.channel != canal_voz:
            await voice_client.move_to(canal_voz)
    except Exception as e:
        await ctx.send(f"❌ Não consegui entrar na call: {e}")
        return

    # Garante estabilidade da conexão de voz
    contador = 0
    while not voice_client.is_connected():
        await asyncio.sleep(0.5)
        contador += 1
        if contador > 10:
            await ctx.send("❌ A conexão com o canal de voz demorou demais. Tente novamente!")
            return

    msg_espera = await ctx.send("🔍 Procurando a música no SoundCloud, aguarde...")

    # Extrai o link de áudio via SoundCloud
    loop = asyncio.get_event_loop()
    try:
        with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ytdl:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(busca, download=False))
            if 'entries' in data and len(data['entries']) > 0:
                data = data['entries'][0]

            url_stream = data.get('url')
            titulo = data.get('title', 'Música')

            if not url_stream:
                await msg_espera.edit(content="❌ Não foi possível obter o áudio no SoundCloud.")
                return

    except Exception as e:
        await msg_espera.edit(content=f"❌ Erro ao buscar no SoundCloud:\n`{e}`")
        return

    # Se já estiver a tocar algo, interrompe
    if voice_client.is_playing():
        voice_client.stop()

    # Toca o áudio diretamente via FFmpeg (Sem precisar baixar)
    try:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        source = discord.FFmpegPCMAudio(url_stream, executable=ffmpeg_exe, **FFMPEG_OPTIONS)
        
        voice_client.play(source, after=lambda e: print(f'Erro na reprodução: {e}') if e else None)
        await msg_espera.edit(content=f"🎶 **Tocando agora (SoundCloud):** `{titulo}` na call **{canal_voz.name}**!")
    except Exception as e:
        await msg_espera.edit(content=f"❌ Erro ao iniciar o áudio: {e}")

# Comando para fazer o bot sair da call
@bot.command(name="parar")
async def parar(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Saí do canal de voz!")
    else:
        await ctx.send("❌ Eu não estou em nenhum canal de voz no momento.")

# ==========================================
# BOAS-VINDAS ESTILO GF
# ==========================================
@bot.event
async def on_member_join(member: discord.Member):
    try:
        embed_pv = discord.Embed(
            title="Oii, amor! 💕",
            description=f"Que bom que você chegou, {member.mention}! Tava morrendo de saudades suas... Seja muito bem-vindo(a) ao nosso servidor! 🥰",
            color=discord.Color.pink()
        )
        await member.send(embed=embed_pv)
    except discord.Forbidden:
        pass

    canal_boas_vindas = member.guild.system_channel
    if not canal_boas_vindas:
        canal_boas_vindas = next((c for c in member.guild.text_channels if c.permissions_for(member.guild.me).send_messages), None)

    if canal_boas_vindas:
        embed_chat = discord.Embed(
            title="Oii meu bem! ❤️",
            description=f"Oii {member.mention}, tava com muita saudade de você! ✨\nFico muito feliz que você chegou por aqui, aproveite o servidor!",
            color=discord.Color.magenta()
        )
        embed_chat.set_thumbnail(url=member.display_avatar.url)
        await canal_boas_vindas.send(embed=embed_chat)

# ==========================================
# SALVAR/ENCAMINHAR FOTOS
# ==========================================
@bot.event
async def on_message(message: discord.Message):
    global CANAL_FOTOS_ID

    if message.author.bot or not message.guild:
        return

    if message.attachments:
        if CANAL_FOTOS_ID:
            canal_destino = message.guild.get_channel(CANAL_FOTOS_ID)
        else:
            canal_destino = message.channel

        if canal_destino:
            for anexo in message.attachments:
                if anexo.content_type and "image" in anexo.content_type:
                    embed = discord.Embed(
                        title="📸 Foto Encaminhada!",
                        description=f"👤 **Enviado por:** {message.author.mention}\n📍 **Canal de origem:** {message.channel.mention}",
                        color=discord.Color.blue()
                    )
                    embed.set_image(url=anexo.url)
                    await canal_destino.send(embed=embed)

    await bot.process_commands(message)

# ==========================================
# COMANDOS DE BARRA (/slash)
# ==========================================
@bot.tree.command(name="stps", description="Atribui o cargo ao membro selecionado.")
@app_commands.describe(membro="Selecione o membro que receberá o cargo")
async def stps(interaction: discord.Interaction, membro: discord.Member):
    cargo = discord.utils.get(interaction.guild.roles, name=NOME_DO_CARGO)
    if cargo is None:
        await interaction.response.send_message(f"⚠️️ O cargo **{NOME_DO_CARGO}** não foi encontrado no servidor!", ephemeral=True)
        return
    try:
        await membro.add_roles(cargo)
        await interaction.response.send_message(f"🔥 O cargo **{cargo.name}** foi atribuído a {membro.mention} com sucesso!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao atribuir cargo: {e}", ephemeral=True)

@bot.tree.command(name="vzr", description="Bane um usuário do servidor.")
@app_commands.describe(membro="Selecione o membro a ser banido", motivo="Motivo do banimento")
async def vzr(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Nenhum motivo fornecido"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ Você não tem permissão para banir membros!", ephemeral=True)
        return
    try:
        await membro.ban(reason=motivo)
        await interaction.response.send_message(f"🔨 O usuário **{membro.display_name}** foi banido!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao banir usuário: {e}", ephemeral=True)

@bot.tree.command(name="slvrfts", description="Define o canal fixo de fotos.")
@app_commands.describe(canal="Selecione o canal")
async def slvrfts(interaction: discord.Interaction, canal: discord.TextChannel):
    global CANAL_FOTOS_ID
    CANAL_FOTOS_ID = canal.id
    await interaction.response.send_message(f"✅ Canal de fotos definido para: {canal.mention}", ephemeral=True)

@bot.tree.command(name="cmnds", description="Exibe a lista de comandos do bot.")
async def cmnds(interaction: discord.Interaction):
    embed = discord.Embed(title="📜 Lista de Comandos", color=discord.Color.green())
    embed.add_field(name="!tocar <nome ou link>", value="O bot entra na call e toca a música via SoundCloud.", inline=False)
    embed.add_field(name="!parar", value="Para de tocar e sai da call de voz.", inline=False)
    embed.add_field(name="/stps @membro", value="Atribui o cargo especial ao membro indicado.", inline=False)
    embed.add_field(name="/vzr @membro", value="Bane o membro selecionado.", inline=False)
    embed.add_field(name="/slvrfts #canal", value="Define o canal para salvar fotos.", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Inicialização do Bot
bot.run(os.getenv("DISCORD_TOKEN"))
                                                   
