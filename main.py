import os
import discord
from discord import app_commands
from discord.ext import commands
import imageio_ffmpeg

# ==========================================
# CONFIGURAÇÕES PRINCIPAIS
# ==========================================
ID_DO_SERVIDOR = 123456789012345678  # 👈 COLOQUE O ID DO SEU SERVIDOR AQUI (apenas números)
DONO_ID = 1461858587080130663

NOME_CARGO_STPS = "putinha do skov"
NOME_CARGO_FILHINHA = "filhinha de skov"
CANAL_FOTOS_ID = None

class MeuBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Sincroniza instantaneamente no seu servidor
        if ID_DO_SERVIDOR != 123456789012345678:
            guild = discord.Object(id=ID_DO_SERVIDOR)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print("✅ Comandos Slash sincronizados instantaneamente no servidor!")
        else:
            await self.tree.sync()
            print("⚠️ ID do servidor não configurado. Sincronização global ativada (pode demorar a aparecer).")

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
# MONITORAMENTO DE MENSAGENS / FOTOS / PAPAI
# ==========================================
@bot.event
async def on_message(message: discord.Message):
    global CANAL_FOTOS_ID

    if message.author.bot or not message.guild:
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
# COMANDOS SLASH (/SLASH)
# ==========================================

# 1. /quem
@bot.tree.command(name="quem", description="Exibe quem tem permissão para mexer no bot.")
async def quem(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔒 Permissões do Bot",
        description=f"Apenas o **dono do bot** (<@{DONO_ID}>) tem acesso exclusivo para alterar e gerenciar as configurações.",
        color=discord.Color.purple()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 2. /gemer
@bot.tree.command(name="gemer", description="O bot entra na call e reproduz o áudio configurado.")
async def gemer(interaction: discord.Interaction):
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("❌ Você precisa estar em um canal de voz para usar esse comando!", ephemeral=True)
        return

    canal_voz = interaction.user.voice.channel
    guild = interaction.guild
    voice_client = guild.voice_client
    ARQUIVO_VIDEO = "gemido.mp4"

    if not os.path.exists(ARQUIVO_VIDEO):
        await interaction.response.send_message(f"❌ O arquivo `{ARQUIVO_VIDEO}` não foi encontrado no servidor do bot!", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    try:
        if voice_client is None:
            voice_client = await canal_voz.connect(reconnect=True, timeout=20.0)
        elif voice_client.channel != canal_voz:
            await voice_client.move_to(canal_voz)
    except Exception as e:
        await interaction.followup.send(f"❌ Erro ao entrar no canal de voz: {e}", ephemeral=True)
        return

    def tocar_loop(error):
        if error:
            print(f"Erro no áudio: {error}")
            return
        if voice_client and voice_client.is_connected():
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            source = discord.FFmpegPCMAudio(ARQUIVO_VIDEO, executable=ffmpeg_exe)
            voice_client.play(source, after=tocar_loop)

    if voice_client.is_playing():
        voice_client.stop()

    try:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        source = discord.FFmpegPCMAudio(ARQUIVO_VIDEO, executable=ffmpeg_exe)
        voice_client.play(source, after=tocar_loop)
        await interaction.followup.send(f"🔊 Conectado na call **{canal_voz.name}** e tocando áudio!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Erro na reprodução: {e}", ephemeral=True)

# 3. /dar
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

# 4. /stps
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

# 5. /vzr
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

# 6. /slvrfts
@bot.tree.command(name="slvrfts", description="Define o canal fixo onde as fotos enviadas serão agrupadas.")
@app_commands.describe(canal="Selecione o canal de fotos")
async def slvrfts(interaction: discord.Interaction, canal: discord.TextChannel):
    global CANAL_FOTOS_ID
    CANAL_FOTOS_ID = canal.id
    await interaction.response.send_message(f"✅ Canal de fotos definido para: {canal.mention}", ephemeral=True)

# 7. /cmnds
@bot.tree.command(name="cmnds", description="Exibe a lista de comandos do bot.")
async def cmnds(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 Lista de Comandos Slash",
        description="Confira todos os comandos disponíveis:",
        color=discord.Color.green()
    )
    embed.add_field(name="/quem", value="Exibe quem pode mexer nas configurações do bot.", inline=False)
    embed.add_field(name="/gemer", value="O bot entra na call e toca o áudio do vídeo.", inline=False)
    embed.add_field(name="/dar @membro", value="Atribui o cargo 'filhinha de skov'.", inline=False)
    embed.add_field(name="/stps @membro", value="Atribui o cargo 'putinha do skov'.", inline=False)
    embed.add_field(name="/vzr @membro", value="Bane o membro selecionado do servidor.", inline=False)
    embed.add_field(name="/slvrfts #canal", value="Define o canal fixo para onde as fotos serão encaminhadas.", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Execução do Bot
bot.run(os.getenv("DISCORD_TOKEN"))
    
