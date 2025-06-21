
import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
from keep_alive import keep_alive

# Configurações do bot
CHANNEL_ID = 1378286447701786694  # ID do canal onde as mensagens serão enviadas
DELETE_AFTER = 300  # 5 minutos em segundos

# Configurar intents
intents = discord.Intents.default()
intents.members = True  # Necessário para detectar novos membros
intents.message_content = True  # Necessário para comandos funcionarem

# Criar o bot
bot = commands.Bot(command_prefix='#', intents=intents)

@bot.event
async def on_ready():
    print(f'🚀 Bot {bot.user} está online!')
    print(f'📋 Conectado a {len(bot.guilds)} servidor(es)')
    
    # Configurar status do bot
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="novos membros chegarem!"
        )
    )

@bot.event
async def on_member_join(member):
    """Evento chamado quando um novo membro entra no servidor"""
    print(f"🔔 Novo membro detectado: {member.display_name} ({member.id}) no servidor {member.guild.name}")
    
    # Buscar o canal pelo ID
    channel = bot.get_channel(CHANNEL_ID)
    
    if channel is None:
        print(f"❌ Canal com ID {CHANNEL_ID} não encontrado!")
        # Listar canais disponíveis para debug
        print("📋 Canais disponíveis:")
        for guild in bot.guilds:
            for ch in guild.text_channels:
                print(f"  - {ch.name} (ID: {ch.id})")
        return
    
    print(f"✅ Canal encontrado: {channel.name}")
    
    # Verificar permissões do bot no canal
    permissions = channel.permissions_for(member.guild.me)
    if not permissions.send_messages:
        print(f"❌ Bot não tem permissão para enviar mensagens no canal {channel.name}")
        return
    
    if not permissions.embed_links:
        print(f"⚠️ Bot não tem permissão para enviar embeds no canal {channel.name}")
    
    # Criar embed bonito para a mensagem de boas-vindas
    embed = discord.Embed(
        title="🎉 Novo Membro!",
        description=f"O **{member.display_name}** acabou de entrar no servidor, ajude-o caso necessário!",
        color=0x00ff56  # Cor verde
    )
    
    # Adicionar informações do membro
    embed.add_field(
        name="<:membromxp:1384773599046537257> Membro",
        value=member.mention,
        inline=True
    )
    
    embed.add_field(
        name="<:textomxp:1384773717271511180> Conta criada em",
        value=member.created_at.strftime("%d/%m/%Y às %H:%M"),
        inline=True
    )
    
    # Verificar se joined_at existe
    if member.joined_at:
        embed.add_field(
            name="<:entrooumxp:1384773662250373120> Entrou em",
            value=member.joined_at.strftime("%d/%m/%Y às %H:%M"),
            inline=True
        )
    
    # Definir thumbnail com avatar do membro
    embed.set_thumbnail(url=member.display_avatar.url)
    
    # Adicionar footer
    embed.set_footer(
        text="Esta mensagem será deletada em 5 minutos",
        icon_url=bot.user.display_avatar.url
    )
    
    try:
        # Enviar mensagem
        message = await channel.send(embed=embed)
        print(f"✅ Mensagem de boas-vindas enviada para {member.display_name}")
        
        # Criar task para deletar mensagem após 5 minutos (não bloquear o evento)
        async def delete_after_delay():
            try:
                await asyncio.sleep(DELETE_AFTER)
                await message.delete()
                print(f"🗑️ Mensagem de boas-vindas de {member.display_name} foi deletada")
            except discord.NotFound:
                print(f"⚠️ Mensagem de {member.display_name} já foi deletada")
            except discord.HTTPException as e:
                print(f"❌ Erro ao deletar mensagem de {member.display_name}: {e}")
        
        # Executar em background
        asyncio.create_task(delete_after_delay())
        
    except discord.HTTPException as e:
        print(f"❌ Erro ao enviar mensagem: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

@bot.command(name='ping')
async def hacker_ping(ctx):
    """Comando de ping estilo hacker cyberpunk"""
    import time
    import random
    
    # Mensagem inicial de hack
    hack_msg = await ctx.send("```ansi\n[2;32m[INICIANDO PROTOCOLO DE PING...][0m```")
    
    await asyncio.sleep(1)
    
    # Simular processo de hack
    await hack_msg.edit(content="```ansi\n[2;32m[CONECTANDO AOS SERVIDORES...][0m\n[2;33m> Establishing secure connection...[0m```")
    
    await asyncio.sleep(1.5)
    
    # Calcular latência real
    start = time.perf_counter()
    await ctx.trigger_typing()
    end = time.perf_counter()
    latency = round((end - start) * 1000)
    bot_latency = round(bot.latency * 1000)
    
    # Dados fictícios para o efeito hacker
    server_data = [
        f"NODE-ALPHA: {random.randint(10, 50)}ms",
        f"NODE-BETA: {random.randint(15, 45)}ms", 
        f"NODE-GAMMA: {random.randint(20, 60)}ms",
        f"CORE-SERVER: {bot_latency}ms"
    ]
    
    # Mensagem final estilo cyberpunk
    embed = discord.Embed(
        title="⚡ NETWORK DIAGNOSTIC COMPLETE ⚡",
        color=0x00ff41  # Verde Matrix
    )
    
    embed.add_field(
        name="🔗 CONNECTION STATUS", 
        value="```ansi\n[2;32m● ONLINE - SECURE CHANNEL ESTABLISHED[0m```", 
        inline=False
    )
    
    embed.add_field(
        name="📡 SERVER NODES", 
        value=f"```ansi\n[2;36m{chr(10).join(server_data)}[0m```", 
        inline=True
    )
    
    embed.add_field(
        name="⚡ RESPONSE TIME", 
        value=f"```ansi\n[2;33mAPI: {latency}ms\nWS: {bot_latency}ms[0m```", 
        inline=True
    )
    
    embed.add_field(
        name="🛡️ SECURITY PROTOCOLS",
        value="```ansi\n[2;32m✓ TLS 1.3 ENCRYPTED\n✓ FIREWALL ACTIVE\n✓ DDOS PROTECTION ON[0m```",
        inline=False
    )
    
    # Status baseado na latência
    if bot_latency < 100:
        status = "[2;32m● OPTIMAL PERFORMANCE[0m"
        status_emoji = "🟢"
    elif bot_latency < 200:
        status = "[2;33m● MODERATE LATENCY[0m" 
        status_emoji = "🟡"
    else:
        status = "[2;31m● HIGH LATENCY DETECTED[0m"
        status_emoji = "🔴"
    
    embed.add_field(
        name=f"{status_emoji} NETWORK STATUS",
        value=f"```ansi\n{status}```",
        inline=False
    )
    
    embed.set_footer(
        text=f"⚡ MADRID MXP NETWORK DIAGNOSTIC v2.1 | Requested by {ctx.author.display_name}",
        icon_url=ctx.author.display_avatar.url
    )
    
    embed.timestamp = discord.utils.utcnow()
    
    await hack_msg.edit(content=None, embed=embed)

@bot.command(name='teste')
async def test_welcome(ctx):
    """Comando para testar a mensagem de boas-vindas"""
    if ctx.author.guild_permissions.administrator:
        await on_member_join(ctx.author)
        await ctx.send("✅ Teste de boas-vindas executado!", delete_after=5)
    else:
        await ctx.send("❌ Você precisa ser administrador para usar este comando!", delete_after=5)

@bot.command(name='status')
async def status_bot(ctx):
    """Comando simples para testar se o bot está respondendo"""
    await ctx.send("✅ Bot está online e funcionando!", delete_after=10)

@bot.command(name='debug')
async def debug_bot(ctx):
    """Comando para debug - verifica permissões e configurações"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Apenas administradores podem usar este comando!", delete_after=5)
        return
    
    # Verificar canal alvo
    target_channel = bot.get_channel(CHANNEL_ID)
    
    embed = discord.Embed(title="🔧 Debug do Bot", color=0xff9500)
    
    if target_channel:
        permissions = target_channel.permissions_for(ctx.guild.me)
        
        embed.add_field(
            name="📍 Canal Alvo",
            value=f"✅ {target_channel.mention} (ID: {CHANNEL_ID})",
            inline=False
        )
        
        # Verificar permissões
        perms_status = []
        perms_status.append(f"📝 Enviar mensagens: {'✅' if permissions.send_messages else '❌'}")
        perms_status.append(f"🔗 Enviar embeds: {'✅' if permissions.embed_links else '❌'}")
        perms_status.append(f"🗑️ Gerenciar mensagens: {'✅' if permissions.manage_messages else '❌'}")
        
        embed.add_field(
            name="🛡️ Permissões no Canal",
            value="\n".join(perms_status),
            inline=False
        )
    else:
        embed.add_field(
            name="📍 Canal Alvo",
            value=f"❌ Canal com ID {CHANNEL_ID} não encontrado!",
            inline=False
        )
        
        # Listar canais disponíveis
        channels_list = []
        for channel in ctx.guild.text_channels:
            channels_list.append(f"• {channel.name} (ID: {channel.id})")
        
        if channels_list:
            embed.add_field(
                name="📋 Canais Disponíveis",
                value="\n".join(channels_list[:10]),  # Mostrar apenas os primeiros 10
                inline=False
            )
    
    # Verificar intents
    embed.add_field(
        name="🔐 Intents",
        value=f"👥 Members: {'✅' if bot.intents.members else '❌'}\n"
              f"💬 Message Content: {'✅' if bot.intents.message_content else '❌'}",
        inline=False
    )
    
    # Info do servidor
    embed.add_field(
        name="📊 Servidor Info",
        value=f"👥 Membros: {ctx.guild.member_count}\n"
              f"🏷️ Nome: {ctx.guild.name}\n"
              f"🆔 ID: {ctx.guild.id}",
        inline=False
    )
    
    await ctx.send(embed=embed, delete_after=30)

@bot.event
async def on_command_error(ctx, error):
    """Tratamento de erros"""
    if isinstance(error, commands.CommandNotFound):
        return  # Ignorar comandos não encontrados
    
    print(f"❌ Erro no comando: {error}")

# Função principal
def main():
    load_dotenv()
    token = os.getenv('DISCORD_BOT_TOKEN')
    
    if not token:
        print("❌ Token do bot não encontrado!")
        print("🔑 Adicione seu token do Discord nas Secrets com a chave 'DISCORD_BOT_TOKEN'")
        return
    
    try:
        keep_alive()
        bot.run(token)
    except discord.LoginFailure:
        print("❌ Token inválido! Verifique se o token está correto.")
    except Exception as e:
        print(f"❌ Erro ao iniciar o bot: {e}")

if __name__ == "__main__":
    main()
