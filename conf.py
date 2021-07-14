"""
Токен бота
"""
bot_id = ''

"""
Директория куда нужно складывать файлы с записями клиентов
"""
file_dir = ''

"""
Путь с названием файла .json с колличеством уникальных 
пользователей и общим колличеством обращений к боту.
"""
spy_file = ''

"""
Кол-во записей, котрые можно сделать с одного id в день.
"""
REG_VALUE = 3

"""
Режим работы зала:
Если зал не работает в этот день, введите значение открытия и закрытия = 0 
"""
#В будние дни
work_day_from = 7 #открытие
work_day_to = 23 #закрытие

#В субботу
saturday_work_from = 8 #открытие
saturday_work_to = 21 #закрытие

#В воскресенье
sunday_work_from = 9 #открытие
sunday_work_to = 21 #закрытие

"""
Укажите диапазон записей клиентов в день (от - до) 
которые будут генерироваться при вызове команды /alarm
"""
NUM_FROM = 400
NUM_TO = 600