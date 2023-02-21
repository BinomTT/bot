from aiogram import Bot, Dispatcher, types, exceptions
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler

from copy import deepcopy
from dataclasses import asdict
from asyncio import sleep
from hashlib import md5
from traceback import format_exc

from edupage import Lesson, TimeTableInfo, TimeTable
from models import Class
from keyboards import Keyboards
from db import User, init_db
from utils import chunker
from basic_data import TEXTS, ALPHABET
from config import config

from typing import Dict, List, Optional, Tuple, Union


keyboards: Keyboards


bot: Bot = Bot(
    token = config.bot_token,
    parse_mode = types.ParseMode.HTML
)

dp: Dispatcher = Dispatcher(
    bot = bot
)


timetable_api: TimeTable = TimeTable()


timetable_numbers: List[str] = []
timetable_hashes: List[str] = []


class_ids: List[str] = []
class_names: Dict[str, Tuple[str, str]] = {}

timetable_classes: Dict[str, Class] = {}

tables: Dict[str, Dict[str, Dict[str, dict]]] = {}

class_name_from_timetable_and_id: Dict[str, Dict[str, str]] = {}
classes_timetables: Dict[str, Dict[str, Dict[str, Dict[str, Dict[str, str]]]]] = {}


class UsersMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        super(UsersMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict) -> None:
        if message.chat.type != types.ChatType.PRIVATE:
            raise CancelHandler

        user_id: int = message.chat.id

        if not await User.find_one(
            User.user_id == user_id
        ):
            await User(
                user_id = user_id
            ).insert()


def get_timetable_for_class(timetable_number: Optional[str]=None, class_id: Optional[str]=None, class_name: Optional[str]=None) -> str:
    if (not timetable_number and not class_id) and not class_name:
        raise ValueError("Incorrect arguments.")

    if not class_name:
        class_name: str = class_name_from_timetable_and_id[timetable_number][class_id]

    class_: Class = timetable_classes[class_name]

    if not class_id:
        class_id = class_.id

    if not timetable_number:
        timetable_number = class_.timetable_number

    class_timetable: Dict[str, Dict[str, Dict[str, str]]] = classes_timetables[timetable_number][class_id]

    tables_: Dict[str, Dict[str, dict]] = tables[timetable_number]

    daysdefs_lessons: Dict[str, Dict[str, str]] = {}

    null_timetable: Dict[str, Union[Dict[str, Union[str, int]], None]] = {
        period_id: None
        for period_id in tables_["periods"].keys()
    }

    for day_id in class_timetable.keys():
        for period_id, lesson_dict in class_timetable[day_id].items():
            if not lesson_dict:
                daysdefs_lessons[day_id][period_id] = TEXTS["edupage"]["timetable"]["lesson"]["default"].format(
                    period = period["name"],
                    start_time = period["starttime"],
                    end_time = period["endtime"],
                    additional = TEXTS["edupage"]["timetable"]["lesson"]["additional"]["unknown"]
                )

                continue

            lesson: Optional[Lesson] = Lesson(**lesson_dict)

            if day_id not in daysdefs_lessons:
                daysdefs_lessons[day_id] = deepcopy(null_timetable)

            int_lesson_period: int = int(lesson.period)

            for i in range(lesson.durationperiods):
                period_id: str = str(int_lesson_period + i)
                period: dict = tables_["periods"][period_id]

                daysdefs_lessons[day_id][period_id] = TEXTS["edupage"]["timetable"]["lesson"]["default"].format(
                    period = period["name"],
                    start_time = period["starttime"],
                    end_time = period["endtime"],
                    additional = TEXTS["edupage"]["timetable"]["lesson"]["additional"]["default"].format(
                        subject = tables_["subjects"][lesson.subjectid]["name"].strip(),
                        teachers = ", ".join([tables_["teachers"][teacher_id]["lastname"].strip() for teacher_id in lesson.teacherids]),
                        groups = ", ".join([tables_["groups"][group_id]["name"] for group_id in lesson.groupids]).lower(),
                        classrooms = (
                            ", ".join([tables_["classrooms"][classroom_id]["name"].strip().split(" ", 1)[0] for classroom_id in lesson.classroomidss if classroom_id])
                            if lesson.classroomidss and lesson.classroomidss[0] != ""
                            else
                            ", ".join([" | ".join([tables_["classrooms"][classroom_id]["name"].strip().split(" ", 1)[0] for classroom_id in classroom_idss]) for classroom_idss in lesson.classroomidss])
                        )
                    )
                )

    daysdefs_lessons = timetable_api.sort(
        class_timetable = daysdefs_lessons,
        not_lesson = True
    )

    daysdefs_lessons__: Dict[str, List[str]] = {}

    for day_id in daysdefs_lessons.keys():
        for period_id, value in daysdefs_lessons[day_id].items():
            if day_id not in daysdefs_lessons__:
                daysdefs_lessons__[day_id] = []

            if value:
                daysdefs_lessons__[day_id].append(value)

            else:
                period: dict = tables_["periods"][period_id]

                daysdefs_lessons__[day_id].append(
                    TEXTS["edupage"]["timetable"]["lesson"]["default"].format(
                        period = period["name"],
                        start_time = period["starttime"],
                        end_time = period["endtime"],
                        additional = TEXTS["edupage"]["timetable"]["lesson"]["additional"]["unknown"]
                    )
                )

    return TEXTS["edupage"]["timetable"]["default"].format(
        class_name = class_name,
        daysdefs = "\n\n".join([
            TEXTS["edupage"]["timetable"]["daysdef"].format(
                daysdef = tables_["daysdefs"][day_id]["name"],
                lessons = "\n".join(lessons)
            )
            for day_id, lessons in daysdefs_lessons__.items()
        ]),
        channel_url = config.channel_url
    )


@dp.inline_handler(lambda inline_query: True)
async def inline_handler(inline_query: types.InlineQuery) -> None:
    class_name: str = inline_query.query.strip()

    if not class_name:
        await inline_query.answer(
            results = [],
            cache_time = config.inline_cache_time
        )

        return

    class_name = class_name.upper()

    if class_name not in class_names:
        await inline_query.answer(
            results = [],
            cache_time = config.inline_cache_time
        )

        return

    timetable_number: str
    class_id: str

    timetable_number, class_id = class_names[class_name]

    await inline_query.answer(
        results = [
            types.InlineQueryResultArticle(
                id = md5(
                    string = class_id.encode("utf-8")
                ).hexdigest(),
                title = TEXTS["edupage"]["timetable"]["inline_title"].format(
                    class_name = class_name
                ),
                input_message_content = types.InputTextMessageContent(
                    message_text = get_timetable_for_class(
                        timetable_number = timetable_number,
                        class_id = class_id
                    ),
                    parse_mode = bot.parse_mode
                )
            )
        ],
        cache_time = config.inline_cache_time
    )


@dp.callback_query_handler()
async def callback_query_handler(callback_query: types.CallbackQuery) -> None:
    await callback_query.answer()

    args: List[str] = callback_query.data.split("_")
    args_len: int = len(args)

    if args[0] == "timetable":
        if args_len == 2 or args[1] == "class":
            class_id: str = (
                args[1]
                if args_len == 2
                else
                args[2]
            )

            if args[3] not in timetable_numbers:
                try:
                    await callback_query.message.delete()

                except exceptions.MessageCantBeDeleted:
                    await callback_query.message.edit_text(
                        text = TEXTS["null"]
                    )

                await callback_query.message.answer(
                    text = TEXTS["edupage"]["timetable"]["updated"],
                    reply_markup = keyboards.classes[0]
                )

                return

            timetable_index: int = (
                0
                if args_len != 4
                else
                timetable_numbers.index(args[3])
            )

            timetable_number: str = timetable_numbers[timetable_index]

            await callback_query.message.answer(
                text = get_timetable_for_class(
                    timetable_number = timetable_number,
                    class_id = class_id
                ),
                disable_web_page_preview = True
            )

        elif args[1] == "page":
            page: int = int(args[2])

            classes_markup: types.InlineKeyboardMarkup

            if page > keyboards._max_classes_page:
                classes_markup = keyboards.classes[0]
            else:
                classes_markup = keyboards.classes[page]

            await callback_query.message.edit_reply_markup(
                reply_markup = classes_markup
            )

    elif args[0] == "classrooms":
        if args[1] == "free":
            if args_len == 2:
                await callback_query.message.edit_text(
                    text = TEXTS["edupage"]["classrooms_free"]["choose_timetable"],
                    reply_markup = keyboards.classrooms_free_select_timetable(
                        timetable_numbers = timetable_numbers
                    )
                )

                return

            if args[2] not in timetable_numbers:
                try:
                    await callback_query.message.delete()

                except exceptions.MessageCantBeDeleted:
                    await callback_query.message.edit_text(
                        text = TEXTS["null"]
                    )

                await callback_query.message.answer(
                    text = TEXTS["edupage"]["timetable"]["updated"],
                    reply_markup = keyboards.classrooms_free_select_timetable(
                        timetable_numbers = timetable_numbers
                    )
                )

                return

            timetable_index: int = timetable_numbers.index(args[2])
            timetable_number: str = timetable_numbers[timetable_index]

            if args_len == 3:
                await callback_query.message.edit_text(
                    text = TEXTS["edupage"]["classrooms_free"]["choose_day"].format(
                        timetable_i = timetable_index + 1
                    ),
                    reply_markup = keyboards.classrooms_free_select_day(
                        timetable_number = timetable_number,
                        days = {
                            day_id: day_data["name"]
                            for day_id, day_data in tables[timetable_number]["daysdefs"].items()
                            if day_data["val"] != None
                        }
                    )
                )

                return

            elif args_len == 4:
                await callback_query.message.edit_text(
                    text = TEXTS["edupage"]["classrooms_free"]["choose_period"].format(
                        timetable_i = timetable_index + 1,
                        day_name = tables[timetable_number]["daysdefs"][args[3]]["name"]
                    ),
                    reply_markup = keyboards.classrooms_free_select_period(
                        timetable_number = timetable_number,
                        day_id = args[3],
                        periods = {
                            period_id: period_data["period"]
                            for period_id, period_data in tables[timetable_number]["periods"].items()
                        }
                    )
                )

                return

            day_id: str = args[3]
            period_id: str = args[4]

            daysdef_val: str = tables[timetable_number]["daysdefs"][day_id]["vals"][0]

            not_busy_classrooms: Dict[str, str] = {}

            for classroom_id, classroom_data in tables[timetable_number]["classrooms"].items():
                classroom_name: str = classroom_data["name"]

                not_busy_classrooms[classroom_id] = classroom_name.strip()

            for card in tables[timetable_number]["cards"].values():
                card: dict

                if card["period"] in timetable_api.INCORRECT_PERIODS or card["period"] != period_id or card["days"] != daysdef_val:
                    continue

                lesson: dict = tables[timetable_number]["lessons"][card["lessonid"]]

                for classroom_idss in lesson["classroomidss"]:
                    for classroom_id in classroom_idss:
                        if classroom_id is not None and classroom_id in not_busy_classrooms:
                            del not_busy_classrooms[classroom_id]

            not_busy_classrooms = dict(sorted(
                not_busy_classrooms.items(),
                key = lambda item: item[1],
                reverse = True
            ))

            classrooms_: List[str] = []

            for chunk in chunker(
                items = list(not_busy_classrooms.values()),
                n = 3
            ):
                chunk: List[str]

                classrooms_.append(
                    ", ".join(chunk)
                )

            await callback_query.message.answer(
                text = TEXTS["edupage"]["classrooms_free"]["default"].format(
                    timetable_i = timetable_index + 1,
                    day_name = tables[timetable_number]["daysdefs"][args[3]]["name"],
                    period_i = tables[timetable_number]["periods"][period_id]["period"],
                    classrooms = "\n".join(classrooms_)
                )
            )


@dp.message_handler(commands=["start"])
async def bot_start_command_handler(message: types.Message) -> None:
    await message.answer(
        text = TEXTS["start"],
        reply_markup = keyboards.classes[0]
    )


async def timetable_load() -> None:
    global classes_timetables, tables, keyboards

    for timetable_number in timetable_numbers:
        classes_timetables_, tables_ = await timetable_api.get_timetables(
            timetable_number = timetable_number
        )

        tables[timetable_number] = tables_

        for class_id in classes_timetables_.keys():
            for day_id in classes_timetables_[class_id].keys():
                for period_id, lesson in classes_timetables_[class_id][day_id].items():
                    if lesson:
                        classes_timetables_[class_id][day_id][period_id] = asdict(lesson)

        classes_timetables[timetable_number] = classes_timetables_


def _sort_classes(item: Tuple[str, Class]) -> Tuple[int, int]:
    grade, letter = item[0].split()
    return int(grade), ALPHABET.index(letter.replace("*", "", 1))

def load_classes(classes: Dict[str, Class]) -> Dict[str, Class]:
    global tables, classes_timetables, class_name_from_timetable_and_id

    for timetable_number in timetable_numbers:
        for class_id, class__ in tables[timetable_number]["classes"].items():
            class_name: str = class__["short"].strip()

            class_: Class

            if class_name not in classes:
                class_ = Class(
                    id = class_id,
                    name = class_name,
                    timetable_number = timetable_number
                )

                class_name_from_timetable_and_id[timetable_number][class_id] = class_name

                classes[class_name] = class_

            elif classes[class_name].timetable_number != timetable_number:
                class_ = classes[class_name]

                class_name_from_timetable_and_id[timetable_number][class_id] = class_name

                class_.timetable_number = timetable_number
                classes[class_name] = class_

    classes = dict(sorted(
        classes.items(),
        key = _sort_classes
    ))

    return classes


async def timetables_checker() -> None:
    while True:
        try:
            timetable_infos: List[TimeTableInfo] = await timetable_api.get_active_timetables_info()
            updated_timetable_infos_list: List[TimeTableInfo] = []

            for timetable_info in timetable_infos:
                if timetable_info.hash not in timetable_hashes:
                    updated_timetable_infos_list.append(timetable_info)

            if updated_timetable_infos_list:
                await errors_handler(
                    updated_timetable_infos_list = updated_timetable_infos_list
                )

                return

        except KeyboardInterrupt:
            return

        except Exception as ex:
            await errors_handler(
                exception = ex
            )

        await sleep(
            delay = config.checker_timeout
        )


async def admins_notify(text: str) -> None:
    for admin in config.admins:
        admin: int

        try:
            await bot.send_message(
                chat_id = admin,
                text = text
            )

        except exceptions.TelegramAPIError:
            pass


@dp.errors_handler()
async def errors_handler(update: Optional[types.Update]=None, exception: Optional[Exception]=None, updated_timetable_infos_list: Optional[List[TimeTableInfo]]=None) -> bool:
    if updated_timetable_infos_list:
        await admins_notify(
            text = TEXTS["admins"]["new_timetables"]["default"].format(
                timetables = "\n".join([
                    TEXTS["admins"]["new_timetables"]["timetable"].format(
                        number = timetable_info.number,
                        text = timetable_info.text,
                        hash = timetable_info.hash
                    )
                    for timetable_info in updated_timetable_infos_list
                ])
            )
        )

        return True

    type_: object = type(exception)

    if type_ == exceptions.InvalidQueryID:
        return True

    await admins_notify(
        text = TEXTS["admins"]["unknown_error"].format(
            traceback = format_exc(),
            update = (
                update.as_json()
                if update
                else
                ""
            )
        )
    )

    return True


dp.middleware.setup(
    middleware = UsersMiddleware()
)


async def on_startup() -> bool:
    global keyboards, timetable_numbers, timetable_hashes, class_name_from_timetable_and_id, timetable_classes

    await init_db(
        db_uri = config.db_uri,
        db_name = config.db_name
    )

    for timetables_info in await timetable_api.get_active_timetables_info():
        timetable_number: str = timetables_info.number

        timetable_numbers.append(timetable_number)
        timetable_hashes.append(timetables_info.hash)

        class_name_from_timetable_and_id[timetable_number] = {}
        classes_timetables[timetable_number] = {}

    try:
        await timetable_load()

    except Exception as ex:
        await errors_handler(
            update = None,
            exception = ex
        )

        return False

    timetable_classes = load_classes(
        classes = timetable_classes
    )

    keyboards = Keyboards(
        texts = TEXTS["keyboards"],
        classes = timetable_classes,
        per_page_limit = config.per_page_limit
    )

    return True


async def on_shutdown() -> None:
    await timetable_api.close()

    await dp.storage.close()
    await dp.storage.wait_closed()

    if bot._session:
        await bot._session.close()


async def main() -> None:
    from asyncio import gather

    startup_status_ok: bool = await on_startup()

    if not startup_status_ok:
        return

    await gather(
        timetables_checker(),
        dp.start_polling()
    )


if __name__ == "__main__":
    from asyncio import AbstractEventLoop, new_event_loop, set_event_loop

    loop: AbstractEventLoop = new_event_loop()

    set_event_loop(
        loop = loop
    )

    try:
        loop.run_until_complete(
            main()
        )

    except KeyboardInterrupt:
        pass

    finally:
        loop.run_until_complete(
            on_shutdown()
        )
