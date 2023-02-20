from httpx import AsyncClient, Response
from aiohttp import hdrs
from json import loads as loads_json
from pathlib import Path

from utils import read_json, save_json

from dataclasses import dataclass
from copy import deepcopy

from typing import Dict, List, Optional, Tuple, Union, Any


tables_list: List[str] = [
    "teachers",
    "subjects",
    "classes",
    "groups",
    "classrooms",
    "lessons",
    "cards",
    "periods",
    "daysdefs"
]


@dataclass
class Lesson:
    card_id: str
    lesson_id: str
    subjectid: str
    teacherids: List[str]
    groupids: List[str]
    durationperiods: int
    classroomidss: List[List[str]]
    day_id: str
    period: str


@dataclass
class TimeTableInfo:
    number: str
    text: str
    hash: str


class TimeTable:
    API_URL: str = "https://binomtt.sek.su{path}"

    INCORRECT_PERIODS: List[str] = [
        "",
        "-1"
    ]

    def __init__(self) -> None:
        self._http_session: AsyncClient = AsyncClient(
            default_encoding = "utf-8"
        )

    def table_to_dict(self, table_rows: List[dict]) -> Dict[str, dict]:
        result: Dict[str, dict] = {}

        for table_row in table_rows:
            result[table_row["id"]] = table_row

        return result

    def load_tables(self, tables: List[dict]) -> Dict[str, Dict[str, dict]]:
        results: Dict[str, Dict[str, dict]] = {}

        for table_data in tables:
            table_id: str = table_data["id"]

            if table_id in tables_list:
                results[table_id] = self.table_to_dict(
                    table_rows = table_data["data_rows"]
                )

        return results

    async def request(self, url: str, **kwargs) -> dict:
        response: Response = await self._http_session.get(
            url = url,
            **kwargs
        )

        return loads_json(
            s = response.text
        )

    async def _get_timetable(self, timetable_number: str) -> dict:
        return await self.request(
            url = self.API_URL.format(
                path = "/timetable/{timetable_number}.json".format(
                    timetable_number = timetable_number
                )
            )
        )

    async def get_active_timetables_info(self) -> List[TimeTableInfo]:
        response_json: dict = await self.request(
            url = self.API_URL.format(
                path = "/timetable/list.json"
            )
        )

        results: List[TimeTableInfo] = []

        for timetable in response_json["r"]["regular"]["timetables"]:
            timetable: dict

            if not timetable["hidden"]:
                results.append(
                    TimeTableInfo(
                        number = timetable["tt_num"],
                        text = timetable["text"],
                        hash = timetable["hash"]
                    )
                )

        return results

    async def get_timetables(self, timetable_number: str, class_ids: Optional[List[str]]=None) -> Tuple[Dict[str, Dict[str, Dict[str, Lesson]]], Dict[str, Dict[str, dict]]]:
        response_json: dict = await self._get_timetable(
            timetable_number = timetable_number
        )

        tables: Dict[str, Dict[str, dict]] = self.load_tables(
            tables = response_json["r"]["dbiAccessorRes"]["tables"]
        )

        val_id_daysdefs: Dict[str, str] = {}
        DEFAULT_DAY_LESSONS: Dict[str, Dict[str, Union[str, int]]] = {}

        for daysdef_id, daysdef in tables["daysdefs"].items():
            if daysdef["val"] == None:
                continue

            val_id_daysdefs[daysdef["vals"][0]] = daysdef_id
            DEFAULT_DAY_LESSONS[daysdef_id] = {}

        results: Dict[str, Dict[str, Dict[str, Dict[str, str]]]] = {}

        for card in tables["cards"].values():
            lesson: dict = tables["lessons"][card["lessonid"]]
            class_id: str = lesson["classids"][0]

            if class_ids:
                if class_id not in class_ids:
                    continue

            if card["period"] in self.INCORRECT_PERIODS:
                continue

            day_id: str = val_id_daysdefs[card["days"]]
            period_start = tables["periods"][card["period"]]

            if class_id not in results:
                results[class_id] = deepcopy(DEFAULT_DAY_LESSONS)

            results[class_id][day_id][period_start["period"]] = Lesson(
                card_id = card["id"],
                lesson_id = lesson["id"],
                subjectid = lesson["subjectid"],
                teacherids = lesson["teacherids"],
                groupids = lesson["groupids"],
                durationperiods = lesson["durationperiods"],
                classroomidss = card["classroomids"],
                day_id = day_id,
                period = card["period"]
            )

        return results, tables

    def sort(self, class_timetable: Dict[str, Dict[str, Lesson]], not_lesson: Optional[bool]=False) -> Dict[str, Dict[str, Lesson]]:
        for key in class_timetable.keys():
            key: dict

            if not_lesson:
                class_timetable[key] = dict(
                    sorted(
                        class_timetable[key].items(),
                        key = lambda kv: (
                            int(kv[0])
                            if kv[0][0] != "*"
                            else
                            int(kv[0][1:])
                        )
                    )
                )

            else:
                class_timetable[key] = dict(
                    sorted(
                        class_timetable[key].items(),
                        key = lambda kv: (
                            int(kv[1].period)
                            if kv[1]
                            else
                            0
                        )
                    )
                )

        return dict(
            sorted(
                class_timetable.items(),
                key = lambda kv: (
                    int(kv[0])
                    if kv[0][0] != "*"
                    else
                    int(kv[0][1:])
                )
            )
        )

    async def close(self) -> None:
        await self._http_session.aclose()
