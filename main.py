import discord
from discord.ext import tasks, commands
import asyncio
from collections import defaultdict

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Словарь для хранения таймеров откатов пользователей
cooldowns = {}
# Словарь для хранения статистики
user_stats = defaultdict(lambda: defaultdict(int))  # Пользователь -> Откат -> Количество

# Список откатов
timers = {
    "схемы": 4 * 60 * 60,  # 4 часа
    "швейка": 4 * 60 * 60,  # 4 часа
    "вступление в организацию": 2 * 60 * 60  # 2 часа
}

# Канал для уведомлений об откатах и статистики
NOTIFY_CHANNEL_ID = 1291053463895015485  # Замените на ID вашего канала для уведомлений
STATS_CHANNEL_ID = 1294698445583552595  # Замените на ID канала для статистики

# Класс с кнопками откатов
class CooldownView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=None)
        self.user = user

    async def start_cooldown(self, interaction: discord.Interaction, timer_name: str):
        await interaction.response.send_message(f"Откат на {timer_name} начался! Ждите уведомления.", ephemeral=True)

        # Запоминаем откат в статистику
        user_stats[self.user.id][timer_name] += 1

        cooldowns[self.user.id] = cooldowns.get(self.user.id, {})
        cooldowns[self.user.id][timer_name] = timers[timer_name]

        # Отсчет времени отката
        await asyncio.sleep(timers[timer_name])

        # Отправляем уведомление об окончании отката
        channel = bot.get_channel(NOTIFY_CHANNEL_ID)
        await channel.send(f"{self.user.mention}, откат на {timer_name} завершен!")

    # Кнопка "Схемы"
    @discord.ui.button(label="Схемы", style=discord.ButtonStyle.primary)
    async def start_schemes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.start_cooldown(interaction, "схемы")

    # Кнопка "Швейка"
    @discord.ui.button(label="Швейка", style=discord.ButtonStyle.primary)
    async def start_clothmaking(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.start_cooldown(interaction, "швейка")

    # Кнопка "Вступление в организацию"
    @discord.ui.button(label="Вступление в организацию", style=discord.ButtonStyle.primary)
    async def start_org(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.start_cooldown(interaction, "вступление в организацию")


# Команда для начала откатов
@bot.command(name="откат")
async def start_cooldown(ctx):
    view = CooldownView(ctx.author)
    await ctx.send("Выберите, на что начать откат:", view=view)


# Еженедельная задача для отправки статистики
@tasks.loop(hours=168)  # 168 часов = 1 неделя
async def send_weekly_stats():
    channel = bot.get_channel(STATS_CHANNEL_ID)
    if channel:
        message = "**Еженедельная статистика откатов**\n"
        for user_id, stats in user_stats.items():
            user = await bot.fetch_user(user_id)
            message += f"\n**{user.name}**:\n"
            for task, count in stats.items():
                message += f" - {task}: {count} откатов\n"
        
        await channel.send(message)
        user_stats.clear()  # Обнуляем статистику после отправки


# Обработчик события запуска бота
@bot.event
async def on_ready():
    print(f"Бот {bot.user} запущен и готов к работе.")
    send_weekly_stats.start()  # Запускаем задачу отправки статистики


# Запуск бота
bot.run("DISCORD_TOKEN")
