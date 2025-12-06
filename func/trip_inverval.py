from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd


class Weekday(Enum):
    """Дни недели для удобства использования"""

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


@dataclass
class TripInterval:
    """Класс для хранения интервала поездки"""

    departure_date: datetime
    return_date: datetime
    duration_days: int

    def __str__(self):
        return (
            f"Отправление: {self.departure_date.strftime('%Y-%m-%d %A')}, "
            f"Возвращение: {self.return_date.strftime('%Y-%m-%d %A')}, "
            f"Длительность: {self.duration_days} дней"
        )


def generate_trip_intervals(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    departure_days: Optional[List[int]] = None,
    return_days: Optional[List[int]] = None,
    desired_duration: int = 7,
    duration_variance: int = 0,
    max_intervals: int = 100,
) -> List[TripInterval]:
    """
    Генерирует список возможных временных интервалов для поездки.

    Args:
        start_date (Optional[datetime]): Начальная дата поиска (если None, используется текущая дата)
        end_date (Optional[datetime]): Конечная дата поиска (если None, используется start_date + 6 месяцев)
        departure_days (Optional[List[int]]): Дни недели для вылета (0-6, где 0 - понедельник)
        return_days (Optional[List[int]]): Дни недели для прилета (0-6, где 0 - понедельник)
        desired_duration (int): Желаемая длительность поездки в днях
        duration_variance (int): Допустимое отклонение от желаемой длительности (+- K дней)
        max_intervals (int): Максимальное количество возвращаемых интервалов

    Returns:
        List[TripInterval]: Список интервалов, удовлетворяющих условиям

    Example:
        # Поиск поездок на выходные (вылет в пятницу, возвращение в воскресенье)
        intervals = generate_trip_intervals(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 1),
            departure_days=[Weekday.FRIDAY.value],
            return_days=[Weekday.SUNDAY.value],
            desired_duration=2,
            duration_variance=1
        )
    """

    # Устанавливаем даты по умолчанию
    if start_date is None:
        start_date = datetime.now()

    if end_date is None:
        end_date = start_date + timedelta(days=180)  # 6 месяцев по умолчанию

    # Нормализуем время до 00:00:00
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

    # Преобразуем дни недели, если они заданы как Weekday enum
    if departure_days:
        departure_days = [
            day.value if isinstance(day, Weekday) else day for day in departure_days
        ]

    if return_days:
        return_days = [
            day.value if isinstance(day, Weekday) else day for day in return_days
        ]

    result_intervals = []

    # Генерируем все возможные даты вылета в заданном диапазоне
    current_date = start_date
    while current_date <= end_date:
        # Проверяем день вылета
        if departure_days is None or current_date.weekday() in departure_days:
            # Определяем минимальную и максимальную длительность
            min_duration = max(1, desired_duration - duration_variance)
            max_duration = desired_duration + duration_variance

            # Перебираем возможные длительности
            for duration in range(min_duration, max_duration + 1):
                return_date = current_date + timedelta(days=duration)

                # Проверяем, что дата возвращения в пределах диапазона
                if return_date > end_date:
                    continue

                # Проверяем день возвращения
                if return_days is None or return_date.weekday() in return_days:
                    interval = TripInterval(
                        departure_date=current_date,
                        return_date=return_date,
                        duration_days=duration,
                    )
                    result_intervals.append(interval)

                    # Ограничиваем количество результатов
                    if len(result_intervals) >= max_intervals:
                        return result_intervals

        current_date += timedelta(days=1)

    return result_intervals


def generate_trip_intervals_with_flexibility(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    departure_days: Optional[List[int]] = None,
    return_days: Optional[List[int]] = None,
    desired_duration: int = 7,
    duration_variance: int = 0,
    flex_days: int = 3,
    max_intervals: int = 50,
) -> List[TripInterval]:
    """
    Улучшенная версия с гибкостью по датам вылета и прилета.

    Args:
        flex_days (int): Количество дней гибкости для вылета/прилета
        Остальные параметры аналогичны generate_trip_intervals
    """

    if start_date is None:
        start_date = datetime.now()

    if end_date is None:
        end_date = start_date + timedelta(days=180)

    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

    result_intervals = []

    # Создаем расширенные списки дней с учетом гибкости
    if departure_days:
        flexible_departure_days = set()
        for day in departure_days:
            day_val = day.value if isinstance(day, Weekday) else day
            for offset in range(-flex_days, flex_days + 1):
                flexible_day = (day_val + offset) % 7
                flexible_departure_days.add(flexible_day)
        departure_days_list = list(flexible_departure_days)
    else:
        departure_days_list = None

    if return_days:
        flexible_return_days = set()
        for day in return_days:
            day_val = day.value if isinstance(day, Weekday) else day
            for offset in range(-flex_days, flex_days + 1):
                flexible_day = (day_val + offset) % 7
                flexible_return_days.add(flexible_day)
        return_days_list = list(flexible_return_days)
    else:
        return_days_list = None

    return generate_trip_intervals(
        start_date=start_date,
        end_date=end_date,
        departure_days=departure_days_list,
        return_days=return_days_list,
        desired_duration=desired_duration,
        duration_variance=duration_variance,
        max_intervals=max_intervals,
    )


# Примеры использования
if __name__ == "__main__":
    # Пример 1: Поездки на выходные в январе 2024
    # print("Пример 1: Поездки на выходные (пт-вс) в январе 2024")
    # intervals = generate_trip_intervals(
    #     start_date=datetime(2026, 1, 1),
    #     end_date=datetime(2026, 1, 31),
    #     departure_days=[Weekday.FRIDAY.value],  # Вылет в пятницу
    #     return_days=[Weekday.SUNDAY.value],  # Возвращение в воскресенье
    #     desired_duration=2,  # 2 дня
    #     duration_variance=1,  # +-1 день
    # )
    # print(intervals)

    # for i, interval in enumerate(intervals[:5], 1):  # Показываем первые 5 результатов
    #     print(f"{i}. {interval}")
    # print(f"... и еще {len(intervals) - 5} вариантов\n" if len(intervals) > 5 else "")

    # # Пример 2: Поездки на 7 дней с гибкостью
    # print("Пример 2: Поездки на 7±2 дня с вылетом в пн/вт и возвращением в пт/сб")
    intervals = generate_trip_intervals_with_flexibility(
        start_date=datetime(2026, 6, 1),
        end_date=datetime(2026, 8, 31),
        departure_days=[Weekday.MONDAY.value, Weekday.TUESDAY.value],
        return_days=[Weekday.FRIDAY.value, Weekday.SATURDAY.value],
        desired_duration=7,
        duration_variance=2,
        flex_days=1,
    )
    print(intervals)
    # for i, interval in enumerate(intervals[:5], 1):
    #     print(f"{i}. {interval}")
    # print(f"... и еще {len(intervals) - 5} вариантов\n" if len(intervals) > 5 else "")

    # # Пример 3: Любые поездки в течение месяца
    # print("Пример 3: Любые поездки длительностью 10±3 дня в июле 2024")
    # intervals = generate_trip_intervals(
    #     start_date=datetime(2024, 7, 1),
    #     end_date=datetime(2024, 7, 31),
    #     desired_duration=10,
    #     duration_variance=3,
    #     max_intervals=10,
    # )

    # for i, interval in enumerate(intervals, 1):
    #     print(f"{i}. {interval}")
