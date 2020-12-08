import os

from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

GET_SPECIALTY_URL = os.getenv('GET_SPECIALTY_URL')
GET_GROUP_URL = os.getenv('GET_GROUP_URL')
GET_TIMETABLE_BLOCK_URL = os.getenv('GET_TIMETABLE_BLOCK_URL')
GET_DEPARTMENT_URL = os.getenv('GET_DEPARTMENT_URL')
GET_TEACHER_URL = os.getenv('GET_TEACHER_URL')
GET_TIMETABLE_TEACHER_URL = os.getenv('GET_TIMETABLE_TEACHER_URL')
GET_TIMETABLE_ROOM_URL = os.getenv('GET_TIMETABLE_ROOM_URL')
SEARCH_URL = os.getenv('SEARCH_URL')
GET_FREE_ROOM_URL = os.getenv('GET_FREE_ROOM_URL')
USERS_GROUP_ID_URL = os.getenv('USERS_GROUP_ID_URL')
AUTHORISE_URL = os.getenv('AUTHORISE_URL')
