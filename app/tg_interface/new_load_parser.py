
from app.loads.load import Load, Stages


class LoadMessageParseError(RuntimeError):
    pass


class LoadMessageParser:

    @staticmethod
    def external(message: str) -> Load:
        """
        0 new:external
        1 Кривой Рог
        2 Днепр
        3 Черновцы
        4 Яссы
        5
        6 Козак Григорий
        7 +380501231212
        8
        9 Client: +380953459607
        """
        try:
            lines = message.strip().split('\n')
            start_place = lines[1].strip()
            engage_place = lines[2].strip()
            clear_place = lines[3].strip()
            finish_place = lines[4].strip()
            driver_name = lines[6].strip()
            driver_num = lines[7].strip().replace('+', '')
            client_num = lines[9].replace('Client: ', '').strip().replace('+', '')
            if not all(
                (
                    start_place,
                    engage_place,
                    clear_place,
                    finish_place,
                    driver_name,
                    driver_num,
                    client_num
                )
            ):
                raise LoadMessageParseError(message)
        except IndexError as e:
            raise LoadMessageParseError(message) from e

        return Load(
            type='external',
            stage='history',
            stages=Stages(
                start=start_place,
                engage=engage_place,
                clear=clear_place,
                finish=finish_place
            ),
            client_num=client_num,
            driver_name=driver_name,
            driver_num=driver_num
        )

    @staticmethod
    def internal(message: str) -> Load:
        """
            0 new:external
            1 Кривой Рог
            2 Днепр
            3 Черновцы
            4 Яссы
            5
            6 Козак Григорий
            7 +380501231212
            8
            9 Client: +380953459607
            """
        try:
            lines = message.strip().split('\n')
            start_place = lines[1].strip()
            finish_place = lines[2].strip()
            driver_name = lines[4].strip()
            driver_num = lines[5].strip().replace('+', '')
            client_num = lines[7].replace('Client: ', '').strip().replace('+', '')

            if not all(
                    (
                            start_place,
                            finish_place,
                            driver_name,
                            driver_num,
                            client_num
                    )
            ):
                raise LoadMessageParseError(message)
        except IndexError as e:
            raise LoadMessageParseError(message) from e

        return Load(
            type='internal',
            stage='history',
            stages=Stages(
                start=start_place,
                engage=None,
                clear=None,
                finish=finish_place
            ),
            client_num=client_num,
            driver_name=driver_name,
            driver_num=driver_num
        )
