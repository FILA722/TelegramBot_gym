import os
import json
import telebot
from telebot import types
import time as t
from datetime import *
import gym_registry_bot_alarm
import conf

bot = telebot.TeleBot(conf.bot_id)

#директория, где будут храниться файлы со списком клиентов, которые записались на занятие
registry_file_dir = conf.file_dir

#файл с данными о работе бота
spy_file = conf.spy_file

#кол-во записей, котрые можно сделать с одного id в день.
REG_VALUE = conf.REG_VALUE

month = {
        '01':'січня',
        '02':'лютого',
        '03':'березня',
        '04':'квітня',
        '05':'травня',
        '06':'червня',
        '07':'липня',
        '08':'серпня',
        '09':'вересня',
        '10':'жовтня',
        '11':'листопада',
        '12':'грудня'
        }
#список с данными от пользователя. (сегодня/завтра, время записи, user_id)
client_registry_data = []

def spy(user_id):
    """
    записывает в директорию spy_file файл с записью user_id : колличество запросов
    """
    with open(spy_file, 'r') as spy_f:
        dict_id = json.load(spy_f)
        if user_id in dict_id.keys():
            dict_id[user_id] += 1
        else:
            dict_id[user_id] = 1
    new_dict_id = json.dumps(dict_id)
    with open(spy_file, 'w') as new_spy_file:
        new_spy_file.write(new_dict_id)

def check_registry(name, time_):
    """
    тут проверяеться валидность имени и имееться ли запись за этим именем
    на выходе вызывает ф-цию регистрации записи.
    """
    input_name = name.split(' ', 1)
    second_name_sep, name_sep = input_name[0], input_name[1]

    # Убрать из имени и фамилии пробелы, а также возможные лишние символы
    second_name_sep = second_name_sep.strip('.!"№%:,.;(){}[]/><#@$^&*_+-=|')
    name_sep = name_sep.strip('.!"№%:,.;(){}[]/><#@$^&*_+-=|')

    #формируем имя файла день_месяц_год
    if client_registry_data[0] == 'Сьогодні':
        file_name = f'{int(t.strftime("%d", t.localtime()))}_{t.strftime("%m", t.localtime())}_{t.strftime("%Y", t.localtime())}.json'
    elif client_registry_data[0] == 'Завтра':
        file_name = f'{int(t.strftime("%d", t.localtime())) + 1}_{t.strftime("%m", t.localtime())}_{t.strftime("%Y", t.localtime())}.json'

    #проверка имени и фамилии на отсутствие цифр и служебных символов
    if second_name_sep.isalpha() and name_sep.isalpha():
        gym_registry = registry_file_dir + file_name
        if not os.path.exists(gym_registry):  #создать файл для записи, если его нет
            rec = json.dumps({})
            with open(gym_registry, 'w') as gym_reg:
                gym_reg.write(rec)
        else: #если файл с запрашиваемой датой есть, проверить в нём наличие записи с аналогичным именем
            with open(gym_registry, 'r') as gym_reg:
                record = json.load(gym_reg)
                user_id = str(client_registry_data[2])
                spy(user_id)
                if user_id in record:
                    if record[user_id][0] >= REG_VALUE:
                        return f'Пробачте, можна зробити не більше трьох записів на один день.'
    else:
        return "Не вірно введене ім'я. Введіть своє справжнє ім'я в форматі: Прізвище Ім'я. Наприклад: Черкашина Олеся"
    return registry(name, time_, gym_registry)

def registry(name, time_, gym_registry):
    """
    Записать имя фамилию и время в файл, сформировать и вывести ответ.
    На входе: name - строка с именем и фамилией; time_ - НН час, на который записать; gym_registry - путь к файлу.
    Возвращает строку с ответом при успешной записи
    """
    day = date.today()
    if client_registry_data[0] == 'Завтра':
        day = day + timedelta(days=1)

    str_day = str(day)
    day_to_registry = f'{str_day[8:10]} {month[str_day[5:7]]}'

    with open(gym_registry, 'r') as gym_reg_1:
        record = json.load(gym_reg_1)
        user_id = str(client_registry_data[2])
        if user_id in record:
            record[user_id][0] += 1
            record[user_id][1][name] = time_
        else:
            record[user_id] = [1, {name: time_}]
    record_json = json.dumps(record)
    with open(gym_registry, 'w') as gym_reg:
        gym_reg.write(record_json)

    return f'Дякуємо! Чекаємо на Вас {client_registry_data[0].lower()}, {day_to_registry} o {client_registry_data[1]}:00'

def hour_range(day, hour=None):
    """
    На входе:
    day = день недели 6-суб, 0-вск
    hour = время, на которое хочет записаться клиент
    Возвращает:
    Кортеж (от"НН", до"НН") с часами, на которые доступна запись в зависимости от дня недели и времени когда делается запрос
    No - значит запись на сегодня уже недоступна(при запросе в последний час работы зала или после закрытия)
    """
    days = {0:(9, 21), 6:(8, 21), 1:(7, 23)} # "код дня недели:(режим работы (ч) от, до)"
    if day not in days.keys():
        day = 1
    if hour == None or hour < days[day][0]:
        return days[day][0], days[day][1]
    elif days[day][0] <= hour < days[day][1]:
            return hour, days[day][1]
    else:
        return 'No'

@bot.message_handler(commands=['start'])
def registry_btn(message):
    """
    Приветствие + формирование кнопок вместо клавы
    """
    markup = types.ReplyKeyboardMarkup(True)
    today = types.KeyboardButton(text='Сьогодні')
    tomorrow = types.KeyboardButton(text='Завтра')
    markup.add(today, tomorrow)
    bot.send_message(message.chat.id, "Вітаю! Ви хочете записатись на тренування сьогодні чи завтра? Оберіть варіант нижче:", reply_markup=markup)

"""
Команда администратора, которая выведет список имеющихся файлов с записями клиентов.
"""
@bot.message_handler(commands=['r2d2'])
def admin_mode(message):
    """
    Формирует список с названиями файлов (один файл - один день со всеми записями внутри)
    Формирует экранные кнопки для выбора нужного файла
    """
    files_list = os.listdir(registry_file_dir)
    files = [i for i in files_list]
    btn = types.InlineKeyboardMarkup()
    for file in sorted(files):
        btn_hour = types.InlineKeyboardButton(text=file, callback_data=file)
        btn.add(btn_hour)
    bot.send_message(message.chat.id, reply_markup=btn, text='Список имеющихся файлов:')

"""
Команда возвращает кол-во уникальных пользователей (users) и общее кол-во обращений к боту (cycles). 
"""
@bot.message_handler(commands=['spy'])
def spy_mode(message):
    with open(spy_file, 'r') as spy:
        dataset = json.load(spy)
        users = len(dataset) #кол-во уникальных пользователей
        cycles = 0 #общее кол-во запросов от всех пользователей
        for cycle in dataset.keys():
            cycles += dataset[cycle] #приба
        bot.send_message(message.chat.id, f'Users = {users}\nCycles = {cycles}')
"""
Генерирует рандомные имена клиентов и время их записи на занятие на весь день 
"""
@bot.message_handler(commands=['alarm'])
def alarm(message):
    bot.send_message(message.chat.id, 'Генерирую файл с generated.txt c именами клиентов...')
    gym_registry_bot_alarm.alarm() #Генерирует json файл  generated.json с рандомными именами и временем
    user_dict = {}
    file_name_txt = registry_file_dir + 'generated.txt'
    with open(registry_file_dir + 'generated.json', 'r') as text:
        l = json.load(text)
        for user_id in l:
            for user_name in l[user_id][1]:
                time = l[user_id][1][user_name]
                if time in user_dict:
                    user_dict[time].append(user_name)
                else:
                    user_dict[time] = [user_name]
    with open(file_name_txt, 'w') as output:
        total_count = 0
        for t in sorted(user_dict.keys()):
            output.write(f'\n-={t}:00=-\n')
            count = 1
            for n in sorted(user_dict[t]):
                output.write(f'{count}.{n}\n')
                count += 1
                total_count += 1
        output.write(f'Всього: {total_count}\n')
    txt = open(file_name_txt, 'rb')
    bot.send_document(message.chat.id, txt)
    os.remove(file_name_txt)
    os.remove(registry_file_dir + 'generated.json')

@bot.message_handler(content_types=['text'])
def hours_buttons(message):
    day_now = int(t.strftime("%w", t.localtime()))
    hour_now = int(t.strftime("%H", t.localtime()))

    # Обработка если клиент передал день
    if message.text == 'Сьогодні':
        client_registry_data.clear()
        client_registry_data.append(message.text)
        range_ = hour_range(day_now, hour_now)
        if range_ == 'No':
            bot.send_message(message.chat.id,"Нажаль на сьогодні вже запис неможливий, спробуйте записатись на завтра.")
            client_registry_data.clear()
        else:
            hours = [i for i in range(range_[0], range_[1])]
            btn = types.InlineKeyboardMarkup()
            for hour in hours:
                btn_hour = types.InlineKeyboardButton(text=f'{hour}:00', callback_data=hour)
                btn.add(btn_hour)
            bot.send_message(message.chat.id, reply_markup=btn,text='Оберіть приблизно годину, коли ви плануете відвідати зал:')
    elif message.text == 'Завтра':
        client_registry_data.clear()
        client_registry_data.append(message.text)
        tomorrow = day_now + 1
        if tomorrow == 7:
            range_ = hour_range(0)
        else:
            range_ = hour_range(tomorrow)
        if range_ == 'No':
            bot.send_message(message.chat.id,"Нажаль на сьогодні вже запис неможливий, спробуйте записатись на завтра.")
            client_registry_data.clear()
        else:
            hours = [i for i in range(range_[0], range_[1])]
            btn = types.InlineKeyboardMarkup()
            for hour in hours:
                btn_hour = types.InlineKeyboardButton(text=f'{hour}:00', callback_data=hour)
                btn.add(btn_hour)
            bot.send_message(message.chat.id, reply_markup=btn,text='Оберіть приблизно годину, коли ви плануете відвідати зал:')

    else: # обработка если клиент передал имя
        name = message.text.strip()
        if ' ' not in name:
            bot.send_message(message.chat.id, "Не вірно введене ім'я. Введіть своє справжнє ім'я в форматі: Прізвище Ім'я . Наприклад: Черкашина Олеся")
        elif not client_registry_data:
            bot.send_message(message.chat.id, "Ви хочете записатись на сьогодні чи на завтра? Будь-ласка оберіть варіант знизу:")
        else: #пустить процедуру проверки имени с последующей записей
            bot.send_message(message.chat.id, check_registry(message.text, client_registry_data[1]))
"""
Тут обрабатываються запросы с экранной клавы
"""
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if len(call.data) in (1,2) and str(call.data).isdigit(): # обработка если клиент передал время
        hour = call.data
        user_id = call.from_user.id
        client_registry_data.append(hour)
        client_registry_data.append(user_id)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Вкажіть своє справжнє Прізвище та Ім'я. Наприклад: Черкашина Олеся")
    elif '_' in str(call.data) and str(call.data)[10:] == '.json': # после выбора файла открыть его и выслать
        user_dict = {}
        file_name_txt = registry_file_dir + str(call.data)[:10] + '.txt'

        with open(registry_file_dir + str(call.data), 'r') as text:
            l = json.load(text)
            for user_id in l:
                for user_name in l[user_id][1]:
                    time = l[user_id][1][user_name]
                    if time in user_dict:
                        user_dict[time].append(user_name)
                    else:
                        user_dict[time] = [user_name]

        with open(file_name_txt, 'w') as output:
            total_count = 0
            for t in sorted(user_dict.keys()):
                output.write(f'\n-={t}:00=-\n')
                count = 1
                for n in sorted(user_dict[t]):
                    output.write(f'{count}.{n}\n')
                    count += 1
                    total_count += 1
            output.write(f'Всього: {total_count}\n')
        txt = open(file_name_txt, 'rb')
        bot.send_document(call.message.chat.id, txt)
        os.remove(file_name_txt)

if __name__== "__main__":
    bot.polling(none_stop=True, timeout=999999)