from typing import List


TEXTS: dict = {
    "edupage": {
        "timetable": {
            "updated": "Распиания обновились.\nПожалуйста, сделай выбор снова:",
            "inline_title": "Расписание {class_name} класса",
            "default": "Расписание \"<b>{class_name}</b>\" класса:\n\n{daysdefs}\n\n<a href=\"{channel_url}\">Binom TimeTable</a> | <b>{class_name}</b>",
            "daysdef": "{daysdef}:\n{lessons}",
            "lesson": {
                "default": "<b>{period}</b> (<i>{start_time}</i> - <i>{end_time}</i>) - {additional}",
                "additional": {
                    "default": "{subject} (<i>{teachers}</i>) - <i>{groups}</i> - [<i>{classrooms}</i>]",
                    "unknown": "Ничего"
                }
            }
        },
        "classrooms_free": {
            "choose_timetable": "Выберите смену:",
            "choose_day": "Выберите день:\n({timetable_i}-я смена)",
            "choose_period": "Выберите урок:\n({timetable_i}-я смена, {day_name})",
            "default": "Свободные кабинеты:\n({timetable_i}-я смена, {day_name}, {period_i}-й урок)\n\n{classrooms}",
        }
    },
    "admins": {
        "new_timetables": {
            "default": "Обновление расписаний приостановлено.\nСписок новых расписаний:\n{timetables}",
            "timetable": "<code>{number}</code> - <i>{text}</i> (<code>{hash}</code>)"
        },
        "unknown_error": "#error\nНеизвестная ошибка:\n<code>{traceback}</code>\n\n<code>{update}</code>"
    },
    "start": "Привет!\nЯ выдаю расписания для всех классов.\nВыберите Ваш класс:",
    "keyboards": {
        "classrooms_free": {
            "default": "Свободные кабинеты",
            "timetable": "{i}-я смена",
            "day": "{day_name}",
            "period": "{i}-й урок"
        },
        "timetable_inline": "Изменения",
        "prev": "⬅️",
        "next": "➡️"
    },
    "null": "⁣"
}

ALPHABET: List[str] = [
    "А",
    "Ә",
    "Б",
    "В",
    "Г",
    "Ғ",
    "Д",
    "Е",
    "Ё",
    "Ж",
    "З",
    "И",
    "Й",
    "К",
    "Қ",
    "Л",
    "М",
    "Н",
    "Ң",
    "О",
    "Ө",
    "П",
    "Р",
    "С",
    "Т",
    "У",
    "Ұ",
    "Ү",
    "Ф",
    "Х",
    "Һ",
    "Ц",
    "Ч",
    "Ш",
    "Щ",
    "Ъ",
    "Ы",
    "І",
    "Ь",
    "Э",
    "Ю",
    "Я"
]
