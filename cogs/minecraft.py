"""Comando /status: consulta servidores de Minecraft (Java Edition)."""

import base64
import binascii
import io
import logging
import os
import re

import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import escape_markdown
from mcstatus import JavaServer

log = logging.getLogger(__name__)

TEMPO_LIMITE = 5  # segundos esperando o servidor responder
MAX_NOMES = 10  # quantos nomes de jogadores mostrar, no máximo

# Códigos de cor do Minecraft, tipo "§a" ou "§l"
CODIGOS_DE_COR = re.compile(r"§.")


def limpar(texto: str) -> str:
    """Tira os códigos de cor do Minecraft e protege o texto da formatação do Discord."""
    return escape_markdown(CODIGOS_DE_COR.sub("", texto)).strip()


def numero(n: int) -> str:
    """Formata números grandes do jeito brasileiro: 19755 -> 19.755"""
    return f"{n:,}".replace(",", ".")


def embed_offline(endereco: str) -> discord.Embed:
    return discord.Embed(
        title="🔴 Servidor offline ou inacessível",
        description=(
            f"Não consegui falar com `{endereco}`.\n"
            "Confira se o IP está certo e se o servidor está ligado.\n\n"
            "*Por enquanto eu só consulto servidores Java Edition.*"
        ),
        color=discord.Color.red(),
    )


def icone_do_servidor(resposta) -> discord.File | None:
    """O servidor manda o ícone como texto (base64). Aqui viramos imagem de novo."""
    if not resposta.icon:
        return None
    try:
        dados = base64.b64decode(resposta.icon.split(",", 1)[-1])
    except (binascii.Error, ValueError):
        return None
    return discord.File(io.BytesIO(dados), filename="icone.png")


def embed_online(endereco: str, resposta) -> discord.Embed:
    motd = limpar(resposta.motd.to_plain())
    embed = discord.Embed(
        title="🟢 Servidor online",
        description=motd or "*Sem descrição*",
        color=discord.Color.green(),
        timestamp=discord.utils.utcnow(),
    )
    embed.add_field(name="Endereço", value=f"`{endereco}`", inline=False)
    embed.add_field(
        name="Jogadores", value=f"{numero(resposta.players.online)}/{numero(resposta.players.max)}"
    )
    embed.add_field(name="Versão", value=limpar(resposta.version.name) or "?")
    embed.add_field(name="Ping", value=f"{round(resposta.latency)} ms")

    # Alguns servidores mostram uma amostra de quem está jogando.
    nomes = [limpar(p.name) for p in (resposta.players.sample or [])]
    nomes = [n for n in nomes if n][:MAX_NOMES]
    if nomes:
        embed.add_field(name="Quem está jogando", value=", ".join(nomes), inline=False)

    return embed


class Minecraft(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.servidor_padrao = os.getenv("SERVIDOR_MINECRAFT_PADRAO", "").strip()

    @app_commands.command(
        name="status", description="Mostra se um servidor de Minecraft está online"
    )
    @app_commands.describe(ip="Endereço do servidor, ex: play.exemplo.com ou 123.45.67.89:25565")
    async def status(self, interaction: discord.Interaction, ip: str | None = None) -> None:
        endereco = (ip or self.servidor_padrao).strip().replace("`", "")[:100]
        if not endereco:
            await interaction.response.send_message(
                "Me diga o IP do servidor, por exemplo: `/status ip:play.exemplo.com`",
                ephemeral=True,
            )
            return

        # Perguntar ao servidor pode passar de 3 segundos (o limite do Discord para
        # responder), então primeiro avisamos que o bot está "pensando".
        await interaction.response.defer(thinking=True)

        try:
            servidor = await JavaServer.async_lookup(endereco, timeout=TEMPO_LIMITE)
            resposta = await servidor.async_status()
        except Exception as erro:  # IP errado, servidor desligado, tempo esgotado...
            log.info("Não consegui consultar %s: %r", endereco, erro)
            await interaction.followup.send(embed=embed_offline(endereco))
            return

        embed = embed_online(endereco, resposta)
        icone = icone_do_servidor(resposta)
        if icone:
            embed.set_thumbnail(url="attachment://icone.png")
            await interaction.followup.send(embed=embed, file=icone)
        else:
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Minecraft(bot))
