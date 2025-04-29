from threading import Thread
from datetime import datetime
from app.lib.apis import telegramapi2
import time


class Scheduler(Thread):

    def __init__(self, loads, interface, sleeptime=4*3600, expirytime=4*3600):
        super().__init__()
        self.loads = loads
        self.interface = interface
        self.now = datetime.now()
        self.sleeptime = sleeptime
        self.expirytime = expirytime

    def run(self):

        try:
            while True:
                self.now = datetime.now()
                if not self.is_business_time():
                    time.sleep(self.sleeptime)
                    continue

                self.interface.render_loads(
                    loads=self.get_expired_loads(self.loads.get_active_loads(), self.expirytime),
                    message='Update now!'
                )
                time.sleep(self.sleeptime)

        except Exception as e:
            telegramapi2.send_developer(f'Scheduler thread died. Cause: {str(e)}', e)
            # TODO Rerun

    def is_business_time(self, start_hour=9, end_hour=18, business_days=(0, 1, 2, 3, 4)):
        """
        Проверяет, является ли текущее время бизнес-временем.
        :param start_hour: Час начала рабочего времени (по умолчанию 9)
        :param end_hour: Час окончания рабочего времени (по умолчанию 18)
        :param business_days: Кортеж с номерами рабочих дней (по умолчанию с понедельника по пятницу)
        :return: True, если текущее время в пределах рабочего времени, иначе False
        """
        return self.now.weekday() in business_days and start_hour <= self.now.hour < end_hour

    @staticmethod
    def has_hours_passed(dt1, dt2, duration):
        """
        Проверяет, прошло ли между двумя datetime-объектами указанное количество часов.
        :param dt1: Первый datetime-объект
        :param dt2: Второй datetime-объект
        :param duration: Количество времени для проверки
        :return: True, если прошло указанное количество часов или больше, иначе False
        """
        return abs((dt2 - dt1).total_seconds()) >= duration

    def get_expired_loads(self, loads, duration):
        """
        Проверяет, прошло ли между двумя datetime-объектами указанное количество часов.
        :param loads: list обьектов Load которые подлежат проверке
        :param duration: Срок годности обьектов Load
        :return: [Load, ] лист обьектов срок годности которых уже вышел или [] если таких нет
        """
        expired_loads = list()
        for load in loads:
            if self.has_hours_passed(load.last_update, self.now, duration):
                expired_loads.append(load)
        return expired_loads
