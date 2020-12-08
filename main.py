import requests
import telegram
from service import api_calls
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, Filters, CallbackQueryHandler, ConversationHandler, MessageHandler, RegexHandler

import logging
from core import bot_variables, sensitive, bot_states, bot_messages

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)


### COMMANDS ###

def check_auth(user_data):
    return 'access_token' in user_data

def authorise_request(bot, update, user_data):
    password = update.message.text
    response = api_calls.authorise(update.message.chat_id, password)
    logger.info("password: {}".format(password))
    if response.status_code == 200:
        response_json = response.json()
        logger.info("token received {}".format(response_json["access_token"]))
        user_data['access_token'] = "Bearer " + response_json["access_token"]
        bot.send_message(chat_id=update.message.chat_id, text="success")
        return ConversationHandler.END
    else:
        bot.send_message(chat_id=update.message.chat_id, text=bot_messages.error_password_response)
        return bot_states.PASSWORD

def start(bot, update, user_data):
    logger.info("UserId: {}".format(update.message.chat_id))
    if check_auth(user_data) == False:
        bot.send_message(chat_id=update.message.chat_id, text=bot_messages.auth_start_response)
    else:
        bot.send_message(chat_id=update.message.chat_id, text=bot_messages.start_response)

def get_group_schedule(bot, update, user_data):
    if check_auth(user_data) == False:
        bot.send_message(chat_id=update.message.chat_id, text=bot_messages.authorisation_response)
    else:
        reply_markup = InlineKeyboardMarkup(api_calls.get_courses())
        bot.send_message(chat_id=update.message.chat_id, text='Select the course:', reply_markup=reply_markup)

def get_teacher_schedule(bot, update, user_data):
    if check_auth(user_data) == False:
        bot.send_message(chat_id=update.message.chat_id, text=bot_messages.authorisation_response)
    else:
        reply_markup = InlineKeyboardMarkup(api_calls.get_departments())
        bot.send_message(chat_id=update.message.chat_id, text='Select the department:', reply_markup=reply_markup)

def get_free_rooms(bot, update, user_data):
    if check_auth(user_data) == False:
        bot.send_message(chat_id=update.message.chat_id, text=bot_messages.authorisation_response)
    else:
        reply_markup = InlineKeyboardMarkup(api_calls.get_free_room_days())
        bot.send_message(chat_id=update.message.chat_id, text='Select the day:', reply_markup=reply_markup)

def get_my_group_schedule(bot, update, user_data):
    if check_auth(user_data) == False:
        bot.send_message(chat_id=update.message.chat_id, text=bot_messages.authorisation_response)
    else:
        group_id = api_calls.get_user_group_id(update.message.chat_id, user_data['access_token'])
        if group_id == -1:
            bot.send_message(chat_id=update.message.chat_id, text=bot_messages.get_my_group_schedule_failure_response)
        else:
            user_data['block_id'] = str(group_id)
            user_data['requested_type'] = 'group'
            user_data['is_search'] = ''
            text = 'Select the day:'
            reply_markup = InlineKeyboardMarkup(api_calls.get_days(str(group_id), 'group'))
            bot.send_message(chat_id=update.message.chat_id,
                            text=text,
                            reply_markup=reply_markup,
                            parse_mode=telegram.ParseMode.HTML)

def authorise(bot, update):
    update.message.reply_text(bot_messages.password_response)
    return bot_states.PASSWORD

def set_my_group(bot, update, user_data):
    if check_auth(user_data) == False:
        update.message.reply_text(bot_messages.authorisation_response)
        return ConversationHandler.END
    else:
        update.message.reply_text(bot_messages.set_my_group_response)
        return bot_states.SET_GROUP

def search(bot, update, user_data):
    if check_auth(user_data) == False:
        update.message.reply_text(bot_messages.authorisation_response)
        return ConversationHandler.END
    else:
        update.message.reply_text(bot_messages.search_response)
        return bot_states.SEARCH

def help(bot, update, user_data):
    if check_auth(user_data) == False:
        bot.send_message(chat_id=update.message.chat_id, text=bot_messages.authorisation_response)
    else:
        bot.send_message(chat_id=update.message.chat_id, text=bot_messages.help_response)

def unknown_command(bot, update, user_data):
    if check_auth(user_data) == False:
        bot.send_message(chat_id=update.message.chat_id, text=bot_messages.authorisation_response)
    else:
        bot.send_message(chat_id=update.message.chat_id, text=bot_messages.unknown_response)

def feedback_command(bot, update, user_data):
    if check_auth(user_data) == False:
        bot.send_message(chat_id=update.message.chat_id, text=bot_messages.authorisation_response)
    else:
        bot.send_message(chat_id=update.message.chat_id, text=bot_messages.feedback_response)

#################
def set_group_request(bot, update, user_data):
    search_text = update.message.text
    schedule_data_list = api_calls.get_result_of_search(search_text, True)

    if not schedule_data_list:
        bot.send_message(chat_id=update.message.chat_id, text=bot_messages.set_my_group_failure_response)
    else:
        schedule_data = schedule_data_list[0]
        if schedule_data.type == 'group' and (schedule_data.matching >= 0.9 or (search_text in schedule_data.name and len(search_text.split('-')[1]) >= 4)):
            response_status = api_calls.set_user_group_id(update.message.chat_id, schedule_data.id, user_data['access_token'])
            if response_status == 200:
                bot.send_message(chat_id=update.message.chat_id, text=bot_messages.set_my_group_success_response)
            else:
                bot.send_message(chat_id=update.message.chat_id, text=bot_messages.set_my_group_server_error_response)
            return ConversationHandler.END
        else:
            bot.send_message(chat_id=update.message.chat_id, text=bot_messages.set_my_group_failure_response)
            return bot_states.SET_GROUP

def search_request(bot, update, user_data):
    search_text = update.message.text
    user_data['search_text'] = search_text

    reply_markup = InlineKeyboardMarkup(api_calls.get_result_of_search(search_text, False))

    if not reply_markup['inline_keyboard']:
        bot.send_message(chat_id=update.message.chat_id, text='Try again, no groups for this requests:')
        return bot_states.SEARCH
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Select one of the options:', reply_markup=reply_markup)
        return ConversationHandler.END


def edit_message_with_reply_markup(bot, update, text, reply_markup):
    query = update.callback_query
    bot.answerCallbackQuery(callback_query_id=query.id,
                            text='Loading...')

    bot.edit_message_text(chat_id=query.message.chat_id, text=text, message_id=query.message.message_id,
                          parse_mode=telegram.ParseMode.HTML)
    bot.edit_message_reply_markup(chat_id=query.message.chat_id, reply_markup=reply_markup,
                                  message_id=query.message.message_id)


### CALLBACK QUERIES ###

def get_days(block_id, requested_type):
    group_data_raw = None

    if requested_type == 'group':
        group_data_raw = requests.get('{}/?block_id={}'.format(sensitive.GET_TIMETABLE_BLOCK_URL, block_id))
    elif requested_type == 'teacher':
        group_data_raw = requests.get('{}/?teacher_id={}'.format(sensitive.GET_TIMETABLE_TEACHER_URL, block_id))
    elif requested_type == 'room':
        group_data_raw = requests.get('{}/?bundle_id={}'.format(sensitive.GET_TIMETABLE_ROOM_URL, block_id))

    group_data = group_data_raw.json()['timetable'].keys()
    days_name = []

    for data in group_data:
        days_name.append([InlineKeyboardButton(bot_variables.days[int(data) - 1]["en"], callback_data='day' + data)])

    return days_name


def get_free_room_callback_query(bot, update):
    text = 'Select the day:'
    reply_markup = InlineKeyboardMarkup(api_calls.get_free_room_days())
    edit_message_with_reply_markup(bot, update, text, reply_markup)


def get_courses_callback_query(bot, update):
    text = 'Select the course:'

    reply_markup = InlineKeyboardMarkup(api_calls.get_courses())
    edit_message_with_reply_markup(bot, update, text, reply_markup)


def get_departments_callback_query(bot, update):
    text = 'Select the department:'

    reply_markup = InlineKeyboardMarkup(api_calls.get_departments())
    edit_message_with_reply_markup(bot, update, text, reply_markup)


def get_search_results_callback_query(bot, update):
    text = 'Select one of the options:'

    msg = update.callback_query.data

    search_text = msg[19:]
    reply_markup = InlineKeyboardMarkup(api_calls.get_result_of_search(search_text, False))
    edit_message_with_reply_markup(bot, update, text, reply_markup)


def get_specialties_callback_query(bot, update, user_data):
    text = 'Select the specialty:'

    msg = update.callback_query.data

    course_id = msg[6:]
    user_data['course_id'] = course_id

    reply_markup_raw = api_calls.get_specialties(course_id)
    reply_markup_raw.append([InlineKeyboardButton('<<', callback_data='courses_menu')])
    reply_markup = InlineKeyboardMarkup(reply_markup_raw)

    edit_message_with_reply_markup(bot, update, text, reply_markup)


def get_groups_callback_query(bot, update, user_data):
    text = 'Select the group:'

    msg = update.callback_query.data

    specialty_id = msg[9:]
    course_id = user_data['course_id']
    user_data['specialty_id'] = specialty_id

    reply_markup_raw = api_calls.get_groups(course_id, specialty_id)
    reply_markup_raw.append([InlineKeyboardButton('<<', callback_data='course' + course_id)])
    reply_markup = InlineKeyboardMarkup(reply_markup_raw)

    edit_message_with_reply_markup(bot, update, text, reply_markup)


def get_group_days_callback_query(bot, update, user_data):
    text = 'Select the day:'

    msg = update.callback_query.data

    block_id = msg[5:]
    user_data['block_id'] = block_id
    user_data['requested_type'] = 'group'
    user_data['is_search'] = ''
    specialty_id = -1
    try:
        specialty_id = user_data['specialty_id']
    except Exception as e:
        logger.debug("specialty_id not found")
    reply_markup_raw = api_calls.get_days(block_id, 'group')
    if specialty_id != -1:
        reply_markup_raw.append([InlineKeyboardButton('<<', callback_data='specialty' + specialty_id)])
    reply_markup = InlineKeyboardMarkup(reply_markup_raw)

    edit_message_with_reply_markup(bot, update, text, reply_markup)


def get_chosen_day_schedule_callback_query(bot, update, user_data):
    msg = update.callback_query.data

    block_id = user_data['block_id']
    requested_type = user_data['requested_type']
    search_str = user_data['is_search']
    day_id = msg[3:]

    text = api_calls.get_schedule(block_id, day_id, requested_type)

    reply_markup_raw = [[InlineKeyboardButton('<<', callback_data=search_str + requested_type + block_id)]]
    reply_markup = InlineKeyboardMarkup(reply_markup_raw)

    edit_message_with_reply_markup(bot, update, text, reply_markup)


def get_teachers_callback_query(bot, update, user_data):
    text = 'Select the teacher:'

    msg = update.callback_query.data

    department_id = msg[10:]
    user_data['department_id'] = department_id

    reply_markup_raw = api_calls.get_teachers(department_id)
    reply_markup_raw.append([InlineKeyboardButton('<<', callback_data='departments_menu')])
    reply_markup = InlineKeyboardMarkup(reply_markup_raw)
    edit_message_with_reply_markup(bot, update, text, reply_markup)


def get_teacher_days_callback_query(bot, update, user_data):
    text = 'Select the day:'

    msg = update.callback_query.data

    teacher_id = msg[7:]
    user_data['block_id'] = teacher_id
    user_data['requested_type'] = 'teacher'
    user_data['is_search'] = ''
    department_id = user_data['department_id']

    reply_markup_raw = api_calls.get_days(teacher_id, 'teacher')
    reply_markup_raw.append([InlineKeyboardButton('<<', callback_data='department' + department_id)])
    reply_markup = InlineKeyboardMarkup(reply_markup_raw)

    edit_message_with_reply_markup(bot, update, text, reply_markup)


def get_search_callback_query(bot, update, user_data):
    text = 'Select the day:'

    msg = update.callback_query.data

    searched_type = msg[6:]
    print(searched_type)

    block_id = ''
    requested_type = ''

    if 'group' in searched_type:
        block_id = searched_type[5:]
        requested_type = 'group'

    elif 'teacher' in searched_type:
        block_id = searched_type[7:]
        requested_type = 'teacher'

    elif 'room' in searched_type:
        block_id = searched_type[4:]
        requested_type = 'room'

    user_data['block_id'] = block_id
    user_data['requested_type'] = requested_type
    user_data['is_search'] = 'search'

    search_text = user_data['search_text']
    reply_markup_raw = api_calls.get_days(block_id, requested_type)
    reply_markup_raw.append([InlineKeyboardButton('<<', callback_data='search_options_menu' + search_text)])
    reply_markup = InlineKeyboardMarkup(reply_markup_raw)

    edit_message_with_reply_markup(bot, update, text, reply_markup)


def get_free_rooms_callback_query(bot, update, user_data):
    msg = update.callback_query.data
    day_id = msg[8:]

    text = api_calls.get_free_room(day_id, user_data['access_token'])

    reply_markup_raw = [[InlineKeyboardButton('<<', callback_data="rooms_menu")]]
    reply_markup = InlineKeyboardMarkup(reply_markup_raw)

    edit_message_with_reply_markup(bot, update, text, reply_markup)

def cancel(bot, update):
  bot.send_message(chat_id=update.message.chat_id, text=bot_messages.cancel_response)
  return ConversationHandler.END
########################

def main():
    updater = Updater(sensitive.BOT_TOKEN)
    dispatcher = updater.dispatcher

    ### COMMAND HANDLERS 
    start_command_handler = CommandHandler('start', start, pass_user_data=True)
    # authorise_command_handler = CommandHandler('authorise', authorise, pass_user_data=True)
    help_command_handler = CommandHandler('help', help, pass_user_data=True)
    get_group_schedule_command_handler = CommandHandler('show_group_schedule', get_group_schedule, pass_user_data=True)
    get_my_group_schedule_command_handler = CommandHandler('my_group_schedule', get_my_group_schedule, pass_user_data=True)

    get_teacher_schedule_command_handler = CommandHandler('show_teacher_schedule', get_teacher_schedule, pass_user_data=True)
    get_free_rooms_command_handler = CommandHandler('show_free_cabinets', get_free_rooms, pass_user_data=True)
    feedback_command_handler = CommandHandler('feedback', feedback_command, pass_user_data=True)
    unknown_command_handler = MessageHandler(Filters.command, unknown_command, pass_user_data=True)

    authorise_handler = ConversationHandler(
        entry_points=[CommandHandler('authorise', authorise)],
        states={
            bot_states.PASSWORD: [MessageHandler(Filters.text, authorise_request, pass_user_data=True)]
        },
        fallbacks=[RegexHandler('[/]*', cancel)]
    )

    search_handler = ConversationHandler(
        entry_points=[CommandHandler('search', search, pass_user_data=True)],
        states={
            bot_states.SEARCH: [MessageHandler(Filters.text, search_request, pass_user_data=True)]
        },
        fallbacks=[RegexHandler('[/]*', cancel)]
    )

    set_my_group_handler = ConversationHandler(
        entry_points=[CommandHandler('set_my_group', set_my_group, pass_user_data=True)],
        states={
            bot_states.SET_GROUP: [MessageHandler(Filters.text, set_group_request, pass_user_data=True)]
        },
        fallbacks=[RegexHandler('[/]*', cancel)]
    )

    ### CALLBACK QUERY HANDLERS
    get_courses_callback_handler = CallbackQueryHandler(get_courses_callback_query,
                                                        pattern='^courses_menu')

    get_free_room_callback_handler = CallbackQueryHandler(get_free_room_callback_query,
                                                          pass_user_data=True,
                                                          pattern='^rooms_menu')

    get_departments_callback_handler = CallbackQueryHandler(get_departments_callback_query,
                                                            pattern='^departments_menu')

    get_search_results_callback_handler = CallbackQueryHandler(get_search_results_callback_query,
                                                               pattern='^search_options_menu')

    get_specialties_callback_handler = CallbackQueryHandler(get_specialties_callback_query,
                                                            pass_user_data=True,
                                                            pattern='^course')

    get_groups_callback_handler = CallbackQueryHandler(get_groups_callback_query,
                                                       pass_user_data=True,
                                                       pattern='^specialty')

    get_group_days_callback_handler = CallbackQueryHandler(get_group_days_callback_query,
                                                           pass_user_data=True,
                                                           pattern='^group')

    get_chosen_day_schedule_callback_handler = CallbackQueryHandler(get_chosen_day_schedule_callback_query,
                                                                    pass_user_data=True,
                                                                    pattern='^day')

    get_teachers_callback_handler = CallbackQueryHandler(get_teachers_callback_query,
                                                         pass_user_data=True,
                                                         pattern='^department')

    get_teacher_days_callback_handler = CallbackQueryHandler(get_teacher_days_callback_query,
                                                             pass_user_data=True,
                                                             pattern='^teacher')

    get_search_callback_handler = CallbackQueryHandler(get_search_callback_query,
                                                       pass_user_data=True,
                                                       pattern='^search')

    get_free_rooms_callback_handler = CallbackQueryHandler(get_free_rooms_callback_query,
                                                           pass_user_data=True,
                                                           pattern='^freeroom')

    bot_handlers = [
        authorise_handler,
        start_command_handler,
        help_command_handler,
        feedback_command_handler,
        get_group_schedule_command_handler,
        get_my_group_schedule_command_handler,
        get_teacher_schedule_command_handler,
        get_free_rooms_command_handler,
        search_handler,
        set_my_group_handler,
        get_courses_callback_handler,
        get_free_room_callback_handler,
        get_departments_callback_handler,
        get_search_results_callback_handler,
        get_specialties_callback_handler,
        get_groups_callback_handler,
        get_group_days_callback_handler,
        get_chosen_day_schedule_callback_handler,
        get_teachers_callback_handler,
        get_teacher_days_callback_handler,
        get_search_callback_handler,
        get_free_rooms_callback_handler,
        unknown_command_handler
    ]

    for handler in bot_handlers:
        dispatcher.add_handler(handler)

    updater.start_polling()


if __name__ == '__main__':
    main()
