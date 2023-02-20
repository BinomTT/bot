from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from itertools import islice

from models import Class

from typing import Any, Iterator, Dict, Callable, List, Union


def chunks(data: dict, size: int):
    data_iter: Iterator = iter(data)

    for _ in range(0, len(data), size):
        yield {
            k: data[k]
            for k in islice(data_iter, size)
        }


class Keyboards:
    def __init__(self, texts: dict, classes: Dict[str, Class], per_page_limit: int) -> None:
        self._texts: dict = texts
        self._per_page_limit: int = per_page_limit

        self._max_classes_page: int = 0

        self.classes: List[InlineKeyboardMarkup] = []

        self.update_classes(
            classes = classes
        )

    def update_classes(self, classes: Dict[str, Class]) -> None:
        self.classes.clear()

        _classes: List[Any] = list(chunks(
            data = classes,
            size = self._per_page_limit
        ))

        self._max_classes_page = len(_classes) - 1

        for page, __classes in enumerate(_classes):
            page: int
            __classes: Dict[str, Class]

            class_markup: InlineKeyboardMarkup = InlineKeyboardMarkup(
                row_width = 2
            )

            for class_name, class_ in __classes.items():
                class_name: str
                class_: Class

                class_markup.insert(
                    InlineKeyboardButton(
                        text = class_name,
                        callback_data = "timetable_class_{class_id}_{timetable_number}".format(
                            class_id = class_.id,
                            timetable_number = class_.timetable_number
                        )
                    )
                )

            have_prev: bool = page > 0

            if have_prev:
                class_markup.add(
                    InlineKeyboardButton(
                        text = self._texts["prev"],
                        callback_data = "timetable_page_{page}".format(
                            page = page - 1
                        )
                    )
                )

            if self._max_classes_page > page:
                if have_prev:
                    func = class_markup.insert
                else:
                    func = class_markup.add

                func(
                    InlineKeyboardButton(
                        text = self._texts["next"],
                        callback_data = "timetable_page_{page}".format(
                            page = page + 1
                        )
                    )
                )

            class_markup.add(
                InlineKeyboardButton(
                    text = self._texts["classrooms_free"]["default"],
                    callback_data = "classrooms_free"
                )
            )

            self.classes.append(class_markup)

    def inline_timetable(self, channel_url: str) -> str:
        return InlineKeyboardMarkup(
            inline_keyboard = [[
                InlineKeyboardButton(
                    text = self._texts["timetable_inline"],
                    url = channel_url
                )
            ]]
        )

    def classrooms_free_select_timetable(self, timetable_numbers: List[str]) -> InlineKeyboardMarkup:
        markup: InlineKeyboardMarkup = InlineKeyboardMarkup()

        for i, timetable_number in enumerate(timetable_numbers, 1):
            markup.add(
                InlineKeyboardButton(
                    text = self._texts["classrooms_free"]["timetable"].format(
                        i = i
                    ),
                    callback_data = "classrooms_free_{timetable_number}".format(
                        timetable_number = timetable_number
                    )
                )
            )

        return markup

    def classrooms_free_select_day(self, timetable_number: str, days: Dict[str, str]) -> InlineKeyboardMarkup:
        markup: InlineKeyboardMarkup = InlineKeyboardMarkup()

        for day_id, day_name in days.items():
            markup.add(
                InlineKeyboardButton(
                    text = self._texts["classrooms_free"]["day"].format(
                        day_name = day_name
                    ),
                    callback_data = "classrooms_free_{timetable_number}_{day_id}".format(
                        timetable_number = timetable_number,
                        day_id = day_id
                    )
                )
            )

        return markup

    def classrooms_free_select_period(self, timetable_number: str, day_id: str, periods: Dict[str, str]) -> InlineKeyboardMarkup:
        markup: InlineKeyboardMarkup = InlineKeyboardMarkup()

        for period_id, period_name in periods.items():
            markup.add(
                InlineKeyboardButton(
                    text = self._texts["classrooms_free"]["period"].format(
                        i = period_name
                    ),
                    callback_data = "classrooms_free_{timetable_number}_{day_id}_{period_id}".format(
                        timetable_number = timetable_number,
                        day_id = day_id,
                        period_id = period_id
                    )
                )
            )

        return markup
