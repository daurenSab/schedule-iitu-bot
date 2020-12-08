import requests
import logging
import json
from telegram import InlineKeyboardButton
from model.scheduledata import ScheduleData

from core import bot_variables, sensitive

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger("api_calls")


def authorise(chat_id, password):
    status = 400
    try:
        user_obj = {'accountId': chat_id, 'password': password}
        headers = {'Content-Type': 'application/json'}
        response = requests.post(sensitive.AUTHORISE_URL, data=json.dumps(user_obj), headers=headers)
        return response
    except Exception as e:
        logger.error('Cannot update groupId, error: %s', e)

def get_courses():
    courses = [
        [InlineKeyboardButton('1 course', callback_data='course1')],
        [InlineKeyboardButton('2 course', callback_data='course2')],
        [InlineKeyboardButton('3 course', callback_data='course3')],
        [InlineKeyboardButton('4 course', callback_data='course4')]
    ]

    return courses


def get_free_room_days():
    days_name = []

    for idx, days in enumerate(bot_variables.days):
        index = idx + 1
        days_name.append([InlineKeyboardButton(days["en"], callback_data='freeroom{}'.format(index))])

    return days_name


def get_days(block_id, requested_type):
    group_data_raw = None
    days_name = []

    try:

        if requested_type == 'group':
            group_data_raw = requests.get('{}/?block_id={}'.format(sensitive.GET_TIMETABLE_BLOCK_URL, block_id))
        elif requested_type == 'teacher':
            group_data_raw = requests.get('{}/?teacher_id={}'.format(sensitive.GET_TIMETABLE_TEACHER_URL, block_id))
        elif requested_type == 'room':
            group_data_raw = requests.get('{}/?bundle_id={}'.format(sensitive.GET_TIMETABLE_ROOM_URL, block_id))

        group_data = group_data_raw.json()['timetable'].keys()
        days_name = [
            [InlineKeyboardButton(bot_variables.days[int(data) - 1]["en"], callback_data='day' + data)]
            for data in group_data
        ]

    except Exception as e:
        logger.warning('Error happened, while retrieving days list, error: %s', e)

    return days_name


def get_departments():
    departments_name = []

    try:

        departments = requests.get(sensitive.GET_DEPARTMENT_URL).json()

        departments_name = [
            [InlineKeyboardButton(department['name_en'], callback_data='department' + department['id'])]
            for department in departments['result']
        ]

    except Exception as e:

        logger.warning('Error happened, while retrieving departments list, error: %s', e)

    return departments_name


def get_teachers(department_id):
    teachers_data = []

    try:

        teachers = requests.get('{}/?department_id={}'.format(sensitive.GET_TEACHER_URL, department_id)).json()

        for teacher in teachers['result']:
            teachers_data.append([InlineKeyboardButton(teacher['name_en'], callback_data='teacher' + teacher['id'])])

    except Exception as e:

        logger.warning('Error happened, while retrieving teachers list, error: %s', e)

    return teachers_data


def get_specialties(course_id):
    specialty_names = []

    try:

        specialties_raw = requests.get('{}/?course={}'.format(sensitive.GET_SPECIALTY_URL, course_id))
        specialties = specialties_raw.json()

        specialty_names = []

        sis = None
        for specialty in specialties['result']:
            if specialty['name_en'][:3] == 'SIS':
                sis = [InlineKeyboardButton('SIS (Systems of Information Security)',
                                            callback_data='specialty' + specialty['id'])]
            else:
                specialty_names.append(
                    [InlineKeyboardButton(specialty['name_en'], callback_data='specialty' + specialty['id'])])

        specialty_names.append(sis)

    except Exception as e:

        logger.warning('Error happened, while retrieving specialty list, error: %s', e)

    return specialty_names


def get_groups(course_id, specialty_id):
    groups_name = []

    try:

        groups = requests.get(
            '{}/?course={}&specialty_id={}'.format(sensitive.GET_GROUP_URL, course_id, specialty_id)).json()

        for group in groups['result']:
            groups_name.append([InlineKeyboardButton(group['name_en'], callback_data='group' + group['id'])])

    except Exception as e:
        logger.warning('Error happened, while retrieving groups list, error: %s', e)

    return groups_name


def get_user_group_id(chat_id, token):
    group_id = -1
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': token
        }
        group_id_raw = requests.get('{}?id={}'.format(sensitive.USERS_GROUP_ID_URL, chat_id), headers=headers)
        group_id = group_id_raw.json()['groupId']
    except Exception as e:
        logger.warning('This user doesn\'t add group_id, error: %s', e)
    return group_id


def set_user_group_id(chat_id, group_id, token):
    status = 400
    try:
        user_obj = {'id': chat_id, 'groupId': int(group_id)}
        headers = {
            'Content-Type': 'application/json',
            'Authorization': token
        }
        response = requests.post(sensitive.USERS_GROUP_ID_URL, data=json.dumps(user_obj), headers=headers)
        response_json = response.json()
        status = response_json['status']
    except Exception as e:
        logger.error('Cannot update groupId, error: %s', e)
    return status


def get_free_room(day_id, token):
    message = ''

    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': token
        }
        room_data_raw = requests.get('{}?day={}'.format(sensitive.GET_FREE_ROOM_URL, day_id), headers=headers)
        room_data = room_data_raw.json()

        timetable = room_data['timetable']

        message += '<b>{}</b>\n\n'.format(bot_variables.days[int(day_id) - 1]["en"])

        for time, timetable_rooms in timetable.items():

            rooms = []
            for room in timetable_rooms:
                rooms.append(room)

            rooms.sort()
            rooms = ', '.join(rooms)

            start_time = bot_variables.times[int(time) - 1]["start_time"]
            end_time = bot_variables.times[int(time) - 1]["end_time"]
            message += '<b>{} - {}</b>\n{}\n\n'.format(
                start_time,
                end_time,
                rooms
            )

    except Exception as e:

        logger.warning('Error happened, while retrieving free rooms, error: %s', e)

    return message


def get_schedule(block_id, day_id, requested_type):
    group_data_raw = None
    message = ''

    try:

        if requested_type == 'group':
            group_data_raw = requests.get('{}/?block_id={}'.format(sensitive.GET_TIMETABLE_BLOCK_URL, block_id))
        elif requested_type == 'teacher':
            group_data_raw = requests.get('{}/?teacher_id={}'.format(sensitive.GET_TIMETABLE_TEACHER_URL, block_id))
        elif requested_type == 'room':
            group_data_raw = requests.get('{}/?bundle_id={}'.format(sensitive.GET_TIMETABLE_ROOM_URL, block_id))

        group_data = group_data_raw.json()
        timetable = group_data['timetable'][day_id]

        message += '<b>{}</b>\n\n'.format(bot_variables.days[int(day_id) - 1]["en"])

        for key, day_value in timetable.items():

            bundle = group_data['bundles'][day_value[0]['bundle_id']]

            room = []

            if bundle['type'] == 'room':
                room.append(bundle['0']['name_en'])
                room = ''.join(room)
            elif bundle['type'] == 'bundle':
                rooms_raw = group_data['bundles'][day_value[0]['bundle_id']]['name']
                for room_raw in rooms_raw:
                    room.append(room_raw['name_en'])
                room = ', '.join(room)

            subject_name = group_data['subjects'][day_value[0]['subject_id']]['subject_en']
            start_time = group_data['times'][day_value[0]['time_id']]['start_time'][:5]
            end_time = group_data['times'][day_value[0]['time_id']]['end_time'][:5]
            subject_type = group_data['subject_types'][day_value[0]['subject_type_id']]['subject_type_en']
            group_name = group_data['blocks'][day_value[0]['block_id']]['name']
            teacher_name = group_data['teachers'][day_value[0]['teacher_id']]['teacher_en']

            message += '<b>{}</b>\n{} - {}\n{}: {}\n{}\n{}\n\n'.format(
                subject_name,
                start_time,
                end_time,
                subject_type,
                group_name,
                teacher_name,
                room
            )

    except Exception as e:

        logger.warning('Error happened, while retrieving schedule, error: %s', e)

    return message


def get_result_of_search(search_text, json):
    results_data = []

    try:

        results_raw = requests.get('{}/?query={}&count=4'.format(sensitive.SEARCH_URL, search_text))
        results = results_raw.json()

        for result in results['result']:
            if json:
                results_data.append(ScheduleData(result['id'], result['name_en'], result['type'], result['matching']))
            else:
                results_data.append(
                    [InlineKeyboardButton(result['name_en'], callback_data='search' + result['type'] + result['id'])])

    except Exception as e:

        logger.warning('Error happened, while retrieving search results, error: %s', e)

    return results_data
