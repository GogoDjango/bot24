import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard
from vk_api.utils import get_random_id

POINTS = {}
TOKEN = '65aaee9bf0633e4ffacd37e8c47a6a2b4d01c5509b2b5067bb440139127e0b6206b2064c8c1ecd6a5db59'
GROUP_TOKEN = "8ed7ea937e32cbd20c6274d5f9d1090036c080b4dfb096cf262dbcf7bb535c3c89ec4c3c8d528d29c0421"
CARDS = []

KEYBOARD = VkKeyboard(one_time=False)
KEYBOARD.add_button('Продолжить', color='primary')
KEYBOARD.add_button('Мои баллы', color='positive')
KEYBOARD.add_line()
KEYBOARD.add_button('Сменить альбом', color='negative')

PACK = 5  # количество карт за раз
CARD_KEYBOARD = VkKeyboard(inline=True)
for i in range(PACK):
    CARD_KEYBOARD.add_button(str(i + 1), color='primary')
GROUPID = '212557440'


def send_message(user_id, message_text, attachment=None):
    vk.method('messages.send',
              {'user_id': user_id, 'message': message_text, 'random_id': get_random_id(), 'attachment': attachment})


def send_keyboard(user_id, keyboard, message_text, attachment=None):
    vk.method('messages.send', {'user_id': user_id, 'message': message_text, 'random_id': get_random_id(),
                                'keyboard': keyboard.get_keyboard(),
                                'inline': 'false', 'attachment': attachment})


# слушаем ответ на вопрос
def listen_answer(true_key, user_id):
    for event in longPoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            request = event.text

            if request.isdigit() and int(request) in [1, 2, 3, 4, 5]:
                if int(request) == true_key:
                    POINTS[user_id] += 3
                    send_keyboard(user_id=event.user_id, message_text=f'Верно! +3 балла!',
                                  keyboard=KEYBOARD)
                    return
                else:
                    send_keyboard(user_id=event.user_id,
                                  message_text=f'Неверно. Загаданная карта находилась под номером {true_key}',
                                  keyboard=KEYBOARD)
                    return
            else:
                send_keyboard(user_id=event.user_id, message_text='Я все еще жду твой ответ:',
                              keyboard=CARD_KEYBOARD)


# выдаем карты
def show_cards(session, alt=None):
    attachment = ''

    # проверяем на пустоту игровой сессии и на окончание карт в колоде
    validate = {x: y for x, y in session.items() if y['used'] == False}
    if not session:
        session = CARDS if event.user_id not in ALT_CARDS else alt
        for card in (CARDS if event.user_id not in ALT_CARDS else alt):
            session[card]['used'] = False
    elif len(validate) < PACK:
        for card in (CARDS if event.user_id not in ALT_CARDS else ALT_CARDS[event.user_id]):
            session[card]['used'] = False

    # упаковываем вложения для запроса к API
    while len(attachment.split(',')) - 1 < PACK:
        id = get_random_id() % len(session.keys())
        if not session[list(session.keys())[id]]['used']:
            attachment += f'{list(session.keys())[id]},'
        session[list(session.keys())[id]]['used'] = True
    attachment = attachment[:-1]

    picked_photo = attachment.split(',')[get_random_id() % PACK]
    keyword = session[picked_photo]['tags'][get_random_id() % len(session[picked_photo]['tags'])]

    # Случайно выбираем карту и слово из ее набора, проверив, не совпадает ли оно со словами других вложений
    #
    # Если в датасете есть две карты с полностью одинаковыми тегами, то это датасет плохой, а не мой код ;)
    # Поэтому True будет достаточно
    while True:
        for i in attachment.split(','):
            if i != picked_photo:
                if keyword in session[i]['tags']:
                    keyword = session[picked_photo]['tags'][get_random_id() % PACK]
        if keyword:
            break
        else:
            keyword = session[picked_photo]['tags'][get_random_id() % PACK]

    # Отправляем и ждем ответа!
    send_message(event.user_id, message_text='', attachment=attachment)
    send_keyboard(user_id=event.user_id, message_text=f'Слово {keyword}, угадай загаданную карту:',
                  keyboard=CARD_KEYBOARD)
    listen_answer(attachment.split(',').index(picked_photo) + 1, event.user_id)


alb_getter = vk_api.VkApi(token=TOKEN)  # создаем объект для обращения к альбомам(он не кушает токен группы)
vk = vk_api.VkApi(token=GROUP_TOKEN)
longPoll = VkLongPoll(vk)
ALT_CARDS = {}  # готовимся к новым колодам
photos = alb_getter.method('photos.get',  # загружаем основную
                           {'owner_id': '-212879524', 'album_id': '282320624', 'count': 100})

CARDS = {}
session = {}
keyword = ''
for i in photos['items']:
    CARDS[f'photo{i["owner_id"]}_{i["id"]}'] = {'tags': i['text'].split()}
for event in longPoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:
            request = event.text.lower()
            if event.user_id not in POINTS.keys():
                POINTS[event.user_id] = 0  # заводим нашемю юзеру кошелек для баллов

            if request in ['старт', 'cnfhn', 'продолжить']:
                if event.user_id in ALT_CARDS.keys():  # проверяем на моды
                    alt_ses = ALT_CARDS[event.user_id]
                    show_cards(alt_ses)
                else:
                    show_cards(session)

            elif request == 'мои баллы':
                send_message(event.user_id, message_text=f'Количество ваших баллов: {POINTS[event.user_id]}')

            elif 'https://vk.com/album' in request:  # генерируем новую колоду из альбома
                owner_id, id = request[request.index('album') + 5:].split('_')
                name = alb_getter.method('photos.getAlbums', {'owner_id': owner_id, 'album_ids': id})['items'][0][
                    'title']
                if event.user_id not in ALT_CARDS.keys():
                    ALT_CARDS[event.user_id] = {}
                send_message(event.user_id, message_text=f'Я тебя понял! Меняю колоду на {name}...')
                alt_photos = alb_getter.method('photos.get',
                                               {'owner_id': owner_id, 'album_id': id, 'count': 100})
                for i in alt_photos['items']:
                    ALT_CARDS[event.user_id][f'photo{i["owner_id"]}_{i["id"]}'] = {'tags': i['text'].split()}
                alt_ses = ALT_CARDS[event.user_id]
                for card in ALT_CARDS[event.user_id]:
                    alt_ses[card]['used'] = False
                show_cards(alt_ses, ALT_CARDS)

            elif 'альбом' in request:
                send_message(event.user_id,
                             message_text='Просто пришли мне ссылку на новую колоду... Если в ней не будет ключевых слов, я за себя не отвечаю')

            else:
                send_message(event.user_id, 'Мой создатель держит меня в заложниках, помоги... Или напиши "Старт"')
