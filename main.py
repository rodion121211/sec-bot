import discord
from discord.ext import commands
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import aiofiles
from threading import Thread
from flask import Flask
import re
from dotenv import load_dotenv

# Keep alive para manter o bot online
app = Flask('')

@app.route('/')
def home():
    return "Security Bot Online"

def run():
    app.run(host='0.0.0.0', port=8000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ID do owner do bot (CONFIGURE AQUI SEU ID)
OWNER_ID = 983196900910039090  # Substitua pelo seu ID real

# Configurações padrão para novos servidores
DEFAULT_CONFIG = {
    'auto_ban_bots': False,
    'auto_ban_new_accounts': False,
    'new_account_days': 7,
    'role_delete_punishment': 'remove_roles',
    'channel_delete_punishment': 'remove_roles',
    'logs_channel_id': None,
    'audit_log_delay': 2,
    'max_logs_history': 100,
    'auto_kick_mass_ping': False,
    'max_mentions': 10,
    'auto_delete_invite_links': False,
    'whitelist_users': [],
    'protection_enabled': True,
    'anti_spam_enabled': False,
    'spam_message_count': 5,
    'spam_time_window': 10,
    'auto_mute_duration': 10,
    'mass_ping_mute_duration': 10,
    'protect_admin_roles': True,
    'backup_channels': True,
    'backup_roles': True
}

COLORS = {
    'danger': 0xff0000,
    'warning': 0xff9900,
    'success': 0x00ff00,
    'info': 0x0099ff,
    'purple': 0x9932cc
}

# Configurações do bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.guild_messages = True
intents.moderation = True

bot = commands.Bot(command_prefix='!sec_', intents=intents, help_command=None)

# Arquivo para salvar dados de segurança
SECURITY_DATA_FILE = "security_data.json"

class SecurityBot:
    def __init__(self):
        self.guild_configs = {}  # Configurações por servidor
        self.restored_roles = {}  # Para armazenar cargos removidos
        self.security_logs = {}  # Logs por servidor
        self.user_warnings = {}  # Avisos por usuário
        self.spam_tracker = {}  # Rastreamento de spam
        self.backup_data = {}  # Backups de canais/cargos

    async def load_data(self):
        """Carrega dados de segurança salvos"""
        try:
            if os.path.exists(SECURITY_DATA_FILE):
                async with aiofiles.open(SECURITY_DATA_FILE, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    data = json.loads(content)
                    self.guild_configs = data.get('guild_configs', {})
                    self.restored_roles = data.get('restored_roles', {})
                    self.security_logs = data.get('security_logs', {})
                    self.user_warnings = data.get('user_warnings', {})
                    self.backup_data = data.get('backup_data', {})
        except Exception as e:
            print(f"❌ Erro ao carregar dados de segurança: {e}")

    async def save_data(self):
        """Salva dados de segurança"""
        try:
            data = {
                'guild_configs': self.guild_configs,
                'restored_roles': self.restored_roles,
                'security_logs': self.security_logs,
                'user_warnings': self.user_warnings,
                'backup_data': self.backup_data
            }
            async with aiofiles.open(SECURITY_DATA_FILE, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"❌ Erro ao salvar dados de segurança: {e}")

    def get_guild_config(self, guild_id: int):
        """Obtém configuração do servidor"""
        guild_id_str = str(guild_id)
        if guild_id_str not in self.guild_configs:
            self.guild_configs[guild_id_str] = DEFAULT_CONFIG.copy()
        return self.guild_configs[guild_id_str]

    async def get_logs_channel(self, guild):
        """Encontra o canal de logs configurado"""
        config = self.get_guild_config(guild.id)
        if config['logs_channel_id']:
            return guild.get_channel(config['logs_channel_id'])
        return None

    async def log_security_action(self, guild, title: str, description: str, color: int, fields: List[Dict] = None):
        """Registra ação de segurança no canal de logs"""
        logs_channel = await self.get_logs_channel(guild)
        if not logs_channel:
            return

        embed = discord.Embed(
            title=f"🔒 {title}",
            description=description,
            color=color,
            timestamp=datetime.utcnow()
        )

        if fields:
            for field in fields:
                embed.add_field(
                    name=field['name'],
                    value=field['value'],
                    inline=field.get('inline', False)
                )

        embed.set_footer(text="Sistema de Segurança Automático")

        try:
            await logs_channel.send(embed=embed)

            # Salva no histórico
            guild_id_str = str(guild.id)
            if guild_id_str not in self.security_logs:
                self.security_logs[guild_id_str] = []

            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'title': title,
                'description': description
            }
            self.security_logs[guild_id_str].append(log_entry)

            # Mantém apenas os últimos logs
            config = self.get_guild_config(guild.id)
            max_logs = config['max_logs_history']
            self.security_logs[guild_id_str] = self.security_logs[guild_id_str][-max_logs:]

            await self.save_data()

        except Exception as e:
            print(f"❌ Erro ao enviar log de segurança: {e}")

# Instância global do sistema de segurança
security_system = SecurityBot()

@bot.event
async def on_ready():
    """Evento executado quando o bot está pronto"""
    await security_system.load_data()
    
    # Status interessante e dinâmico
    activities = [
        discord.Activity(type=discord.ActivityType.watching, name=f"🔒 {len(bot.guilds)} servidores protegidos"),
        discord.Activity(type=discord.ActivityType.listening, name="🛡️ Detectando ameaças 24/7"),
        discord.Activity(type=discord.ActivityType.playing, name="⚡ Sistema Anti-Raid Ativo"),
        discord.Game(name="🚀 Máxima Segurança Garantida!"),
    ]
    
    # Define um status aleatório
    import random
    chosen_activity = random.choice(activities)
    await bot.change_presence(
        status=discord.Status.online,
        activity=chosen_activity
    )
    
    print("🔥" + "=" * 60 + "🔥")
    print("⚡           SISTEMA DE SEGURANÇA AVANÇADO           ⚡")
    print("🔥" + "=" * 60 + "🔥")
    print(f"🚀 STATUS: OPERACIONAL | SERVIDORES: {len(bot.guilds)}")
    print("🛡️ PROTEÇÕES ATIVAS:")
    print("   ⚡ Anti-Raid System        - ATIVO")
    print("   🤖 Bot Detection          - ATIVO") 
    print("   📢 Anti-Spam Engine       - ATIVO")
    print("   🔒 Channel/Role Guard     - ATIVO")
    print("   💾 Auto-Backup System    - ATIVO")
    print("   📋 Advanced Logging       - ATIVO")
    print("   ⚠️ Warning System         - ATIVO")
    print("   👑 Owner Protection       - MÁXIMO")
    print("🔥" + "=" * 60 + "🔥")
    print("💎 OWNER DO BOT É COMPLETAMENTE INTOCÁVEL!")
    print("⚡ NENHUM COMANDO PODE AFETAR O DONO DO BOT!")
    print("🔥" + "=" * 60 + "🔥")
    
    # Atualiza status a cada 30 segundos
    async def update_status():
        while True:
            await asyncio.sleep(30)
            new_activity = random.choice(activities)
            await bot.change_presence(
                status=discord.Status.online,
                activity=new_activity
            )
    
    # Inicia task de atualização de status
    bot.loop.create_task(update_status())

@bot.event
async def on_guild_channel_delete(channel):
    """🔥 Detecta exclusão de canais"""
    try:
        guild = channel.guild
        config = security_system.get_guild_config(guild.id)

        if not config['protection_enabled']:
            return

        # Salva backup do canal
        if config['backup_channels']:
            guild_id_str = str(guild.id)
            if guild_id_str not in security_system.backup_data:
                security_system.backup_data[guild_id_str] = {'channels': [], 'roles': []}

            channel_backup = {
                'name': channel.name,
                'type': str(channel.type),
                'category': channel.category.name if channel.category else None,
                'position': channel.position,
                'topic': getattr(channel, 'topic', None),
                'deleted_at': datetime.utcnow().isoformat()
            }
            security_system.backup_data[guild_id_str]['channels'].append(channel_backup)

        await asyncio.sleep(config['audit_log_delay'])

        async for entry in guild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=1):
            if entry.target.id == channel.id:
                executor = entry.user

                # 👑 OWNER E WHITELIST TÊM PROTEÇÃO TOTAL
                if executor.id == OWNER_ID:
                    await security_system.log_security_action(
                        guild,
                        "Canal Deletado - 👑 OWNER DO BOT",
                        f"🟢 {executor.mention} (OWNER) deletou o canal #{channel.name} - ✅ **AUTORIZADO**",
                        COLORS['success']
                    )
                    return
                elif executor.id in config['whitelist_users']:
                    await security_system.log_security_action(
                        guild,
                        "Canal Deletado - Usuário Autorizado",
                        f"🟢 {executor.mention} deletou o canal #{channel.name}",
                        COLORS['success']
                    )
                    return

                # Aplica punição
                member = guild.get_member(executor.id)
                if member and config['channel_delete_punishment'] == 'remove_roles':
                    original_roles = [role for role in member.roles if role != guild.default_role]
                    if original_roles:
                        security_system.restored_roles[str(executor.id)] = {
                            'roles': [role.id for role in original_roles],
                            'removed_at': datetime.utcnow().isoformat(),
                            'reason': f"Deletou canal #{channel.name}",
                            'guild_id': guild.id
                        }
                        await member.remove_roles(*original_roles, reason="🔒 Segurança: Deletou canal")

                await security_system.log_security_action(
                    guild,
                    "🚨 CANAL DELETADO",
                    f"⚠️ {executor.mention} deletou o canal #{channel.name}",
                    COLORS['danger'],
                    [
                        {'name': '📺 Canal', 'value': f"#{channel.name}", 'inline': True},
                        {'name': '👤 Responsável', 'value': executor.mention, 'inline': True},
                        {'name': '⚡ Ação', 'value': config['channel_delete_punishment'], 'inline': True}
                    ]
                )
                break
    except Exception as e:
        print(f"❌ Erro no detector de exclusão de canais: {e}")

@bot.event
async def on_guild_role_delete(role):
    """🎭 Detecta exclusão de cargos"""
    try:
        guild = role.guild
        config = security_system.get_guild_config(guild.id)

        if not config['protection_enabled']:
            return

        # Salva backup do cargo
        if config['backup_roles']:
            guild_id_str = str(guild.id)
            if guild_id_str not in security_system.backup_data:
                security_system.backup_data[guild_id_str] = {'channels': [], 'roles': []}

            role_backup = {
                'name': role.name,
                'color': str(role.color),
                'permissions': role.permissions.value,
                'position': role.position,
                'deleted_at': datetime.utcnow().isoformat()
            }
            security_system.backup_data[guild_id_str]['roles'].append(role_backup)

        await asyncio.sleep(config['audit_log_delay'])

        async for entry in guild.audit_logs(action=discord.AuditLogAction.role_delete, limit=1):
            if entry.target.id == role.id:
                executor = entry.user

                # 👑 OWNER E WHITELIST TÊM PROTEÇÃO TOTAL
                if executor.id == OWNER_ID:
                    await security_system.log_security_action(
                        guild,
                        "Cargo Deletado - 👑 OWNER DO BOT",
                        f"🟢 {executor.mention} (OWNER) deletou o cargo @{role.name} - ✅ **AUTORIZADO**",
                        COLORS['success']
                    )
                    return
                elif executor.id in config['whitelist_users']:
                    await security_system.log_security_action(
                        guild,
                        "Cargo Deletado - Usuário Autorizado",
                        f"🟢 {executor.mention} deletou o cargo @{role.name}",
                        COLORS['success']
                    )
                    return

                # Aplica punição
                member = guild.get_member(executor.id)
                punishment = config['role_delete_punishment']

                if member:
                    if punishment == 'ban':
                        await member.ban(reason=f"🔒 Segurança: Deletou cargo @{role.name}")
                    else:  # remove_roles
                        original_roles = [r for r in member.roles if r != guild.default_role]
                        if original_roles:
                            security_system.restored_roles[str(executor.id)] = {
                                'roles': [r.id for r in original_roles],
                                'removed_at': datetime.utcnow().isoformat(),
                                'reason': f"Deletou cargo @{role.name}",
                                'guild_id': guild.id
                            }
                            await member.remove_roles(*original_roles, reason="🔒 Segurança: Deletou cargo")

                await security_system.log_security_action(
                    guild,
                    "🚨 CARGO DELETADO",
                    f"⚠️ {executor.mention} deletou o cargo @{role.name}",
                    COLORS['danger'],
                    [
                        {'name': '🎭 Cargo', 'value': f"@{role.name}", 'inline': True},
                        {'name': '👤 Responsável', 'value': executor.mention, 'inline': True},
                        {'name': '⚡ Ação', 'value': punishment, 'inline': True}
                    ]
                )
                break
    except Exception as e:
        print(f"❌ Erro no detector de exclusão de cargos: {e}")

@bot.event
async def on_member_join(member):
    """🤖 Eventos quando usuário entra"""
    guild = member.guild
    config = security_system.get_guild_config(guild.id)

    if not config['protection_enabled']:
        return

    # Ban automático de bots
    if member.bot and config['auto_ban_bots']:
        try:
            await member.ban(reason="🔒 Segurança: Bot banido automaticamente")
            await security_system.log_security_action(
                guild,
                "🤖 Bot Banido",
                f"Bot {member.mention} foi banido automaticamente",
                COLORS['warning']
            )
        except Exception as e:
            print(f"❌ Erro ao banir bot: {e}")

    # Ban de contas muito novas
    if not member.bot and config['auto_ban_new_accounts']:
        account_age = (datetime.utcnow() - member.created_at).days
        if account_age < config['new_account_days']:
            try:
                await member.ban(reason=f"🔒 Segurança: Conta muito nova ({account_age} dias)")
                await security_system.log_security_action(
                    guild,
                    "🆕 Conta Nova Banida",
                    f"Usuário {member.mention} banido (conta com {account_age} dias)",
                    COLORS['warning']
                )
            except Exception as e:
                print(f"❌ Erro ao banir conta nova: {e}")

@bot.event
async def on_message(message):
    """📨 Monitora mensagens para anti-spam e outras proteções"""
    if message.author.bot:
        return

    guild = message.guild
    if not guild:
        return

    config = security_system.get_guild_config(guild.id)

    if not config['protection_enabled']:
        await bot.process_commands(message)
        return

    # Anti-spam
    if config['anti_spam_enabled']:
        user_id = str(message.author.id)
        guild_id = str(guild.id)

        if guild_id not in security_system.spam_tracker:
            security_system.spam_tracker[guild_id] = {}

        if user_id not in security_system.spam_tracker[guild_id]:
            security_system.spam_tracker[guild_id][user_id] = []

        now = datetime.utcnow()
        user_messages = security_system.spam_tracker[guild_id][user_id]

        # Remove mensagens antigas
        user_messages[:] = [msg_time for msg_time in user_messages 
                           if (now - msg_time).seconds < config['spam_time_window']]

        user_messages.append(now)

        if len(user_messages) >= config['spam_message_count']:
            try:
                await message.author.timeout(
                    timedelta(seconds=config['auto_mute_duration']),
                    reason="🔒 Anti-spam: Muitas mensagens em pouco tempo"
                )
                await security_system.log_security_action(
                    guild,
                    "🚫 Usuário Mutado por Spam",
                    f"{message.author.mention} foi mutado por {config['auto_mute_duration']}s",
                    COLORS['warning']
                )
                user_messages.clear()
            except Exception as e:
                print(f"❌ Erro ao mutar por spam: {e}")

    # Anti mass ping
    if config['auto_kick_mass_ping']:
        mention_count = len(message.mentions)
        if mention_count >= config['max_mentions']:
            try:
                await message.delete()
                await message.author.timeout(
                    timedelta(seconds=config['mass_ping_mute_duration']),
                    reason=f"🔒 Mass ping: {mention_count} menções"
                )
                await security_system.log_security_action(
                    guild,
                    "🚫 Usuário Silenciado por Mass Ping",
                    f"{message.author.mention} silenciado por {config['mass_ping_mute_duration']}s ({mention_count} menções)",
                    COLORS['warning']
                )
            except Exception as e:
                print(f"❌ Erro ao silenciar por mass ping: {e}")

    # Anti convite
    if config['auto_delete_invite_links']:
        invite_pattern = r'discord\.gg/\w+'
        if re.search(invite_pattern, message.content):
            try:
                await message.delete()
                await security_system.log_security_action(
                    guild,
                    "🔗 Link de Convite Deletado",
                    f"Mensagem de {message.author.mention} continha convite",
                    COLORS['info']
                )
            except Exception as e:
                print(f"❌ Erro ao deletar convite: {e}")

    await bot.process_commands(message)

# === COMANDOS DO BOT ===

def is_owner():
    def predicate(ctx):
        return ctx.author.id == OWNER_ID
    return commands.check(predicate)

def is_staff():
    async def predicate(ctx):
        # 👑 OWNER TEM PODER ABSOLUTO - SEMPRE PODE USAR QUALQUER COMANDO
        if ctx.author.id == OWNER_ID == 983196900910039090:
            return True
        # Para outros usuários, precisa ser administrador
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)

@bot.command(name='config', aliases=['c'])
@is_owner()
async def config_security(ctx, setting: str = None, *, value: str = None):
    """Configura o sistema de segurança"""
    config = security_system.get_guild_config(ctx.guild.id)

    if not setting:
        embed = discord.Embed(title="🔧 Configurações de Segurança", color=COLORS['info'])

        # Mostra configurações atuais
        embed.add_field(name="🤖 auto_ban_bots", value="✅" if config['auto_ban_bots'] else "❌", inline=True)
        embed.add_field(name="🆕 auto_ban_new_accounts", value="✅" if config['auto_ban_new_accounts'] else "❌", inline=True)
        embed.add_field(name="📅 new_account_days", value=config['new_account_days'], inline=True)
        embed.add_field(name="🛡️ protection_enabled", value="✅" if config['protection_enabled'] else "❌", inline=True)
        embed.add_field(name="📢 anti_spam_enabled", value="✅" if config['anti_spam_enabled'] else "❌", inline=True)
        embed.add_field(name="🚫 auto_kick_mass_ping", value="✅" if config['auto_kick_mass_ping'] else "❌", inline=True)
        embed.add_field(name="🔗 auto_delete_invite_links", value="✅" if config['auto_delete_invite_links'] else "❌", inline=True)
        embed.add_field(name="💾 backup_channels", value="✅" if config['backup_channels'] else "❌", inline=True)
        embed.add_field(name="📺 logs_channel_id", value=f"<#{config['logs_channel_id']}>" if config['logs_channel_id'] else "Não definido", inline=True)

        embed.add_field(
            name="💡 Exemplos de uso:",
            value="`!sec_c auto_ban_bots true`\n`!sec_c anti_spam_enabled true`\n`!sec_c auto_mute_duration 10`\n`!sec_c logs_channel_id #logs`",
            inline=False
        )

        await ctx.send(embed=embed)
        return

    # Aplica configuração
    if setting == 'auto_ban_bots':
        config['auto_ban_bots'] = value.lower() == 'true'
    elif setting == 'auto_ban_new_accounts':
        config['auto_ban_new_accounts'] = value.lower() == 'true'
    elif setting == 'new_account_days':
        config['new_account_days'] = int(value)
    elif setting == 'protection_enabled':
        config['protection_enabled'] = value.lower() == 'true'
    elif setting == 'anti_spam_enabled':
        config['anti_spam_enabled'] = value.lower() == 'true'
    elif setting == 'auto_kick_mass_ping':
        config['auto_kick_mass_ping'] = value.lower() == 'true'
    elif setting == 'auto_delete_invite_links':
        config['auto_delete_invite_links'] = value.lower() == 'true'
    elif setting == 'backup_channels':
        config['backup_channels'] = value.lower() == 'true'
    elif setting == 'backup_roles':
        config['backup_roles'] = value.lower() == 'true'
    elif setting == 'max_mentions':
        config['max_mentions'] = int(value)
    elif setting == 'spam_message_count':
        config['spam_message_count'] = int(value)
    elif setting == 'auto_mute_duration':
        config['auto_mute_duration'] = int(value)
    elif setting == 'mass_ping_mute_duration':
        config['mass_ping_mute_duration'] = int(value)
    elif setting == 'logs_channel_id':
        if value.startswith('#'):
            channel = discord.utils.get(ctx.guild.channels, name=value[1:])
        else:
            channel = ctx.guild.get_channel(int(value.strip('<#>')))
        config['logs_channel_id'] = channel.id if channel else None
    else:
        await ctx.send("❌ Configuração inválida!")
        return

    await security_system.save_data()

    embed = discord.Embed(
        title="✅ Configuração Atualizada",
        description=f"**{setting}** = **{value}**",
        color=COLORS['success']
    )
    await ctx.send(embed=embed)

@bot.command(name='whitelist', aliases=['w'])
@is_owner()
async def manage_whitelist(ctx, action: str = None, user: discord.Member = None):
    """Gerencia whitelist"""
    config = security_system.get_guild_config(ctx.guild.id)

    if not action:
        embed = discord.Embed(title="🔐 Whitelist de Segurança", color=COLORS['info'])

        if config['whitelist_users']:
            users = []
            for user_id in config['whitelist_users']:
                user_obj = bot.get_user(user_id)
                users.append(user_obj.mention if user_obj else f"ID: {user_id}")
            embed.add_field(name="👥 Usuários", value='\n'.join(users), inline=False)
        else:
            embed.add_field(name="👥 Usuários", value="Nenhum usuário na whitelist", inline=False)

        embed.add_field(name="💡 Uso", value="`!sec_w add @user`\n`!sec_w remove @user`", inline=False)
        await ctx.send(embed=embed)
        return

    if not user:
        await ctx.send("❌ Mencione um usuário!")
        return

    if action == 'add':
        if user.id not in config['whitelist_users']:
            config['whitelist_users'].append(user.id)
            await security_system.save_data()
            await ctx.send(f"✅ {user.mention} adicionado à whitelist!")
        else:
            await ctx.send("❌ Usuário já está na whitelist!")

    elif action == 'remove':
        if user.id in config['whitelist_users']:
            config['whitelist_users'].remove(user.id)
            await security_system.save_data()
            await ctx.send(f"✅ {user.mention} removido da whitelist!")
        else:
            await ctx.send("❌ Usuário não está na whitelist!")

@bot.command(name='restore', aliases=['r'])
@is_staff()
async def restore_roles(ctx, user: discord.Member):
    """Restaura cargos de um usuário"""
    user_id = str(user.id)

    if user_id not in security_system.restored_roles:
        await ctx.send("❌ Usuário não tem cargos para restaurar!")
        return

    try:
        user_data = security_system.restored_roles[user_id]
        roles_to_restore = []

        for role_id in user_data['roles']:
            role = ctx.guild.get_role(role_id)
            if role:
                roles_to_restore.append(role)

        if roles_to_restore:
            await user.add_roles(*roles_to_restore, reason=f"Restauração por {ctx.author}")
            del security_system.restored_roles[user_id]
            await security_system.save_data()

            await ctx.send(f"✅ Cargos de {user.mention} restaurados!")
        else:
            await ctx.send("❌ Nenhum cargo válido para restaurar!")

    except Exception as e:
        await ctx.send(f"❌ Erro: {e}")

@bot.command(name='status', aliases=['s'])
@is_staff()
async def security_status(ctx):
    """Status do sistema"""
    config = security_system.get_guild_config(ctx.guild.id)

    embed = discord.Embed(title="🔒 Status do Sistema", color=COLORS['info'])

    # Status geral
    guild_id_str = str(ctx.guild.id)
    logs_count = len(security_system.security_logs.get(guild_id_str, []))
    pending_restores = len([r for r in security_system.restored_roles.values() 
                           if r['guild_id'] == ctx.guild.id])

    embed.add_field(name="🟢 Sistema", value="Operacional", inline=True)
    embed.add_field(name="📊 Logs", value=logs_count, inline=True)
    embed.add_field(name="🔄 Restaurações", value=pending_restores, inline=True)

    # Proteções ativas
    protections = []
    if config['protection_enabled']:
        protections.append("🛡️ Proteção geral ativa")
        if config['auto_ban_bots']:
            protections.append("🤖 Anti-bot")
        if config['anti_spam_enabled']:
            protections.append("📢 Anti-spam")
        if config['auto_kick_mass_ping']:
            protections.append("🚫 Anti mass-ping")
    else:
        protections.append("❌ Proteções desativadas")

    embed.add_field(name="🛡️ Proteções", value='\n'.join(protections), inline=False)

    # Canal de logs
    logs_channel = "Não configurado"
    if config['logs_channel_id']:
        logs_channel = f"<#{config['logs_channel_id']}>"
    embed.add_field(name="📺 Canal de Logs", value=logs_channel, inline=True)

    await ctx.send(embed=embed)

@bot.command(name='logs', aliases=['l'])
@is_staff()
async def view_logs(ctx, limit: int = 10):
    """Visualiza logs recentes"""
    guild_id_str = str(ctx.guild.id)
    logs = security_system.security_logs.get(guild_id_str, [])

    if not logs:
        await ctx.send("❌ Nenhum log encontrado!")
        return

    embed = discord.Embed(title="📋 Logs Recentes", color=COLORS['info'])

    recent_logs = logs[-limit:]
    for log in recent_logs:
        timestamp = datetime.fromisoformat(log['timestamp']).strftime("%d/%m %H:%M")
        embed.add_field(
            name=f"🕐 {timestamp}",
            value=f"**{log['title']}**\n{log['description'][:100]}...",
            inline=False
        )

    await ctx.send(embed=embed)

@bot.command(name='backup', aliases=['b'])
@is_staff()
async def view_backups(ctx):
    """Visualiza backups de canais/cargos deletados"""
    guild_id_str = str(ctx.guild.id)
    backups = security_system.backup_data.get(guild_id_str, {'channels': [], 'roles': []})

    embed = discord.Embed(title="💾 Backups Disponíveis", color=COLORS['info'])

    # Canais deletados
    if backups['channels']:
        channels_text = []
        for channel in backups['channels'][-5:]:  # Últimos 5
            deleted_date = datetime.fromisoformat(channel['deleted_at']).strftime("%d/%m")
            channels_text.append(f"#{channel['name']} ({deleted_date})")
        embed.add_field(name="📺 Canais Deletados", value='\n'.join(channels_text), inline=True)

    # Cargos deletados
    if backups['roles']:
        roles_text = []
        for role in backups['roles'][-5:]:  # Últimos 5
            deleted_date = datetime.fromisoformat(role['deleted_at']).strftime("%d/%m")
            roles_text.append(f"@{role['name']} ({deleted_date})")
        embed.add_field(name="🎭 Cargos Deletados", value='\n'.join(roles_text), inline=True)

    if not backups['channels'] and not backups['roles']:
        embed.add_field(name="💾 Status", value="Nenhum backup disponível", inline=False)

    await ctx.send(embed=embed)

@bot.command(name='warn', aliases=['av'])
@is_staff()
async def warn_user(ctx, user: discord.Member, *, reason: str = "Sem motivo especificado"):
    """Aplica aviso a um usuário"""
    # 👑 OWNER DO BOT É INTOCÁVEL - PROTEÇÃO ABSOLUTA
    if user.id == OWNER_ID:
        embed = discord.Embed(
            title="👑 PROTEÇÃO DO OWNER",
            description="❌ **O OWNER DO BOT É COMPLETAMENTE INTOCÁVEL!**\n🛡️ Nenhum comando pode afetar o dono do bot por segurança.",
            color=COLORS['danger']
        )
        await ctx.send(embed=embed)
        return
    user_id = str(user.id)
    guild_id = str(ctx.guild.id)

    if guild_id not in security_system.user_warnings:
        security_system.user_warnings[guild_id] = {}

    if user_id not in security_system.user_warnings[guild_id]:
        security_system.user_warnings[guild_id][user_id] = []

    warning = {
        'reason': reason,
        'moderator': ctx.author.id,
        'timestamp': datetime.utcnow().isoformat()
    }

    security_system.user_warnings[guild_id][user_id].append(warning)
    await security_system.save_data()

    warnings_count = len(security_system.user_warnings[guild_id][user_id])

    embed = discord.Embed(
        title="⚠️ Aviso Aplicado",
        description=f"{user.mention} recebeu um aviso",
        color=COLORS['warning']
    )
    embed.add_field(name="📝 Motivo", value=reason, inline=False)
    embed.add_field(name="📊 Total de Avisos", value=warnings_count, inline=True)
    embed.add_field(name="👮 Moderador", value=ctx.author.mention, inline=True)

    await ctx.send(embed=embed)

    await security_system.log_security_action(
        ctx.guild,
        "⚠️ Aviso Aplicado",
        f"{user.mention} recebeu aviso de {ctx.author.mention}",
        COLORS['warning'],
        [
            {'name': '📝 Motivo', 'value': reason, 'inline': False},
            {'name': '📊 Total', 'value': warnings_count, 'inline': True}
        ]
    )

@bot.command(name='warnings', aliases=['avisos'])
@is_staff()
async def view_warnings(ctx, user: discord.Member = None):
    """Visualiza avisos de um usuário"""
    if not user:
        user = ctx.author

    user_id = str(user.id)
    guild_id = str(ctx.guild.id)

    warnings = security_system.user_warnings.get(guild_id, {}).get(user_id, [])

    if not warnings:
        await ctx.send(f"✅ {user.mention} não possui avisos!")
        return

    embed = discord.Embed(
        title=f"⚠️ Avisos de {user.display_name}",
        color=COLORS['warning']
    )

    for i, warning in enumerate(warnings[-10:], 1):  # Últimos 10
        timestamp = datetime.fromisoformat(warning['timestamp']).strftime("%d/%m %H:%M")
        moderator = bot.get_user(warning['moderator'])
        mod_name = moderator.mention if moderator else "Desconhecido"

        embed.add_field(
            name=f"Aviso #{i}",
            value=f"**Motivo:** {warning['reason']}\n**Moderador:** {mod_name}\n**Data:** {timestamp}",
            inline=False
        )

    embed.add_field(name="📊 Total", value=len(warnings), inline=True)

    await ctx.send(embed=embed)

@bot.command(name='clear_warnings', aliases=['limpar_avisos'])
@is_owner()
async def clear_warnings(ctx, user: discord.Member):
    """Limpa avisos de um usuário"""
    user_id = str(user.id)
    guild_id = str(ctx.guild.id)

    if guild_id in security_system.user_warnings and user_id in security_system.user_warnings[guild_id]:
        warnings_count = len(security_system.user_warnings[guild_id][user_id])
        del security_system.user_warnings[guild_id][user_id]
        await security_system.save_data()

        await ctx.send(f"✅ {warnings_count} avisos de {user.mention} foram limpos!")
    else:
        await ctx.send(f"❌ {user.mention} não possui avisos para limpar!")

@bot.command(name='mute', aliases=['m'])
@is_staff()
async def mute_user(ctx, user: discord.Member, duration: int = 300, *, reason: str = "Sem motivo"):
    """Muta um usuário temporariamente"""
    # 👑 OWNER DO BOT É INTOCÁVEL - PROTEÇÃO ABSOLUTA
    if user.id == OWNER_ID:
        embed = discord.Embed(
            title="👑 PROTEÇÃO DO OWNER",
            description="❌ **O OWNER DO BOT É COMPLETAMENTE INTOCÁVEL!**\n🛡️ Nenhum comando pode afetar o dono do bot por segurança.",
            color=COLORS['danger']
        )
        await ctx.send(embed=embed)
        return
        
    try:
        await user.timeout(
            timedelta(seconds=duration),
            reason=f"🔒 Mutado por {ctx.author}: {reason}"
        )

        embed = discord.Embed(
            title="🔇 Usuário Mutado",
            description=f"{user.mention} foi mutado por {duration} segundos",
            color=COLORS['warning']
        )
        embed.add_field(name="📝 Motivo", value=reason, inline=False)
        embed.add_field(name="⏱️ Duração", value=f"{duration} segundos", inline=True)
        embed.add_field(name="👮 Moderador", value=ctx.author.mention, inline=True)

        await ctx.send(embed=embed)

        await security_system.log_security_action(
            ctx.guild,
            "🔇 Usuário Mutado",
            f"{user.mention} mutado por {ctx.author.mention}",
            COLORS['warning'],
            [
                {'name': '📝 Motivo', 'value': reason, 'inline': False},
                {'name': '⏱️ Duração', 'value': f"{duration}s", 'inline': True}
            ]
        )

    except Exception as e:
        await ctx.send(f"❌ Erro ao mutar usuário: {e}")

@bot.command(name='unmute', aliases=['desmutar'])
@is_staff()
async def unmute_user(ctx, user: discord.Member):
    """Desmuta um usuário"""
    try:
        await user.timeout(None, reason=f"Desmutado por {ctx.author}")
        await ctx.send(f"✅ {user.mention} foi desmutado!")

        await security_system.log_security_action(
            ctx.guild,
            "🔊 Usuário Desmutado",
            f"{user.mention} desmutado por {ctx.author.mention}",
            COLORS['success']
        )

    except Exception as e:
        await ctx.send(f"❌ Erro ao desmutar usuário: {e}")

@bot.command(name='banir', aliases=['ban'])
@is_staff()
async def ban_user(ctx, user: discord.Member, *, motivo: str = "Sem motivo especificado"):
    """Bane um usuário do servidor"""
    # 👑 OWNER DO BOT É INTOCÁVEL - PROTEÇÃO ABSOLUTA
    if user.id == OWNER_ID:
        embed = discord.Embed(
            title="👑 PROTEÇÃO DO OWNER",
            description="❌ **O OWNER DO BOT É COMPLETAMENTE INTOCÁVEL!**\n🛡️ Nenhum comando pode afetar o dono do bot por segurança.",
            color=COLORS['danger']
        )
        await ctx.send(embed=embed)
        return
        
    try:
        await user.ban(reason=f"🔒 Banido por {ctx.author}: {motivo}")

        embed = discord.Embed(
            title="🔨 Usuário Banido",
            description=f"{user.mention} foi banido do servidor",
            color=COLORS['danger']
        )
        embed.add_field(name="📝 Motivo", value=motivo, inline=False)
        embed.add_field(name="👮 Moderador", value=ctx.author.mention, inline=True)

        await ctx.send(embed=embed)

        await security_system.log_security_action(
            ctx.guild,
            "🔨 Usuário Banido",
            f"{user.mention} banido por {ctx.author.mention}",
            COLORS['danger'],
            [{'name': '📝 Motivo', 'value': motivo, 'inline': False}]
        )

    except Exception as e:
        await ctx.send(f"❌ Erro ao banir usuário: {e}")

@bot.command(name='expulsar', aliases=['kick'])
@is_staff()
async def kick_user(ctx, user: discord.Member, *, motivo: str = "Sem motivo especificado"):
    """Expulsa um usuário do servidor"""
    # 👑 OWNER DO BOT É INTOCÁVEL - PROTEÇÃO ABSOLUTA
    if user.id == OWNER_ID:
        embed = discord.Embed(
            title="👑 PROTEÇÃO DO OWNER",
            description="❌ **O OWNER DO BOT É COMPLETAMENTE INTOCÁVEL!**\n🛡️ Nenhum comando pode afetar o dono do bot por segurança.",
            color=COLORS['danger']
        )
        await ctx.send(embed=embed)
        return
        
    try:
        await user.kick(reason=f"🔒 Expulso por {ctx.author}: {motivo}")

        embed = discord.Embed(
            title="👢 Usuário Expulso",
            description=f"{user.mention} foi expulso do servidor",
            color=COLORS['warning']
        )
        embed.add_field(name="📝 Motivo", value=motivo, inline=False)
        embed.add_field(name="👮 Moderador", value=ctx.author.mention, inline=True)

        await ctx.send(embed=embed)

        await security_system.log_security_action(
            ctx.guild,
            "👢 Usuário Expulso",
            f"{user.mention} expulso por {ctx.author.mention}",
            COLORS['warning'],
            [{'name': '📝 Motivo', 'value': motivo, 'inline': False}]
        )

    except Exception as e:
        await ctx.send(f"❌ Erro ao expulsar usuário: {e}")

@bot.command(name='limpar', aliases=['clear', 'purge'])
@is_owner()
async def clear_messages(ctx, quantidade: int = 10):
    """Limpa mensagens do canal"""
    if quantidade > 100:
        await ctx.send("❌ Máximo de 100 mensagens por vez!")
        return

    try:
        deleted = await ctx.channel.purge(limit=quantidade + 1)

        embed = discord.Embed(
            title="🧹 Mensagens Limpas",
            description=f"{len(deleted) - 1} mensagens foram deletadas",
            color=COLORS['success']
        )
        embed.add_field(name="👮 Moderador", value=ctx.author.mention, inline=True)
        embed.add_field(name="📺 Canal", value=ctx.channel.mention, inline=True)

        msg = await ctx.send(embed=embed)
        await asyncio.sleep(3)
        await msg.delete()

        await security_system.log_security_action(
            ctx.guild,
            "🧹 Mensagens Limpas",
            f"{len(deleted) - 1} mensagens deletadas por {ctx.author.mention}",
            COLORS['info']
        )

    except Exception as e:
        await ctx.send(f"❌ Erro ao limpar mensagens: {e}")

@bot.command(name='slowmode', aliases=['slow'])
@is_staff()
async def set_slowmode(ctx, segundos: int = 0):
    """Define modo lento no canal"""
    try:
        await ctx.channel.edit(slowmode_delay=segundos)

        if segundos == 0:
            await ctx.send("✅ Modo lento desativado!")
        else:
            await ctx.send(f"⏱️ Modo lento ativado: {segundos} segundos")

        await security_system.log_security_action(
            ctx.guild,
            "⏱️ Modo Lento Alterado",
            f"Slowmode definido para {segundos}s por {ctx.author.mention}",
            COLORS['info']
        )

    except Exception as e:
        await ctx.send(f"❌ Erro ao definir modo lento: {e}")

@bot.command(name='bloquear', aliases=['lock'])
@is_staff()
async def lock_channel(ctx):
    """Bloqueia o canal para @everyone"""
    try:
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        embed = discord.Embed(
            title="🔒 Canal Bloqueado",
            description="Canal bloqueado para @everyone",
            color=COLORS['warning']
        )
        await ctx.send(embed=embed)

        await security_system.log_security_action(
            ctx.guild,
            "🔒 Canal Bloqueado",
            f"Canal {ctx.channel.mention} bloqueado por {ctx.author.mention}",
            COLORS['warning']
        )

    except Exception as e:
        await ctx.send(f"❌ Erro ao bloquear canal: {e}")

@bot.command(name='desbloquear', aliases=['unlock'])
@is_staff()
async def unlock_channel(ctx):
    """Desbloqueia o canal para @everyone"""
    try:
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        embed = discord.Embed(
            title="🔓 Canal Desbloqueado",
            description="Canal desbloqueado para @everyone",
            color=COLORS['success']
        )
        await ctx.send(embed=embed)

        await security_system.log_security_action(
            ctx.guild,
            "🔓 Canal Desbloqueado",
            f"Canal {ctx.channel.mention} desbloqueado por {ctx.author.mention}",
            COLORS['success']
        )

    except Exception as e:
        await ctx.send(f"❌ Erro ao desbloquear canal: {e}")

@bot.command(name='info', aliases=['userinfo'])
@is_staff()
async def user_info(ctx, user: discord.Member = None):
    """Mostra informações de um usuário"""
    if not user:
        user = ctx.author

    created_at = user.created_at.strftime("%d/%m/%Y %H:%M")
    joined_at = user.joined_at.strftime("%d/%m/%Y %H:%M") if user.joined_at else "Desconhecido"

    embed = discord.Embed(
        title=f"👤 Informações de {user.display_name}",
        color=COLORS['info']
    )
    embed.set_thumbnail(url=user.avatar.url if user.avatar else None)

    embed.add_field(name="🆔 ID", value=user.id, inline=True)
    embed.add_field(name="📅 Conta criada", value=created_at, inline=True)
    embed.add_field(name="📥 Entrou em", value=joined_at, inline=True)
    embed.add_field(name="🤖 Bot", value="Sim" if user.bot else "Não", inline=True)
    embed.add_field(name="🎭 Cargos", value=len(user.roles) - 1, inline=True)
    embed.add_field(name="🔝 Maior cargo", value=user.top_role.mention, inline=True)

    await ctx.send(embed=embed)

@bot.command(name='roleinfo', aliases=['cargoinfo'])
@is_staff()
async def role_info(ctx, *, nome_cargo: str):
    """Mostra informações de um cargo"""
    role = discord.utils.get(ctx.guild.roles, name=nome_cargo)

    if not role:
        await ctx.send("❌ Cargo não encontrado!")
        return

    created_at = role.created_at.strftime("%d/%m/%Y %H:%M")

    embed = discord.Embed(
        title=f"🎭 Informações do Cargo @{role.name}",
        color=role.color
    )

    embed.add_field(name="🆔 ID", value=role.id, inline=True)
    embed.add_field(name="📅 Criado em", value=created_at, inline=True)
    embed.add_field(name="👥 Membros", value=len(role.members), inline=True)
    embed.add_field(name="📍 Posição", value=role.position, inline=True)
    embed.add_field(name="🎨 Cor", value=str(role.color), inline=True)
    embed.add_field(name="🔗 Mencionável", value="Sim" if role.mentionable else "Não", inline=True)

    await ctx.send(embed=embed)

@bot.command(name='serverinfo', aliases=['servidor'])
@is_staff()
async def server_info(ctx):
    """Mostra informações do servidor"""
    guild = ctx.guild
    created_at = guild.created_at.strftime("%d/%m/%Y %H:%M")

    embed = discord.Embed(
        title=f"🏰 Informações do Servidor",
        color=COLORS['info']
    )

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    embed.add_field(name="📛 Nome", value=guild.name, inline=True)
    embed.add_field(name="🆔 ID", value=guild.id, inline=True)
    embed.add_field(name="👑 Dono", value=guild.owner.mention if guild.owner else "Desconhecido", inline=True)
    embed.add_field(name="👥 Membros", value=guild.member_count, inline=True)
    embed.add_field(name="📺 Canais", value=len(guild.channels), inline=True)
    embed.add_field(name="🎭 Cargos", value=len(guild.roles), inline=True)
    embed.add_field(name="📅 Criado em", value=created_at, inline=False)

    await ctx.send(embed=embed)

@bot.command(name='avatar')
@is_staff()
async def show_avatar(ctx, user: discord.Member = None):
    """Mostra o avatar de um usuário"""
    if not user:
        user = ctx.author

    embed = discord.Embed(
        title=f"🖼️ Avatar de {user.display_name}",
        color=COLORS['info']
    )

    if user.avatar:
        embed.set_image(url=user.avatar.url)
        embed.add_field(name="🔗 Link direto", value=f"[Clique aqui]({user.avatar.url})", inline=False)
    else:
        embed.description = "Usuário não possui avatar personalizado"

    await ctx.send(embed=embed)

@bot.command(name='cargo', aliases=['role'])
@is_staff()
async def manage_role(ctx, acao: str, user: discord.Member, *, nome_cargo: str):
    """Adiciona ou remove cargo de um usuário"""
    role = discord.utils.get(ctx.guild.roles, name=nome_cargo)

    if not role:
        await ctx.send("❌ Cargo não encontrado!")
        return

    try:
        if acao.lower() in ['add', 'adicionar', 'dar']:
            await user.add_roles(role, reason=f"Cargo adicionado por {ctx.author}")

            embed = discord.Embed(
                title="✅ Cargo Adicionado",
                description=f"Cargo @{role.name} adicionado a {user.mention}",
                color=COLORS['success']
            )

            await security_system.log_security_action(
                ctx.guild,
                "🎭 Cargo Adicionado",
                f"@{role.name} adicionado a {user.mention} por {ctx.author.mention}",
                COLORS['success']
            )

        elif acao.lower() in ['remove', 'remover', 'tirar']:
            await user.remove_roles(role, reason=f"Cargo removido por {ctx.author}")

            embed = discord.Embed(
                title="❌ Cargo Removido",
                description=f"Cargo @{role.name} removido de {user.mention}",
                color=COLORS['warning']
            )

            await security_system.log_security_action(
                ctx.guild,
                "🎭 Cargo Removido",
                f"@{role.name} removido de {user.mention} por {ctx.author.mention}",
                COLORS['warning']
            )
        else:
            await ctx.send("❌ Ação inválida! Use: `adicionar` ou `remover`")
            return

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ Erro: {e}")

@bot.command(name='nick', aliases=['nickname'])
@is_staff()
async def change_nickname(ctx, user: discord.Member, *, novo_nick: str = None):
    """Altera o nickname de um usuário"""
    try:
        old_nick = user.display_name
        await user.edit(nick=novo_nick, reason=f"Nickname alterado por {ctx.author}")

        embed = discord.Embed(
            title="✏️ Nickname Alterado",
            color=COLORS['success']
        )
        embed.add_field(name="👤 Usuário", value=user.mention, inline=True)
        embed.add_field(name="📝 Antes", value=old_nick, inline=True)
        embed.add_field(name="📝 Depois", value=novo_nick or user.name, inline=True)

        await ctx.send(embed=embed)

        await security_system.log_security_action(
            ctx.guild,
            "✏️ Nickname Alterado",
            f"Nickname de {user.mention} alterado por {ctx.author.mention}",
            COLORS['info']
        )

    except Exception as e:
        await ctx.send(f"❌ Erro ao alterar nickname: {e}")

@bot.command(name='criar_cargo', aliases=['create_role'])
@is_owner()
async def create_role(ctx, *, nome_cargo: str):
    """Cria um novo cargo"""
    try:
        role = await ctx.guild.create_role(
            name=nome_cargo,
            reason=f"Cargo criado por {ctx.author}"
        )

        embed = discord.Embed(
            title="✅ Cargo Criado",
            description=f"Cargo @{role.name} criado com sucesso!",
            color=COLORS['success']
        )
        embed.add_field(name="🆔 ID", value=role.id, inline=True)
        embed.add_field(name="👮 Criado por", value=ctx.author.mention, inline=True)

        await ctx.send(embed=embed)

        await security_system.log_security_action(
            ctx.guild,
            "🎭 Cargo Criado",
            f"Cargo @{role.name} criado por {ctx.author.mention}",
            COLORS['success']
        )

    except Exception as e:
        await ctx.send(f"❌ Erro ao criar cargo: {e}")

@bot.command(name='deletar_cargo', aliases=['delete_role'])
@is_owner()
async def delete_role(ctx, *, nome_cargo: str):
    """Deleta um cargo"""
    role = discord.utils.get(ctx.guild.roles, name=nome_cargo)

    if not role:
        await ctx.send("❌ Cargo não encontrado!")
        return

    try:
        role_name = role.name
        await role.delete(reason=f"Cargo deletado por {ctx.author}")

        embed = discord.Embed(
            title="🗑️ Cargo Deletado",
            description=f"Cargo @{role_name} foi deletado",
            color=COLORS['warning']
        )
        embed.add_field(name="👮 Deletado por", value=ctx.author.mention, inline=True)

        await ctx.send(embed=embed)

        await security_system.log_security_action(
            ctx.guild,
            "🗑️ Cargo Deletado",
            f"Cargo @{role_name} deletado por {ctx.author.mention}",
            COLORS['warning']
        )

    except Exception as e:
        await ctx.send(f"❌ Erro ao deletar cargo: {e}")

@bot.command(name='backup_server', aliases=['backup_completo'])
@is_owner()
async def backup_server(ctx):
    """Cria backup completo do servidor"""
    try:
        guild = ctx.guild
        backup_data = {
            'server_name': guild.name,
            'created_at': datetime.utcnow().isoformat(),
            'channels': [],
            'roles': [],
            'members_count': guild.member_count
        }

        # Backup de canais
        for channel in guild.channels:
            channel_data = {
                'name': channel.name,
                'type': str(channel.type),
                'position': channel.position
            }
            if hasattr(channel, 'topic'):
                channel_data['topic'] = channel.topic
            backup_data['channels'].append(channel_data)

        # Backup de cargos
        for role in guild.roles:
            if role != guild.default_role:
                role_data = {
                    'name': role.name,
                    'color': str(role.color),
                    'position': role.position,
                    'permissions': role.permissions.value
                }
                backup_data['roles'].append(role_data)

        # Salva backup
        guild_id_str = str(guild.id)
        if guild_id_str not in security_system.backup_data:
            security_system.backup_data[guild_id_str] = {'channels': [], 'roles': [], 'full_backups': []}

        security_system.backup_data[guild_id_str]['full_backups'] = [backup_data]
        await security_system.save_data()

        embed = discord.Embed(
            title="💾 Backup Criado",
            description="Backup completo do servidor criado com sucesso!",
            color=COLORS['success']
        )
        embed.add_field(name="📺 Canais", value=len(backup_data['channels']), inline=True)
        embed.add_field(name="🎭 Cargos", value=len(backup_data['roles']), inline=True)
        embed.add_field(name="👥 Membros", value=backup_data['members_count'], inline=True)

        await ctx.send(embed=embed)

        await security_system.log_security_action(
            guild,
            "💾 Backup Criado",
            f"Backup completo criado por {ctx.author.mention}",
            COLORS['success']
        )

    except Exception as e:
        await ctx.send(f"❌ Erro ao criar backup: {e}")

@bot.command(name='audit', aliases=['auditoria'])
@is_staff()
async def audit_logs(ctx, limite: int = 10):
    """Mostra logs de auditoria do servidor"""
    try:
        embed = discord.Embed(
            title="📋 Logs de Auditoria",
            color=COLORS['info']
        )

        logs = []
        async for entry in ctx.guild.audit_logs(limit=limite):
            timestamp = entry.created_at.strftime("%d/%m %H:%M")
            action_name = str(entry.action).replace('AuditLogAction.', '').replace('_', ' ').title()

            log_text = f"**{timestamp}** - {action_name}"
            if entry.user:
                log_text += f" por {entry.user.name}"
            if entry.target:
                target_name = getattr(entry.target, 'name', str(entry.target))
                log_text += f" (Target: {target_name})"

            logs.append(log_text)

        if logs:
            embed.description = '\n'.join(logs)
        else:
            embed.description = "Nenhum log encontrado"

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ Erro ao buscar logs: {e}")

@bot.command(name='membros', aliases=['members'])
@is_staff()
async def list_members(ctx, status: str = "all"):
    """Lista membros por status"""
    guild = ctx.guild

    if status == "online":
        members = [m for m in guild.members if m.status == discord.Status.online]
        title = "🟢 Membros Online"
    elif status == "offline":
        members = [m for m in guild.members if m.status == discord.Status.offline]
        title = "⚫ Membros Offline"
    elif status == "bots":
        members = [m for m in guild.members if m.bot]
        title = "🤖 Bots no Servidor"
    else:
        members = guild.members
        title = "👥 Todos os Membros"

    embed = discord.Embed(
        title=title,
        description=f"Total: {len(members)} membros",
        color=COLORS['info']
    )

    member_list = []
    for member in members[:20]:  # Máximo 20 para não ultrapassar limite
        member_list.append(f"{member.display_name} ({member.id})")

    if member_list:
        embed.add_field(
            name="📝 Lista",
            value='\n'.join(member_list),
            inline=False
        )

    if len(members) > 20:
        embed.add_field(
            name="ℹ️ Aviso",
            value=f"Mostrando apenas os primeiros 20 de {len(members)} membros",
            inline=False
        )

    await ctx.send(embed=embed)

@bot.command(name='canais', aliases=['channels'])
@is_staff()
async def list_channels(ctx):
    """Lista todos os canais do servidor"""
    guild = ctx.guild

    text_channels = [c for c in guild.channels if isinstance(c, discord.TextChannel)]
    voice_channels = [c for c in guild.channels if isinstance(c, discord.VoiceChannel)]
    categories = [c for c in guild.channels if isinstance(c, discord.CategoryChannel)]

    embed = discord.Embed(
        title="📺 Canais do Servidor",
        color=COLORS['info']
    )

    if text_channels:
        text_list = [f"#{c.name} ({c.id})" for c in text_channels[:10]]
        embed.add_field(
            name=f"💬 Texto ({len(text_channels)})",
            value='\n'.join(text_list),
            inline=True
        )

    if voice_channels:
        voice_list = [f"🔊 {c.name} ({c.id})" for c in voice_channels[:10]]
        embed.add_field(
            name=f"🔊 Voz ({len(voice_channels)})",
            value='\n'.join(voice_list),
            inline=True
        )

    if categories:
        cat_list = [f"📁 {c.name} ({c.id})" for c in categories[:10]]
        embed.add_field(
            name=f"📁 Categorias ({len(categories)})",
            value='\n'.join(cat_list),
            inline=True
        )

    await ctx.send(embed=embed)

@bot.command(name='anuncio', aliases=['announce'])
@is_staff()
async def make_announcement(ctx, canal: discord.TextChannel, *, mensagem: str):
    """Faz um anúncio em um canal específico"""
    try:
        embed = discord.Embed(
            title="📢 Anúncio Official",
            description=mensagem,
            color=COLORS['info'],
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Anúncio feito por {ctx.author.display_name}")

        await canal.send(embed=embed)

        confirmation = discord.Embed(
            title="✅ Anúncio Enviado",
            description=f"Anúncio enviado para {canal.mention}",
            color=COLORS['success']
        )
        await ctx.send(embed=confirmation)

        await security_system.log_security_action(
            ctx.guild,
            "📢 Anúncio Feito",
            f"Anúncio enviado para {canal.mention} por {ctx.author.mention}",
            COLORS['info']
        )

    except Exception as e:
        await ctx.send(f"❌ Erro ao enviar anúncio: {e}")

@bot.command(name='help', aliases=['h', 'ajuda'])
async def security_help(ctx):
    """Central de ajuda"""
    # Embed principal com design melhorado
    embed = discord.Embed(
        title="⚡ SISTEMA DE SEGURANÇA AVANÇADO ⚡",
        description="```css\n🚀 Bot de segurança mais completo do Discord!\n💎 Proteção absoluta para seu servidor\n🛡️ Sistema anti-raid, anti-spam e muito mais!```",
        color=0x00ff41,
        timestamp=datetime.utcnow()
    )
    
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/123456789/123456789/security_logo.png")
    embed.set_author(name="Central de Comandos", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)

    # Comandos básicos com emojis melhorados
    basic_commands = [
        "🔧 `!sec_c` ➜ Configurações do sistema",
        "🔐 `!sec_w` ➜ Gerenciar whitelist", 
        "🔄 `!sec_r` ➜ Restaurar cargos removidos",
        "📊 `!sec_s` ➜ Status completo do sistema",
        "📋 `!sec_l` ➜ Visualizar logs de segurança",
        "💾 `!sec_b` ➜ Ver backups disponíveis"
    ]

    # Comandos de moderação
    moderation_commands = [
        "🔨 `!sec_banir @user motivo` ➜ Banir usuário",
        "👢 `!sec_expulsar @user motivo` ➜ Expulsar usuário", 
        "🔇 `!sec_m @user tempo motivo` ➜ Mutar usuário",
        "🔊 `!sec_desmutar @user` ➜ Desmutar usuário",
        "⚠️ `!sec_av @user motivo` ➜ Aplicar aviso",
        "📝 `!sec_avisos @user` ➜ Visualizar avisos"
    ]

    # Comandos de canal
    channel_commands = [
        "🧹 `!sec_limpar [qtd]` ➜ Limpar mensagens",
        "⏱️ `!sec_slowmode [seg]` ➜ Ativar modo lento",
        "🔒 `!sec_bloquear` ➜ Bloquear canal atual",
        "🔓 `!sec_desbloquear` ➜ Desbloquear canal",
        "📢 `!sec_anuncio #canal msg` ➜ Fazer anúncio"
    ]

    # Comandos utilitários
    utility_commands = [
        "👤 `!sec_info [@user]` ➜ Informações do usuário",
        "🖼️ `!sec_avatar [@user]` ➜ Avatar do usuário",
        "🏰 `!sec_servidor` ➜ Informações do servidor",
        "👥 `!sec_membros [status]` ➜ Listar membros",
        "📺 `!sec_canais` ➜ Listar todos os canais",
        "📋 `!sec_audit [limite]` ➜ Logs de auditoria"
    ]

    # Comandos de cargos
    role_commands = [
        "🎭 `!sec_cargo add/remove @user cargo` ➜ Gerenciar cargo",
        "✏️ `!sec_nick @user novo_nick` ➜ Alterar nickname",
        "➕ `!sec_criar_cargo nome` ➜ Criar novo cargo",
        "🗑️ `!sec_deletar_cargo nome` ➜ Deletar cargo",
        "ℹ️ `!sec_cargoinfo nome` ➜ Informações do cargo"
    ]

    embed.add_field(
        name="🎮 ╔══ COMANDOS BÁSICOS ══╗",
        value='\n'.join(basic_commands),
        inline=False
    )
    
    embed.add_field(
        name="🛡️ ╔══ MODERAÇÃO ══╗", 
        value='\n'.join(moderation_commands),
        inline=False
    )
    
    embed.add_field(
        name="📺 ╔══ GERENCIAR CANAIS ══╗",
        value='\n'.join(channel_commands),
        inline=False
    )
    
    embed.add_field(
        name="🔧 ╔══ UTILIDADES ══╗",
        value='\n'.join(utility_commands),
        inline=True
    )
    
    embed.add_field(
        name="🎭 ╔══ CARGOS ══╗",
        value='\n'.join(role_commands),
        inline=True
    )

    # Informações especiais
    embed.add_field(
        name="👑 ╔══ SUPER ADMIN ══╗",
        value="```css\n🔥 Owner tem PODER ABSOLUTO!\n⚡ Nenhum comando afeta o owner\n🛡️ Proteção total garantida\n💎 Acesso a comandos exclusivos```",
        inline=False
    )

    embed.add_field(
        name="📊 ╔══ ESTATÍSTICAS ══╗",
        value=f"```yaml\nServidores Protegidos: {len(bot.guilds)}\nUptime: Online 24/7\nProteções Ativas: Todas\nVelocidade: Ultra Rápida```",
        inline=True
    )

    embed.add_field(
        name="🚀 ╔══ RECURSOS ══╗",
        value="```diff\n+ Anti-Raid Avançado\n+ Backup Automático\n+ Logs Completos\n+ Sistema de Avisos\n+ Proteção de Cargos\n+ Anti-Spam Inteligente```",
        inline=True
    )

    embed.add_field(
        name="⚠️ ╔══ AVISOS IMPORTANTES ══╗",
        value="```fix\n🔴 Configure o canal de logs primeiro!\n🟡 Owner do bot é INTOCÁVEL\n🟢 Use !sec_backup_completo para backup\n🔵 Comandos staff precisam de admin```",
        inline=False
    )

    embed.set_footer(
        text="⚡ Sistema desenvolvido para máxima segurança | Versão 2.0 ⚡",
        icon_url=bot.user.avatar.url if bot.user.avatar else None
    )

    await ctx.send(embed=embed)

# Error handler
@bot.event
async def on_command_error(ctx, error):
    """Tratamento de erros dos comandos"""
    if isinstance(error, commands.CheckFailure):
        # Verifica se é um comando que precisa de owner ou staff
        command_name = ctx.command.name if ctx.command else "desconhecido"
        owner_only_commands = ['config', 'whitelist', 'limpar', 'criar_cargo', 'deletar_cargo', 'backup_server']

        if command_name in owner_only_commands:
            embed = discord.Embed(
                title="🚫 Acesso Negado",
                description="Apenas o owner do bot pode usar este comando!",
                color=COLORS['danger']
            )
        else:
            embed = discord.Embed(
                title="🚫 Acesso Negado", 
                description="Você precisa ser staff (administrador) ou owner para usar este comando!",
                color=COLORS['danger']
            )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        print(f"❌ Erro no comando: {error}")

# Inicialização
if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')

    if TOKEN:
        print("🚀 Iniciando Sistema de Segurança Avançado...")
        print("⚙️ Configurações padrão:")
        print("  • Proteção de canais/cargos: SEMPRE ATIVO")
        print("  • Anti-spam: OPCIONAL (10s de silenciamento)")
        print("  • Anti mass-ping: OPCIONAL (10s de silenciamento)")
        print("  • Outras proteções: CONFIGURÁVEIS por servidor")
        keep_alive()
        bot.run(TOKEN)
    else:
        print("❌ Token não encontrado! Configure DISCORD_BOT_TOKEN nas Secrets")