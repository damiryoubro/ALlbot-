import discord
import random
import os
import requests
from discord.ext import commands
import asyncio
import chess
import chess.svg
import cairosvg
from datetime import datetime, timedelta
from discord import app_commands
import time
import sympy as sp
import svgwrite



birthdays = {}  # Словарь для хранения дней рождения


intents = discord.Intents.default()
intents.message_content = False  # Выключено, так как это не нужно для слэш-команд
intents.members = True  # Включите, если нужно работать с участниками

bot = commands.Bot(command_prefix='/', intents=intents)

# Событие при готовности бота
@bot.event
async def on_ready():
    await bot.tree.sync()  # Синхронизирует слэш-команды с Discord
    print(f'Бот {bot.user} готов!')

# Варианты для игры
options = ["камень", "ножницы", "бумага"]

# Команда для игры "Камень-ножницы-бумага"
@bot.tree.command(name="каменьножницыбумага", description="Игра 'Камень, ножницы, бумага' против бота или другого пользователя.")
@app_commands.describe(opponent="Ваш оппонент: выберите другого пользователя или играйте против бота", choice="Ваш выбор: камень, ножницы или бумага")
async def каменьножницыбумага(interaction: discord.Interaction, opponent: discord.Member = None, choice: str = None):
    explanation = (
        "Как играть:\n"
        "1. Выберите 'камень', 'ножницы' или 'бумага'.\n"
        "2. Если играете с ботом, бот тоже сделает выбор.\n"
        "3. Если играете с другим пользователем, ожидайте, пока он сделает свой выбор.\n"
        "4. Победитель определяется по классическим правилам: камень побеждает ножницы, ножницы побеждают бумагу, бумага побеждает камень."
    )

    if choice is None:
        await interaction.response.send_message("Вы не сделали выбор. Пожалуйста, выберите 'камень', 'ножницы' или 'бумага'.\n" + explanation, ephemeral=True)
        return

    user_choice = choice.lower()

    if user_choice not in options:
        await interaction.response.send_message("Пожалуйста, выберите одно из следующих: камень, ножницы, бумага.\n" + explanation, ephemeral=True)
        return

    if opponent is None or opponent == interaction.user:
        # Игра против бота
        bot_choice = random.choice(options)
        if user_choice == bot_choice:
            result = "Ничья!"
        elif (user_choice == "камень" and bot_choice == "ножницы") or \
             (user_choice == "ножницы" and bot_choice == "бумага") or \
             (user_choice == "бумага" and bot_choice == "камень"):
            result = "Вы выиграли!"
        else:
            result = "Бот выиграл!"

        await interaction.response.send_message(
            f"Вы выбрали: {user_choice.capitalize()}.\nБот выбрал: {bot_choice.capitalize()}.\n{result}\n" + explanation,
            ephemeral=False
        )
    else:
        # Игра против другого пользователя
        await interaction.response.send_message(f"Ожидаем, пока {opponent.mention} сделает свой выбор.\n" + explanation, ephemeral=False)


# Словарь для хранения текущих шахматных игр
games = {}

# Функция для генерации изображения шахматной доски (PNG)
def generate_chess_board_png(board: chess.Board, filename="chessboard.png"):
    # Генерация SVG доски
    svg_data = chess.svg.board(board=board).encode("utf-8")
    # Конвертация SVG в PNG
    cairosvg.svg2png(bytestring=svg_data, write_to=filename)

# Команда для запуска шахматной партии
@bot.tree.command(name="шахматы", description="Организовать шахматную партию с ботом или другим пользователем.")
async def шахматы(interaction: discord.Interaction):
    explanation = (
        "Как играть в шахматы:\n"
        "1. Выберите команду '/ход', чтобы сделать ход.\n"
        "2. Введите ход в формате шахматной нотации, например 'e2e4' для перемещения пешки с e2 на e4.\n"
        "3. После каждого хода доска обновляется.\n"
        "4. Игра продолжается до шаха и мата или ничьей."
    )

    await interaction.response.send_message("Начинаем шахматную партию против бота!\n" + explanation, ephemeral=False)
    
    # Создаем новую доску
    board = chess.Board()

    # Сохраняем игру в словарь игр
    games[interaction.user.id] = {"board": board}

    # Генерируем PNG доски и отправляем
    generate_chess_board_png(board)
    await interaction.followup.send(file=discord.File("chessboard.png"))

# Команда для хода в шахматной партии
@bot.tree.command(name="ход", description="Сделать ход в шахматной партии.")
@app_commands.describe(move="Введите ваш ход (например, e2e4)")
async def ход(interaction: discord.Interaction, move: str):
    explanation = (
        "Как сделать ход:\n"
        "1. Введите ход в формате 'e2e4' (например, для перемещения пешки с e2 на e4).\n"
        "2. После этого доска обновится и бот сделает свой ход, если играете против бота."
    )

    game = games.get(interaction.user.id)

    if not game:
        await interaction.response.send_message("У вас нет активной партии! Начните новую с помощью команды /шахматы.\n" + explanation, ephemeral=True)
        return

    board = game["board"]

    # Проверяем правильность хода
    try:
        chess_move = chess.Move.from_uci(move)
        if chess_move not in board.legal_moves:
            raise ValueError("Недопустимый ход.")
        board.push(chess_move)
    except ValueError:
        await interaction.response.send_message("Некорректный ход! Пожалуйста, введите ход в формате e2e4.\n" + explanation, ephemeral=True)
        return

    # Генерируем PNG доски после хода
    generate_chess_board_png(board)
    
    # Проверка, используется ли response или followup
    if interaction.response.is_done():
        await interaction.followup.send(f"Вы сделали ход: {move}.\n" + explanation, file=discord.File("chessboard.png"))
    else:
        await interaction.response.send_message(f"Вы сделали ход: {move}.\n" + explanation, file=discord.File("chessboard.png"))

    # Проверяем окончание игры
    if board.is_checkmate():
        await interaction.followup.send(f"Шах и мат! {interaction.user.mention} выиграл.")
        del games[interaction.user.id]
        return
    elif board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves():
        await interaction.followup.send("Игра завершилась ничьей.")
        del games[interaction.user.id]
        return

    # Если игра с ботом, то делаем ход бота
    bot_move = random.choice(list(board.legal_moves))
    board.push(bot_move)
    generate_chess_board_png(board)  # Генерируем доску для хода бота

    await interaction.followup.send(f"Бот сделал ход: {bot_move}.\n" + explanation, file=discord.File("chessboard.png"))

# Функция для получения координат города через Nominatim API с заголовком User-Agent
def get_coordinates(city: str):
    url = f"https://nominatim.openstreetmap.org/search?q={city}&format=json&limit=1"
    headers = {
        'User-Agent': 'DiscordWeatherBot/1.0 (damiryoubro@mail.ru)'  # Укажите свой email
    }
    response = requests.get(url, headers=headers)

    print(f"Status code: {response.status_code}")
    print(f"Response text: {response.text}")

    if response.status_code == 200 and response.json():
        data = response.json()[0]
        lat = data.get('lat')
        lon = data.get('lon')
        if lat and lon:
            return float(lat), float(lon)
    return None

# Команда для получения погоды
@bot.tree.command(name="weather", description="Показывает текущую погоду в указанном городе.")
@app_commands.describe(city="Название города для получения информации о погоде")
async def weather(interaction: discord.Interaction, city: str):
    # Получение координат города через Nominatim API
    coordinates = get_coordinates(city)
    
    if not coordinates:
        await interaction.response.send_message(f"Город {city} не найден.", ephemeral=True)
        return

    lat, lon = coordinates

    # Запрос к Open-Meteo API
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        current_weather = data['current_weather']

        temp = current_weather['temperature']
        wind_speed = current_weather['windspeed']

        # Формируем сообщение
        embed = discord.Embed(title=f"Погода в городе {city.capitalize()}", color=discord.Color.blue())
        embed.add_field(name="Температура", value=f"{temp}°C", inline=True)
        embed.add_field(name="Скорость ветра", value=f"{wind_speed} км/ч", inline=True)

        await interaction.response.send_message(embed=embed)

    else:
        await interaction.response.send_message(f"Не удалось получить данные о погоде для города {city}.", ephemeral=True)


# Команда для игры "Найди пару"
@bot.tree.command(name="найдипару", description="Игра 'Найди пару'. Открывайте две карточки за ход и находите совпадающие пары.")
async def найдите_пару(interaction: discord.Interaction):
    explanation = (
        "Как играть в 'Найди пару':\n"
        "1. Игра представляет сетку из 16 перевёрнутых карточек (4x4).\n"
        "2. Введите два числа (от 1 до 16), чтобы открыть две карточки за ход.\n"
        "3. Если карточки совпадают, они остаются открытыми.\n"
        "4. Игра заканчивается, когда все пары найдены."
    )

# Команда 8ball
@bot.tree.command(name="8ball", description="Ответит на ваш вопрос в стиле магического шара.")
@app_commands.describe(question="Ваш вопрос, на который бот даст ответ.")
async def ball(interaction: discord.Interaction, question: str):
    responses = [
        "Да", "Нет", "Может быть", "Скорее всего", "Точно!", "Никогда!", "Спроси позже", 
        "Конечно", "Совершенно верно", "Вряд ли", "Лучше не знать", "Наверное", "Определённо да", "Не сейчас"
    ]
    
    # Случайный выбор ответа
    answer = random.choice(responses)
    
    # Ответ на вопрос
    await interaction.response.send_message(f"🎱 Ваш вопрос: {question}\nОтвет: {answer}", ephemeral=False)


    # Создание карточек (пары)
    items = ['🍎', '🍌', '🍒', '🍇', '🍉', '🍓', '🍑', '🍍']
    board = items * 2  # Дублирование для создания пар
    random.shuffle(board)

    # Сетка из 16 карточек (4x4)
    grid = [['❓'] * 4 for _ in range(4)]
    matched_pairs = []  # Уже угаданные пары

    def format_grid():
        return "\n".join(" ".join(row) for row in grid)
    

    explanation = "Выберите два числа, чтобы открыть карточки. Совпадения образуют пару. Напишите сперва первую цифру отправьте его и потом вторую!"
    

    await interaction.response.send_message(
    f"Игра началась! Найдите все пары. Вот текущая сетка:\n\n{format_grid()}\n" + explanation,
    ephemeral=False
)

    while len(matched_pairs) < 8:
        def check(msg):
            return msg.author == interaction.user and msg.content.isdigit() and 1 <= int(msg.content) <= 16

        # Просим игрока ввести два числа для открытия карточек
        await interaction.followup.send("Введите два числа (от 1 до 16), чтобы открыть карточки.")
        
        try:
            msg1 = await bot.wait_for('message', check=check, timeout=30.0)
            msg2 = await bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await interaction.followup.send("Время вышло! Игра окончена.")
            return
        
        pos1 = int(msg1.content) - 1
        pos2 = int(msg2.content) - 1
        
        # Преобразуем числа в позиции на сетке 4x4
        row1, col1 = divmod(pos1, 4)
        row2, col2 = divmod(pos2, 4)

        # Открываем карточки
        if grid[row1][col1] != '❓' or grid[row2][col2] != '❓' or (row1 == row2 and col1 == col2):
            await interaction.followup.send("Карточки уже открыты или вы выбрали одну и ту же карточку. Попробуйте снова.")
            continue
        
        # Открываем карточки для игрока
        grid[row1][col1] = board[pos1]
        grid[row2][col2] = board[pos2]
        
        await interaction.followup.send(f"Вы открыли:\n{format_grid()}")
        
        # Проверяем, совпадают ли карточки
        if board[pos1] == board[pos2]:
            await interaction.followup.send(f"Пара найдена: {board[pos1]}!")
            matched_pairs.append((row1, col1))
            matched_pairs.append((row2, col2))
        else:
            await interaction.followup.send(f"Пара не найдена. Карточки будут снова перевёрнуты.")
            await asyncio.sleep(2)
            # Закрываем карточки
            grid[row1][col1] = '❓'
            grid[row2][col2] = '❓'

    await interaction.followup.send("Поздравляем! Вы нашли все пары!")


import os

# Получение абсолютного пути к файлу words2.txt
script_dir = os.path.dirname(os.path.realpath(__file__))  # Папка, где находится скрипт
words_file_path = os.path.join(script_dir, 'words2.txt')   # Полный путь к файлу words2.txt

# Загрузка слов из файла words2.txt
try:
    with open(words_file_path, 'r', encoding='utf-8') as file:
        words = [word.strip().lower() for word in file.readlines()]
except FileNotFoundError:
    words = []  # Пустой список, если файл не найден

# Проверка, что список слов не пуст
if not words:
    raise ValueError("Список слов пуст или файл words2.txt не найден. Убедитесь, что файл существует и заполнен.")


@bot.tree.command(name="угадайслово", description="Запускает игру по угадыванию слова.")
async def угадайслово(interaction: discord.Interaction):
    word_to_guess = random.choice(words)
    guessed_word = ["_"] * len(word_to_guess)
    attempts_left = 6
    guessed_letters = []

    def format_word():
        return " ".join(guessed_word)

    await interaction.response.send_message(f"Игра началась! Загаданное слово: {format_word()}\nКоличество попыток: {attempts_left}", ephemeral=False)

    while attempts_left > 0 and "_" in guessed_word:
        def check(msg):
            return msg.author == interaction.user and len(msg.content) == 1 and msg.content.isalpha()

        await interaction.followup.send(f"Угадайте букву. Оставшиеся попытки: {attempts_left}")

        try:
            guess_msg = await bot.wait_for("message", check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await interaction.followup.send("Время вышло! Игра окончена.")
            return  # Эта строка завершает функцию в случае тайм-аута

        guess = guess_msg.content.lower()

        # Логика обработки введённой буквы
        if guess in guessed_letters:
            await interaction.followup.send("Эта буква уже была угадана. Попробуйте снова.")
            continue

        guessed_letters.append(guess)

        if guess in word_to_guess:
            for index, letter in enumerate(word_to_guess):
                if letter == guess:
                    guessed_word[index] = guess
            await interaction.followup.send(f"Верно! Слово: {format_word()}")
        else:
            attempts_left -= 1
            await interaction.followup.send(f"Неверно. Осталось попыток: {attempts_left}\nСлово: {format_word()}")

    if "_" not in guessed_word:
        await interaction.followup.send(f"Поздравляем! Вы угадали слово: {''.join(guessed_word)}")
    else:
        await interaction.followup.send(f"Игра окончена! Загаданное слово было: {word_to_guess}")


# Команда для получения информации о пользователе
@bot.tree.command(name="userinfo", description="Получить информацию о пользователе.")
@app_commands.describe(user="Пользователь, информацию о котором вы хотите получить.")
async def userinfo(interaction: discord.Interaction, user: discord.Member = None):
    # Если пользователь не указан, выводим информацию о пользователе, который использовал команду
    if user is None:
        user = interaction.user
    
    # Получение информации о пользователе
    embed = discord.Embed(title=f"Информация о пользователе {user.name}", color=discord.Color.blue())
    embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
    embed.add_field(name="ID", value=user.id, inline=True)
    embed.add_field(name="Имя пользователя", value=f"{user.name}#{user.discriminator}", inline=True)
    embed.add_field(name="Никнейм на сервере", value=user.display_name, inline=True)
    embed.add_field(name="Аккаунт создан", value=user.created_at.strftime("%d.%m.%Y %H:%M:%S"), inline=True)
    embed.add_field(name="Присоединился к серверу", value=user.joined_at.strftime("%d.%m.%Y %H:%M:%S"), inline=True)
    embed.add_field(name="Роли", value=", ".join([role.name for role in user.roles if role.name != "@everyone"]), inline=False)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="serverinfo", description="Получить информацию о сервере.")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild  # Текущий сервер (гильдия)

    # Получение информации о сервере
    embed = discord.Embed(title=f"Информация о сервере {guild.name}", color=discord.Color.green())
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    embed.add_field(name="ID сервера", value=guild.id, inline=True)
    embed.add_field(name="Владелец", value=guild.owner.mention, inline=True)
    embed.add_field(name="Создан", value=guild.created_at.strftime("%d.%m.%Y %H:%M:%S"), inline=True)
    embed.add_field(name="Участников", value=guild.member_count, inline=True)
    embed.add_field(name="Количество ролей", value=len(guild.roles), inline=True)
    embed.add_field(name="Количество текстовых каналов", value=len(guild.text_channels), inline=True)
    embed.add_field(name="Количество голосовых каналов", value=len(guild.voice_channels), inline=True)

    await interaction.response.send_message(embed=embed)



@bot.tree.command(name="hug", description="Отправляет виртуальные объятия указанному пользователю.")
@app_commands.describe(user="Пользователь, которого хотите обнять")
async def hug(interaction: discord.Interaction, user: discord.Member):
    # Сообщения об объятиях
    hugs = [
        f"{interaction.user.mention} обнимает {user.mention}! 🤗",
        f"{interaction.user.mention} посылает теплые объятия {user.mention}! 🫂",
        f"{user.mention} получает обнимашки от {interaction.user.mention}! ❤️",
        f"{interaction.user.mention} крепко обнял {user.mention}! 💖"
    ]
    
    # Выбираем случайное сообщение
    hug_message = random.choice(hugs)
    
    # Отправляем сообщение
    await interaction.response.send_message(hug_message)


# Команда coinflip - подбрасывание монеты
@bot.tree.command(name="coinflip", description="Подбрасывает монету: орёл или решка.")
async def coinflip(interaction: discord.Interaction):
    outcome = random.choice(["Орёл", "Решка"])
    await interaction.response.send_message(f"Монета выпала на: {outcome}")

# Команда roll [число] - Генерация случайного числа
@bot.tree.command(name="roll", description="Генерирует случайное число от 1 до указанного числа.")
@app_commands.describe(number="Максимальное число для генерации")
async def roll(interaction: discord.Interaction, number: int):
    result = random.randint(1, number)
    await interaction.response.send_message(f"Вы получили число: {result}")

# Команда timer [время] - Установка таймера
@bot.tree.command(name="timer", description="Устанавливает таймер на указанное время (в секундах).")
@app_commands.describe(time_in_seconds="Время в секундах")
async def timer(interaction: discord.Interaction, time_in_seconds: int):
    await interaction.response.send_message(f"Таймер установлен на {time_in_seconds} секунд.")
    await asyncio.sleep(time_in_seconds)
    await interaction.followup.send(f"Таймер завершен! {interaction.user.mention}")

# Команда math [выражение] - Решение математических выражений
@bot.tree.command(name="math", description="Решает математическое выражение.")
@app_commands.describe(expression="Математическое выражение для вычисления")
async def math(interaction: discord.Interaction, expression: str):
    try:
        result = sp.sympify(expression)
        await interaction.response.send_message(f"Результат: {result}")
    except Exception as e:
        await interaction.response.send_message(f"Ошибка в выражении: {e}")

# Команда birthday [дата] - Запоминание и напоминание о дне рождения
@bot.tree.command(name="birthday", description="Запоминает день рождения и напоминает о нём.")
@app_commands.describe(birthday_date="Введите день рождения в формате ДД.ММ.ГГГГ")
async def birthday(interaction: discord.Interaction, birthday_date: str):
    try:
        birthday_obj = datetime.strptime(birthday_date, "%d.%m.%Y")
        birthdays[interaction.user.id] = birthday_obj
        await interaction.response.send_message(f"Ваш день рождения {birthday_date} был запомнен!")
    except ValueError:
        await interaction.response.send_message("Неправильный формат даты. Пожалуйста, используйте формат ДД.ММ.ГГГГ.")

# Команда avatar [пользователь] - Показ аватара пользователя
@bot.tree.command(name="avatar", description="Показывает аватар указанного пользователя.")
@app_commands.describe(user="Пользователь, чей аватар нужно показать")
async def avatar(interaction: discord.Interaction, user: discord.Member = None):
    if user is None:
        user = interaction.user
    avatar_url = user.display_avatar.url
    embed = discord.Embed(title=f"Аватар пользователя {user.display_name}")
    embed.set_image(url=avatar_url)
    await interaction.response.send_message(embed=embed)



# Словарь для хранения текущих игр крестики-нолики
tictactoe_games = {}

# Генерация изображения крестиков-ноликов
def generate_tictactoe_board(board, filename="tictactoe.svg"):
    size = 300
    square_size = size // 3
    dwg = svgwrite.Drawing(filename, size=(size, size))
    
    # Рисуем сетку
    for i in range(1, 3):
        dwg.add(dwg.line((i * square_size, 0), (i * square_size, size), stroke='black'))
        dwg.add(dwg.line((0, i * square_size), (size, i * square_size), stroke='black'))
    
    # Рисуем крестики и нолики
    for y in range(3):
        for x in range(3):
            if board[y][x] == 'X':
                dwg.add(dwg.line((x * square_size + 10, y * square_size + 10), 
                                 ((x + 1) * square_size - 10, (y + 1) * square_size - 10), stroke='red', stroke_width=5))
                dwg.add(dwg.line((x * square_size + 10, (y + 1) * square_size - 10), 
                                 ((x + 1) * square_size - 10, y * square_size + 10), stroke='red', stroke_width=5))
            elif board[y][x] == 'O':
                dwg.add(dwg.circle(center=((x + 0.5) * square_size, (y + 0.5) * square_size), 
                                   r=square_size // 2 - 10, stroke='blue', stroke_width=5, fill='none'))
    
    dwg.save()
    cairosvg.svg2png(url=filename, write_to="tictactoe.png")

# Функция для проверки победы
def check_winner(board):
    # Проверяем строки, столбцы и диагонали
    for row in board:
        if row[0] == row[1] == row[2] and row[0] != '':
            return row[0]
    
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] and board[0][col] != '':
            return board[0][col]
    
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] != '':
        return board[0][0]
    
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] != '':
        return board[0][2]
    
    return None

# Команда для начала игры в крестики-нолики
@bot.tree.command(name="tictactoe", description="Игра в крестики-нолики с другим пользователем.")
@app_commands.describe(opponent="Пользователь, с которым вы хотите сыграть")
async def tictactoe(interaction: discord.Interaction, opponent: discord.Member):
    if opponent == interaction.user:
        await interaction.response.send_message("Вы не можете играть сами с собой!", ephemeral=True)
        return

    # Создаём пустую доску 3x3
    board = [['' for _ in range(3)] for _ in range(3)]
    
    # Сохраняем игру
    tictactoe_games[interaction.user.id] = {"board": board, "turn": interaction.user, "opponent": opponent}

    # Генерируем изображение доски
    generate_tictactoe_board(board)

    # Отправляем изображение доски
    await interaction.response.send_message(f"Игра в крестики-нолики началась! {interaction.user.mention} против {opponent.mention}.", file=discord.File("tictactoe.png"))

# Команда для хода в крестики-нолики
@bot.tree.command(name="ходтик", description="Сделать ход в игре крестики-нолики.")
@app_commands.describe(position="Введите позицию (1-9), куда хотите поставить символ.")
async def ходтик(interaction: discord.Interaction, position: int):
    game = tictactoe_games.get(interaction.user.id)

    if not game:
        await interaction.response.send_message("У вас нет активной партии! Начните новую с помощью команды /tictactoe.", ephemeral=True)
        return

    board = game["board"]
    turn = game["turn"]
    opponent = game["opponent"]

    if turn != interaction.user:
        await interaction.response.send_message("Сейчас не ваш ход!", ephemeral=True)
        return

    # Преобразуем позицию (1-9) в координаты на доске (3x3)
    row, col = divmod(position - 1, 3)

    # Проверяем, занято ли место
    if board[row][col] != '':
        await interaction.response.send_message("Это место уже занято! Попробуйте другое.", ephemeral=True)
        return

    # Ход игрока
    board[row][col] = 'X' if interaction.user == turn else 'O'

    # Проверка победы
    winner = check_winner(board)
    if winner:
        generate_tictactoe_board(board)
        await interaction.response.send_message(f"Поздравляем! {interaction.user.mention} выиграл!", file=discord.File("tictactoe.png"))
        del tictactoe_games[interaction.user.id]
        return

    # Проверяем ничью
    if all(cell != '' for row in board for cell in row):
        generate_tictactoe_board(board)
        await interaction.response.send_message(f"Игра закончилась ничьей!", file=discord.File("tictactoe.png"))
        del tictactoe_games[interaction.user.id]
        return

    # Меняем ход
    game["turn"] = opponent

    # Генерируем новую доску после хода
    generate_tictactoe_board(board)

    # Отправляем обновлённое изображение доски
    await interaction.response.send_message(f"{interaction.user.mention} сделал ход на позиции {position}. Теперь ходит {opponent.mention}.", file=discord.File("tictactoe.png"))

# Команда для бана пользователя
@bot.tree.command(name="бан", description="Забанить пользователя на сервере.")
@app_commands.describe(member="Участник, которого нужно забанить", reason="Причина бана")
async def бан(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    await member.ban(reason=reason)
    await interaction.response.send_message(f'Пользователь {member.mention} был забанен. Причина: {reason}', ephemeral=True)

# Команда для кика пользователя
@bot.tree.command(name="кик", description="Кикнуть пользователя с сервера.")
@app_commands.describe(member="Участник, которого нужно кикнуть", reason="Причина кика")
async def кик(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    await member.kick(reason=reason)
    await interaction.response.send_message(f'Пользователь {member.mention} был кикнут. Причина: {reason}', ephemeral=True)

@bot.tree.command(name="мьют", description="Выдать мьют пользователю.")
@app_commands.describe(member="Участник, которого нужно замьютить", duration="Длительность в минутах", reason="Причина мьюта")
async def мьют(interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = None):
    timeout_duration = timedelta(minutes=duration)
    try:
        await member.edit(timed_out_until=discord.utils.utcnow() + timeout_duration, reason=reason)
        await interaction.response.send_message(f'Пользователь {member.mention} был замьючен на {duration} минут. Причина: {reason}', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f'Не удалось замьютить пользователя {member.mention}. Ошибка: {str(e)}', ephemeral=True)

# Команда для снятия мьюта
@bot.tree.command(name="размьют", description="Снять мьют с пользователя.")
@app_commands.describe(member="Участник, которого нужно размьютить")
async def размьют(interaction: discord.Interaction, member: discord.Member):
    await member.timeout(None)
    await interaction.response.send_message(f'Пользователь {member.mention} был размьючен', ephemeral=True)

# Команда для временного назначения роли
@bot.tree.command(name="временнаяроль", description="Временно назначить роль пользователю.")
@app_commands.describe(member="Участник, которому нужно назначить роль", role="Роль, которую нужно назначить", duration="Длительность в минутах")
async def временнаяроль(interaction: discord.Interaction, member: discord.Member, role: discord.Role, duration: int):
    await member.add_roles(role)
    await interaction.response.send_message(f'Пользователю {member.mention} была выдана роль {role.name} на {duration} минут', ephemeral=True)
    
    await asyncio.sleep(duration * 60)
    await member.remove_roles(role)
    await interaction.followup.send(f'Роль {role.name} была снята с пользователя {member.mention}', ephemeral=True)



bot.run('MTI4MDcwODg2MDQyODAyNTg5OA.G2693v.nYz1guiuXWRE0fSdw2Pv28vnO1MxFkTZ1n7Hw4')
