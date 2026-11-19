"""Comandos gerais do bot."""

import discord
from discord import app_commands
from discord.ext import commands


class Geral(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ajuda", description="Mostra o que o bot sabe fazer")
    async def ajuda(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="📖 O que eu sei fazer",
            description="Bot feito para comunidades de Minecraft.",
            color=discord.Color.blurple(),
        )

        # A lista é montada a partir dos comandos registrados,
        # então um comando novo aparece aqui sozinho.
        for comando in self.bot.tree.get_commands():
            if comando.default_permissions is not None:
                continue  # comandos só para administradores não aparecem aqui
            embed.add_field(name=f"/{comando.name}", value=comando.description, inline=False)

        embed.add_field(
            name="👋 Boas-vindas",
            value="Quando alguém entra no servidor, eu mando uma mensagem de boas-vindas.",
            inline=False,
        )
        embed.set_footer(text=f"Ping do bot: {round(self.bot.latency * 1000)} ms")

        # ephemeral=True: só quem usou o comando vê a resposta.
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Geral(bot))
