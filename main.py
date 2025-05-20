import disnake
from disnake.ext import commands
from disnake import TextInputStyle

GUILD_ID = "YOUR_GIULD_ID"  # твой сервер
ADMIN_CHANNEL_ID = "YOUR_ADMIN_CHANNEL_ID" # канал заявок для стаффа
ROLE_ID = "YOUR_BLACKLIST_ROLE_ID" # роль, которой запрещено подавать заявку

intents = disnake.Intents.default()
intents.members = True  # чтобы выдавать роли
intents.message_content = False  # не нужен, т.к. используем только интерактив

bot = commands.Bot(command_prefix="!", intents=intents, test_guilds=[GUILD_ID])

class Application(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="Ваш возраст?",
                placeholder="пример: 17",
                custom_id="Возраст",
                style=TextInputStyle.short,
                max_length=25
            ),
            disnake.ui.TextInput(
                label="Ваш ник в игре?",
                placeholder="пример: steve",
                custom_id="Ник",
                style=TextInputStyle.short,
                max_length=32
            ),
            disnake.ui.TextInput(
                label="Откуда вы узнали о сервере?",
                placeholder="пустовато...",
                custom_id="Откуда_узнал",
                style=TextInputStyle.short,
                max_length=100
            ),
            disnake.ui.TextInput(
                label="Чем планируете заниматься на сервере?",
                placeholder="много чем...",
                custom_id="Планы",
                style=TextInputStyle.paragraph,
                max_length=400
            ),
        ]
        super().__init__(title="Заявка на сервер", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        user = inter.author
        guild = bot.get_guild(GUILD_ID)
        member = guild.get_member(user.id)

        # Проверка роли — на всякий случай (можно убрать, если сделано в команде)
        if member is not None and any(role.id == ROLE_ID for role in member.roles):
            await inter.response.send_message("❌ Вы уже являетесь игроком!", ephemeral=True)
            return

        embed = disnake.Embed(
            title="📩 Новая заявка на сервер",
            description=f"От пользователя {user.mention} (`{user}`)",
            color=disnake.Color.blurple()
        )
        for key, value in inter.text_values.items():
            embed.add_field(name=key.replace("_", " ").capitalize(), value=value[:1024], inline=False)

        view = ResponseButtons(member)

        channel = bot.get_channel(ADMIN_CHANNEL_ID)
        if not channel:
            await inter.response.send_message("❌ Канал для заявок не найден.", ephemeral=True)
            return

        await channel.send(embed=embed, view=view)

        await inter.response.send_message("✅ Ваша заявка отправлена!", ephemeral=True)


class ResponseButtons(disnake.ui.View):
    def __init__(self, member: disnake.Member):
        super().__init__(timeout=None)
        self.member = member

    @disnake.ui.button(label="✅ Принять", style=disnake.ButtonStyle.success)
    async def accept(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        role = inter.guild.get_role(ROLE_ID)
        if role is None:
            await inter.response.send_message("❌ Роль для выдачи не найдена.", ephemeral=True)
            return

        try:
            await self.member.add_roles(role, reason="Заявка принята")
        except disnake.Forbidden:
            await inter.response.send_message("❌ У бота нет прав выдавать роль.", ephemeral=True)
            return
        except Exception as e:
            await inter.response.send_message(f"❌ Ошибка при выдаче роли: {e}", ephemeral=True)
            return

        try:
            await self.member.send(f"🎉 Ваша заявка принята, ожидайте добавления в Whitelist (обычно занимает до 15 минут). Добро пожаловать на сервер {inter.guild.name}!")
        except disnake.Forbidden:
            # ЛС закрыты - игнорируем
            pass

        await inter.response.edit_message(content=f"✅ Заявка принята. Роль выдана {self.member.mention}", view=None)

    @disnake.ui.button(label="❌ Отклонить", style=disnake.ButtonStyle.danger)
    async def reject(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        try:
            await self.member.send(f"❌ Ваша заявка на сервер {inter.guild.name} была отклонена.")
        except disnake.Forbidden:
            # ЛС закрыты - игнорируем
            pass

        await inter.response.edit_message(content=f"❌ Заявка отклонена для {self.member.mention}", view=None)


@bot.slash_command(description="Подать заявку на сервер")
async def apply(inter: disnake.CommandInteraction):
    member = inter.author
    guild = bot.get_guild(GUILD_ID)
    member = guild.get_member(member.id)  # убедиться, что объект Member, а не User

    if member is None:
        await inter.response.send_message("❌ Ошибка: участник не найден на сервере.", ephemeral=True)
        return

    # Проверка роли
    if any(role.id == ROLE_ID for role in member.roles):
        await inter.response.send_message("❌ У вас уже есть роль, заявки подавать нельзя.", ephemeral=True)
        return

    # Отправляем предупреждение + кнопку
    class ApplyButton(disnake.ui.View):
        @disnake.ui.button(label="Заполнить заявку", style=disnake.ButtonStyle.primary)
        async def open_modal(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
            await interaction.response.send_modal(Application())

    warning_embed = disnake.Embed(
        description="⚠️ Пожалуйста, убедитесь, что у вас открыты Личные Сообщения от участников сервера.\n"
                    "Бот отправит вам сообщение после рассмотрения заявки.",
        color=disnake.Color.orange()
    )

    await inter.response.send_message(embed=warning_embed, view=ApplyButton(), ephemeral=False)


@bot.event
async def on_ready():
    await bot.change_presence(activity=disnake.Activity(type=disnake.ActivityType.watching, name="анкеты"))
    print(f"Бот запущен как {bot.user}")

bot.run("BOT_TOKEN")

