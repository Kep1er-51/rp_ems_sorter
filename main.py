import os
import shutil
import configparser
from datetime import datetime, timedelta
from PIL import Image
import pytesseract

# Основные категории
categories = ["Таблетки", "ПМП", "ПМП ОБ", "Мед. Карты", "Уколы", "МП-ГМП-АКЦИИ"]

# Подкатегории актуальности
subcategories = ["Повышение + Недельный отчет", "Недельный отчет", "Мусор"]

# Путь к конфигурационному файлу
config_file = 'config.ini'

# Получение дат
now = datetime.now()
start_of_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

# Укажите путь к tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Функция для чтения конфигурации
def read_config():
    config = configparser.ConfigParser()
    config.read(config_file)
    if 'SETTINGS' in config:
        base_dir = config['SETTINGS'].get('base_dir', '/path/to/screenshots')
        last_promotion_time_str = config['SETTINGS'].get('last_promotion_time', '2024-07-18 00:00')
        last_promotion_time = datetime.strptime(last_promotion_time_str, '%Y-%m-%d %H:%M')
        path_visibility = config['SETTINGS'].getboolean('path_visibility', True)
    else:
        base_dir = '/path/to/screenshots'
        last_promotion_time = datetime(2024, 7, 18, 0, 0)
        path_visibility = True
    return base_dir, last_promotion_time, path_visibility

# Функция для записи конфигурации
def write_config(base_dir, last_promotion_time, path_visibility):
    config = configparser.ConfigParser()
    config['SETTINGS'] = {
        'base_dir': base_dir,
        'last_promotion_time': last_promotion_time.strftime('%Y-%m-%d %H:%M'),
        'path_visibility': str(path_visibility)
    }
    with open(config_file, 'w') as configfile:
        config.write(configfile)

# Функция для инициализации папок
def initialize_directories(base_dir):
    for category in categories:
        category_path = os.path.join(base_dir, category)
        if not os.path.exists(category_path):
            os.makedirs(category_path)
        for subcategory in subcategories:
            subcategory_path = os.path.join(category_path, subcategory)
            if not os.path.exists(subcategory_path):
                os.makedirs(subcategory_path)

# Функция для определения категории скриншота
def determine_category(screenshot):
    resolution = screenshot.size  # (width, height)

    area1 = (resolution[0] / 2 - 270, resolution[1] - 290, resolution[0] / 2 - 270 + 560, resolution[1] - 30)
    area2 = (resolution[0] / 2 - 585, resolution[1] / 2 - 225, resolution[0] / 2 - 585 + 700, resolution[1] / 2 - 225 + 40)
    area3 = (resolution[0] / 2 - 250, resolution[1] / 2 - 95, resolution[0] / 2 - 250 + 220, resolution[1] / 2 - 95 + 20)
    area4 = (int(430 * resolution[0] / 2560), resolution[1] - 75, int(430 * resolution[0] / 2560) + 300, resolution[1] - 25)

    region1 = screenshot.crop(area1)
    region2 = screenshot.crop(area2)
    region3 = screenshot.crop(area3)
    region4 = screenshot.crop(area4)

    text1 = str(pytesseract.image_to_string(region1, lang='rus+eng'))
    text2 = str(pytesseract.image_to_string(region2, lang='rus+eng'))
    text3 = str(pytesseract.image_to_string(region3, lang='rus+eng'))
    text4 = str(pytesseract.image_to_string(region4, lang='rus+eng'))

    if 'ваши' in text2.lower() and 'предметы' in text2.lower() and 'склад' in text2.lower():
        return "ПМП"
    elif 'вы' in text1.lower() and 'успешно' in text1.lower() and 'оказали' in text1.lower() and 'первую' in text1.lower() and 'помощь' in text1.lower():
        if any(place in text4.lower() for place in
               ['занкудо', 'палето', 'чилиад', 'гора', 'джосайя', 'гордо', 'пустыня', 'гранд', 'сенора',
                'сан-шаньский', 'шорс', 'чумаш', 'грейпсид', 'брэддока', 'хармони', 'ратон', 'аламо', 'кэтфиш',
                'дигнити', 'дейвис', 'кварц', 'тюрьма']):
            return "ПМП ОБ"
        else:
            return None
    elif 'гражданин' in text1.lower() and 'принял' in text1.lower() and 'предложение' in text1.lower():
        if '1500' in text1.lower():
            return "Уколы"
        else:
            return "Таблетки"
    elif 'medical' in text3.lower() and 'card' in text3.lower():
        return "Мед. Карты"
    else:
        return None

# Функция для перемещения скриншотов в нужные подкатегории
def move_to_subcategory(category_path, screenshot_path, screenshot_name, last_promotion_time):
    creation_time = datetime.fromtimestamp(os.path.getmtime(screenshot_path))
    if creation_time > last_promotion_time:
        new_subcategory = subcategories[0]  # Повышение + Недельный отчет
    elif creation_time > start_of_week:
        new_subcategory = subcategories[1]  # Недельный отчет
    else:
        new_subcategory = subcategories[2]  # Мусор

    new_subcategory_path = os.path.join(category_path, new_subcategory)
    if not os.path.exists(new_subcategory_path):
        os.makedirs(new_subcategory_path)
    shutil.move(screenshot_path, os.path.join(new_subcategory_path, screenshot_name))

# Функция для распределения скриншотов по категориям и подкатегориям
def distribute_screenshots(base_dir, last_promotion_time):
    for category in categories:
        category_path = os.path.join(base_dir, category)
        for screenshot_name in os.listdir(category_path):
            screenshot_path = os.path.join(category_path, screenshot_name)
            if os.path.isfile(screenshot_path) and screenshot_name not in subcategories:
                screenshot = Image.open(screenshot_path)
                new_category = determine_category(screenshot)
                if new_category and new_category != category:
                    new_category_path = os.path.join(base_dir, new_category)
                    if not os.path.exists(new_category_path):
                        os.makedirs(new_category_path)
                    move_to_subcategory(new_category_path, screenshot_path, screenshot_name, last_promotion_time)
                else:
                    move_to_subcategory(category_path, screenshot_path, screenshot_name, last_promotion_time)

# Функция для обновления актуальности скриншотов
def update_screenshot_relevance(base_dir, last_promotion_time):
    for category in categories:
        for subcategory in subcategories:
            subcategory_path = os.path.join(base_dir, category, subcategory)
            if os.path.exists(subcategory_path):
                for screenshot_name in os.listdir(subcategory_path):
                    screenshot_path = os.path.join(subcategory_path, screenshot_name)
                    if os.path.isfile(screenshot_path):
                        # Проверяем, в правильной ли категории находится скриншот
                        screenshot = Image.open(screenshot_path)
                        new_category = determine_category(screenshot)
                        if new_category and new_category != category:
                            new_category_path = os.path.join(base_dir, new_category)
                            if not os.path.exists(new_category_path):
                                os.makedirs(new_category_path)
                            move_to_subcategory(new_category_path, screenshot_path, screenshot_name, last_promotion_time)
                        else:
                            move_to_subcategory(os.path.join(base_dir, category), screenshot_path, screenshot_name, last_promotion_time)

# Функция для получения ввода с защитой от дурака
def get_valid_input(prompt, validation_func):
    while True:
        user_input = input(prompt)
        if validation_func(user_input):
            return user_input
        else:
            print("Некорректный ввод. Попробуйте снова.")

# Основная функция
def main():
    base_dir, last_promotion_time, path_visibility = read_config()

    print("Если в ближайшее время вам не понадобится изменять настройки пути, то напишите в качестве ответа на вопрос о пути '1'. Чтобы вернуть эту настройку, введите '1' в вопросе о дате.")

    if path_visibility:
        get_valid_input_1 = get_valid_input(f"Текущий путь к скриншотам: {base_dir}. Хотите обновить? (y/n/1): ", lambda x: x.lower() in ['y', 'n', '1'])
        if get_valid_input_1 == 'y':
            base_dir = get_valid_input("Введите новый путь к скриншотам: ", os.path.isdir)
        elif get_valid_input_1 == '1':
            path_visibility = False

    get_valid_input_2 = get_valid_input(f"Текущая дата последнего повышения: {last_promotion_time.strftime('%Y-%m-%d %H:%M')}. Хотите обновить? (y/n/1): ", lambda x: x.lower() in ['y', 'n', '1'])
    if get_valid_input_2 == 'y':
        last_promotion_time_str = get_valid_input("Введите новую дату последнего повышения (гггг-мм-дд чч:мм): ", lambda x: bool(datetime.strptime(x, '%Y-%m-%d %H:%M')))
        last_promotion_time = datetime.strptime(last_promotion_time_str, '%Y-%m-%d %H:%M')
    elif get_valid_input_2 == '1':
        path_visibility = True

    #вопрос для проверки, является ли пользователь сотрудником SS или PRMD
    get_valid_input_3 = get_valid_input("Вы являетесь сотрудником SS или PRMD (если вы являетесь 10 рангом или выше, в любом случае ответьте 'n')? (y/n): ", lambda x: x.lower() in ['y', 'n'])
    if get_valid_input_3 == 'n':
        last_promotion_time = now + timedelta(days=1)

    write_config(base_dir, last_promotion_time, path_visibility)

    initialize_directories(base_dir)

    distribute_screenshots(base_dir, last_promotion_time)
    update_screenshot_relevance(base_dir, last_promotion_time)

    for filename in os.listdir(base_dir):
        file_path = os.path.join(base_dir, filename)
        if os.path.isfile(file_path) and file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            screenshot = Image.open(file_path)
            category = determine_category(screenshot)
            if category:
                category_path = os.path.join(base_dir, category)
                move_to_subcategory(category_path, file_path, filename, last_promotion_time)

if __name__ == "__main__":
    main()
