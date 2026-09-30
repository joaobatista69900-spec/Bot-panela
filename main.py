import os
import ctypes
import discord
from discord import app_commands
from discord.ext import commands
import imageio_ffmpeg

# ==========================================
# CARREGAMENTO FORÇADO DO OPUS VIA PYTHON
# ==========================================
def carregar_opus():
    if discord.opus.is_loaded():
        return True

    # Tenta carregar usando a biblioteca nativa empacotada no Python
    try:
        import opuslib_sys
        # Tenta pegar o caminho do arquivo compilado do opuslib_sys
        opus_path = opuslib_sys._opus_lib_path
        discord.opus.load_opus(opus_path)
        print(f"✅ Opus carregado via opuslib_sys: {opus_path}")
        return True
    except Exception as e:
        print(f"⚠️ Erro ao carregar via opuslib_sys: {e}")

    # Outras tentativas padrão de fallback no Linux
    caminhos_fallback = [
        'libopus.so.0',
        'libopus.so',
        '/usr/lib/x86_64-linux-gnu/libopus.so.0',
        '/usr/lib/libopus.so.0'
    ]
    for caminho in caminhos_fallback:
        try:
            discord.opus.load_opus(caminho)
            print(f"✅ Opus carregado via fallback: {caminho}")
            return True
        except Exception:
            continue

    return False

carregar_opus()

# ==========================================
# CONFIGURAÇÕES PRINCIPAIS
# ==========================================
DONO_ID = 1461858587080130663

NOME_CARGO_STPS = "putinha do skov"
NOME_CARGO_FILHINHA = "filhinha de skov"
CANAL_FOTOS_ID = None

AGUARDANDO_ARQUIVO_GEMIDO = False
USUARIO_AGUARDANDO_ID = None

class MeuBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.voice_states = True
        super().__init__(command_prefix=["$", "!"], intents=intents)

    async def setup_hook(self):
        await self.tree.sync()

bot = MeuBot()

@bot.event
async def on_ready():
    print(f"🔥 Bot conectado e rodando como {bot.user}!")

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
# MONITORAMENTO DE MENSAGENS / FOTOS / DOWNLOAD
# ==========================================
@bot.event
async def on_message(message: discord.Message):
    global CANAL_FOTOS_ID, AGUARDANDO_ARQUIVO_GEMIDO, USUARIO_AGUARDANDO_ID

    if message.author.bot or not message.guild:
        return

    # --- BAIXAR ARQUIVO SOLICITADO VIA $gemer ---
    if AGUARDANDO_ARQUIVO_GEMIDO and message.author.id == USUARIO_AGUARDANDO_ID:
        if message.attachments:
            anexo = message.attachments[0]
            try:
                await anexo.save("gemido.mp4")
                AGUARDANDO_ARQUIVO_GEMIDO = False
                USUARIO_AGUARDANDO_ID = None
                await message.channel.send("✅ Arquivo recebido e copiado com sucesso! Entre na call e digite `$entrarcallgemer`.")
                return
            except Exception as e:
                await message.channel.send(f"❌ Erro ao salvar o arquivo: {e}")
                return

    # --- AUTOMATISMO DO "PAPAI" ---
    conteudo = message.content.lower()
    if "papai" in conteudo:
        skov_member = discord.utils.find(
            lambda m: (m.nick and "skov pdx" in m.nick.lower()) or ("skov pdx" in m.name.lower()),
            message.guild.members
        )

        if skov_member:
            chamou_skov = False
            if skov_member in message.mentions:
                chamou_skov = True
            elif message.reference and message.reference.resolved:
                if isinstance(message.reference.resolved, discord.Message):
                    if message.reference.resolved.author.id == skov_member.id:
                        chamou_skov = True

            if chamou_skov:
                cargo_filhinha = discord.utils.get(message.guild.roles, name=NOME_CARGO_FILHINHA)
                if cargo_filhinha:
                    try:
                        await message.author.add_roles(cargo_filhinha)
                        await message.channel.send(
                            f"✨ {message.author.mention} chamou o {skov_member.mention} de papai e recebeu o cargo **{cargo_filhinha.name}**!"
                        )
                    except Exception as e:
                        print(f"Erro ao atribuir cargo automático: {e}")

    # --- SALVAR/ENCAMINHAR FOTOS ---
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
# COMANDOS COM PREFIXO $
# ==========================================

# 1. $quem
@bot.command(name="quem")
async def quem_cmd(ctx):
    embed = discord.Embed(
        title="🔒 Permissões do Bot",
        description=f"Apenas o **dono do bot** (<@{DONO_ID}>) tem acesso exclusivo para alterar e gerenciar as configurações.",
        color=discord.Color.purple()
    )
    await ctx.send(embed=embed)

# 2. $gemer
@bot.command(name="gemer")
async def gemer_cmd(ctx):
    global AGUARDANDO_ARQUIVO_GEMIDO, USUARIO_AGUARDANDO_ID
    AGUARDANDO_ARQUIVO_GEMIDO = True
    USUARIO_AGUARDANDO_ID = ctx.author.id
    await ctx.send("Envia o arquivo que irei copiar o som")

# 3. $entrarcallgemer
@bot.command(name="entrarcallgemer")
async def entrarcallgemer_cmd(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ Você precisa estar em um canal de voz para usar esse comando!")
        return

    if not discord.opus.is_loaded():
        carregar_opus()

    if not discord.opus.is_loaded():
        await ctx.send("❌ A biblioteca de áudio Opus não está carregada no servidor do bot.")
        return

    canal_voz = ctx.author.voice.channel
    voice_client = ctx.voice_client
    ARQUIVO_VIDEO = "gemido.mp4"

    if not os.path.exists(ARQUIVO_VIDEO):
        await ctx.send("❌ Nenhum arquivo de som foi enviado ainda! Digite `$gemer` e envie o arquivo primeiro.")
        return

    msg_espera = await ctx.send("⏳ Conectando e preparando áudio...")

    try:
        if voice_client is None:
            voice_client = await canal_voz.connect(reconnect=True, timeout=20.0)
        elif voice_client.channel != canal_voz:
            await voice_client.move_to(canal_voz)
    except Exception as e:
        await msg_espera.edit(content=f"❌ Erro ao entrar no canal de voz: `{e}`")
        return

    try:
        try:
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ffmpeg_exe = "ffmpeg"

        if voice_client.is_playing():
            voice_client.stop()

        source = discord.FFmpegPCMAudio(
            ARQUIVO_VIDEO,
            executable=ffmpeg_exe,
            options="-vn"
        )

        voice_client.play(source)
        await msg_espera.edit(content=f"🔊 Conectado na call **{canal_voz.name}** e tocando áudio!")

    except Exception as e:
        await msg_espera.edit(content=f"❌ Erro na reprodução: `{type(e).__name__}: {e}`")

# ==========================================
# COMANDOS SLASH (/SLASH)
# ==========================================

@bot.tree.command(name="dar", description="Atribui o cargo filhinha de skov.")
@app_commands.describe(membro="Selecione o membro que receberá o cargo")
async def dar(interaction: discord.Interaction, membro: discord.Member):
    cargo = discord.utils.get(interaction.guild.roles, name=NOME_CARGO_FILHINHA)
    if cargo is None:
        await interaction.response.send_message(f"⚠️ O cargo **{NOME_CARGO_FILHINHA}** não foi encontrado!", ephemeral=True)
        return
    try:
        await membro.add_roles(cargo)
        await interaction.response.send_message(f"💖 O cargo **{cargo.name}** foi atribuído a {membro.mention}!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao atribuir cargo: {e}", ephemeral=True)

@bot.tree.command(name="stps", description="Atribui o cargo putinha do skov.")
@app_commands.describe(membro="Selecione o membro que receberá o cargo")
async def stps(interaction: discord.Interaction, membro: discord.Member):
    cargo = discord.utils.get(interaction.guild.roles, name=NOME_CARGO_STPS)
    if cargo is None:
        await interaction.response.send_message(f"⚠️ O cargo **{NOME_CARGO_STPS}** não foi encontrado!", ephemeral=True)
        return
    try:
        await membro.add_roles(cargo)
        await interaction.response.send_message(f"🔥 O cargo **{cargo.name}** foi atribuído a {membro.mention}!", ephemeral=True)
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

@bot.tree.command(name="slvrfts", description="Define o canal fixo onde as fotos enviadas serão agrupadas.")
@app_commands.describe(canal="Selecione o canal de fotos")
async def slvrfts(interaction: discord.Interaction, canal: discord.TextChannel):
    global CANAL_FOTOS_ID
    CANAL_FOTOS_ID = canal.id
    await interaction.response.send_message(f"✅ Canal de fotos definido para: {canal.mention}", ephemeral=True)

@bot.tree.command(name="cmnds", description="Exibe a lista de comandos do bot.")
async def cmnds(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 Lista de Comandos",
        description="Confira todos os comandos disponíveis:",
        color=discord.Color.green()
    )
    embed.add_field(name="$quem", value="Exibe quem pode mexer nas configurações do bot.", inline=False)
    embed.add_field(name="$gemer", value="Prepara o bot para receber o arquivo de som.", inline=False)
    embed.add_field(name="$entrarcallgemer", value="Entra na call e toca o som enviado.", inline=False)
    embed.add_field(name="/dar @membro", value="Atribui o cargo 'filhinha de skov'.", inline=False)
    embed.add_field(name="/stps @membro", value="Atribui o cargo 'putinha do skov'.", inline=False)
    embed.add_field(name="/vzr @membro", value="Bane o membro selecionado do servidor.", inline=False)
    embed.add_field(name="/slvrfts #canal", value="Define o canal fixo para onde as fotos serão encaminhadas.", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Execução do Bot
bot.run(os.getenv("DISCORD_TOKEN"))
