"""Ponto de partida do bot: lê as configurações do arquivo .env e liga tudo."""

import logging
import os

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN", "").strip()

# Cada "cog" é um arquivo da pasta cogs/ com um grupo de funções do bot.
EXTENSOES = [
    "cogs.geral",
    "cogs.minecraft",
    "cogs.boas_vindas",
]

log = logging.getLogger("bot")


class MeuBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        # Necessário para o bot saber quando alguém entra no servidor (boas-vindas).
        intents.members = True
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)

    async def setup_hook(self) -> None:
        for extensao in EXTENSOES:
            await self.load_extension(extensao)

        self.tree.error(self.erro_no_comando)

        # Envia a lista de comandos de barra (/status, /ajuda...) para o Discord.
        comandos = await self.tree.sync()
        log.info("%d comandos de barra sincronizados", len(comandos))

    async def on_ready(self) -> None:
        log.info("Bot online como %s (ID %s)", self.user, self.user.id)
        await self.change_presence(activity=discord.Game(name="/ajuda"))

    async def erro_no_comando(
        self, interaction: discord.Interaction, erro: app_commands.AppCommandError
    ) -> None:
        """Se um comando quebrar, avisa quem usou em vez de ficar em silêncio."""
        log.exception("Erro no comando /%s", interaction.command.name if interaction.command else "?", exc_info=erro)
        mensagem = "Algo deu errado ao executar esse comando. 😕 Tente de novo daqui a pouco."
        if interaction.response.is_done():
            await interaction.followup.send(mensagem, ephemeral=True)
        else:
            await interaction.response.send_message(mensagem, ephemeral=True)


def main() -> None:
    if not TOKEN or TOKEN == "cole_seu_token_aqui":
        raise SystemExit("❌ Coloque o token do bot no arquivo .env (linha DISCORD_TOKEN=...)")

    bot = MeuBot()
    try:
        bot.run(TOKEN, root_logger=True)
    except discord.LoginFailure:
        raise SystemExit(
            "❌ O Discord recusou o token. Gere um novo em Developer Portal → Bot → Reset Token "
            "e cole no arquivo .env."
        )
    except discord.PrivilegedIntentsRequired:
        raise SystemExit(
            "❌ Falta ativar a opção 'Server Members Intent' em Developer Portal → Bot → "
            "Privileged Gateway Intents."
        )


if __name__ == "__main__":
    main()
