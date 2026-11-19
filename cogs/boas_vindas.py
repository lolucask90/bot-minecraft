"""Mensagem automática de boas-vindas para quem entra no servidor do Discord."""

import logging
import os

import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import escape_markdown

log = logging.getLogger(__name__)


class BoasVindas(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        canal = os.getenv("CANAL_BOAS_VINDAS_ID", "").strip()
        self.canal_id = int(canal) if canal.isdigit() else None

    def escolher_canal(self, guild: discord.Guild) -> discord.TextChannel | None:
        """Usa o canal do .env; se não tiver, usa o canal de mensagens do sistema."""
        if self.canal_id:
            canal = guild.get_channel(self.canal_id)
            if isinstance(canal, discord.TextChannel):
                return canal
        return guild.system_channel

    async def dar_boas_vindas(self, membro: discord.Member) -> discord.TextChannel | None:
        """Manda a mensagem e devolve o canal usado (ou None se não deu)."""
        canal = self.escolher_canal(membro.guild)
        if canal is None:
            log.warning("Nenhum canal de boas-vindas em %s", membro.guild.name)
            return None

        embed = discord.Embed(
            title=f"Bem-vindo(a), {escape_markdown(membro.display_name)}! 👋",
            description=(
                f"Que bom ter você em **{escape_markdown(membro.guild.name)}**!\n"
                "Digite `/ajuda` para ver o que eu sei fazer."
            ),
            color=discord.Color.gold(),
        )
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_footer(text=f"Agora somos {membro.guild.member_count} membros")

        try:
            # A menção fica fora do quadro para a pessoa receber a notificação.
            await canal.send(content=membro.mention, embed=embed)
        except discord.Forbidden:
            log.warning("Sem permissão para mandar mensagem em #%s", canal.name)
            return None
        return canal

    @commands.Cog.listener()
    async def on_member_join(self, membro: discord.Member) -> None:
        if not membro.bot:
            await self.dar_boas_vindas(membro)

    # Serve para testar (e tirar print) sem precisar de outra conta entrando no servidor.
    @app_commands.command(
        name="testar-boas-vindas",
        description="Mostra a mensagem de boas-vindas como se você tivesse acabado de entrar",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    async def testar(self, interaction: discord.Interaction) -> None:
        canal = await self.dar_boas_vindas(interaction.user)
        if canal:
            resposta = f"Pronto! Mandei a mensagem em {canal.mention}."
        else:
            resposta = (
                "Não consegui mandar. Defina CANAL_BOAS_VINDAS_ID no arquivo .env "
                "ou escolha um canal de mensagens do sistema nas configurações do servidor, "
                "e confira se eu tenho permissão para falar nele."
            )
        await interaction.response.send_message(resposta, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BoasVindas(bot))
