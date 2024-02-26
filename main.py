import os
import json
import requests
import telebot
from dotenv import load_dotenv
from telebot.types import Message
from googletrans import Translator

load_dotenv()

bot = telebot.TeleBot(os.environ['BOT_TOKEN'])


@bot.message_handler(commands=['start'])
def start(message: Message):
  """
  Обработчик команды `/start`: нужен исключительно для запуска бота
  Заглушка; не выполняет никаких действий.
  """

  pass


@bot.message_handler(commands=['weather'])
def weather(message: Message):
  """
  Обработчик команды `/weater {город}`: собирает, форматирует, и отправляет данные о погоде
  """

  # Валидация введенной команды
  splitted_message = message.text.split(' ')
  if len(splitted_message) <= 1:
    bot.reply_to(message, 'Неверный формат команды: `/weather {город}`\nПример: `/weather Москва`')
    return None
  

  def translate_city_name(ru_city_name: str):
    """
    Перевести название города для дальнейшего использования в запросах
    """

    translator = Translator()
    en_city_name = translator.translate(
      ru_city_name.capitalize(), 
      dest='en', 
      src='ru'
    )
    return en_city_name.text
  
  city = translate_city_name(splitted_message[1])
  

  def get_weather(city) -> str:
    """
    Получить данные о погоде в заданном городе
    """

    api_key = os.environ['WEATHER_API_KEY']
    api_url = os.environ['WEATHER_API_URL']

    weather_data = requests.get(api_url, params={
      'key': api_key,
      'q': city
    })


    def format_response(weather_data: dict) -> str:
      """
      Отформатировать ответное сообщение
      """


      def format_wind_direction(direction_label: str):
        """
        Отформатировать поле `wind_dir`
        """

        # Набор всех направлений
        wind_directions = {
            'N': 'северный ветер',
            'NNE': 'северо-восточный ветер',
            'NE': 'северо-восточный ветер',
            'ENE': 'восточно-северо-восточный ветер',
            'E': 'восточный ветер',
            'ESE': 'ветер с востока на юго-восток',
            'SE': 'ветер с юго-востока',
            'SSE': 'ветер с юга на юго-восток',
            'S': 'южный ветер',
            'SSW': 'юго-западный ветер',
            'SW': 'юго-западный ветер',
            'WSW': 'западно-юго-западный ветер',
            'W': 'западный ветер',
            'WNW': 'ветер западный-северо-западный',
            'NW': 'ветер северо-западный',
            'NNW': 'ветер северо-западный',
            'N360': 'северный ветер'
        }

        return wind_directions[direction_label]


      def format_last_update(last_update: str):
        """
        Отформатировать поле `last_update`
        """

        last_update_parts = last_update.split(' ')
        date_part = last_update_parts[0].split('-')
        date_str = f'{date_part[2]}.{date_part[1]}.{date_part[0]}'
        time_str = last_update_parts[1]
        return f'{date_str} {time_str}'
      

      def format_condition(condition_code: int):
        """
        Отформатировать поле `condition`
        """


        def find_condition_by_code(conditions_data: list, condition_code: int):
          """
          Найти погодное условие по его коду
          """

          for condition_data in conditions_data:
            if condition_data['code'] == condition_code:
              return condition_data


        def find_ru_equivalent(condition_data: dict):
          """
          Найти перевод название погодного условия
          """

          for condition_translation in condition_data['languages']:
            if condition_translation['lang_iso'] == 'ru':
              return condition_translation['day_text']

        # Запрос к справочнику погодных условий
        conditions_data_request = requests.get('https://www.weatherapi.com/docs/conditions.json')
        conditions_data_request.encoding = 'utf-8-sig'
        conditions_data = json.loads(conditions_data_request.text)
        condition = find_condition_by_code(conditions_data, condition_code)
        formated_condition = find_ru_equivalent(condition)
        return formated_condition

      main_data = weather_data['current']
      temperature = main_data['temp_c']
      feels_like = main_data['feelslike_c']
      wind_speed = main_data['wind_kph']

      last_update = format_last_update(main_data['last_updated'])
      wind_direction = format_wind_direction(main_data['wind_dir'])
      condition = format_condition(main_data['condition']['code'])

      response_parts = [
        f'⌛ Данные от [{last_update}]',
        f'🌂 {condition}',
        f'🌡️ Температура {temperature} °C (ощущается как {feels_like} °C)',
        f'🌬️ {wind_direction.capitalize()}, скорость {wind_speed} км/ч'
      ]

      return '\n'.join(response_parts)

    return format_response(json.loads(weather_data.text))
  
  bot.reply_to(message, get_weather(city))

bot.polling(none_stop=True, interval=0)
