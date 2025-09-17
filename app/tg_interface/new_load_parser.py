
from app.loads.load import Load, Stages
from app.logger import parser_logger


class LoadMessageParseError(RuntimeError):
    """Exception raised when load message parsing fails due to invalid format."""
    pass


class LoadMessageParser:
    """
    Parser for converting Telegram messages into Load objects.

    Handles parsing of both external and internal load messages with
    different formats and validation requirements.
    """

    @staticmethod
    def external(message: str) -> Load:
        """
        Parse an external load message into a Load object.

        Expected message format:
        0 new:external
        1 Кривой Рог            # Start place
        2 Днепр                 # Engage place
        3 Черновцы              # Clear place
        4 Яссы                  # Finish place
        5
        6 Козак Григорий        # Driver name
        7 +380501231212         # Driver phone
        8
        9 Client: +380953459607 # Client phone

        Args:
            message: Raw message string from Telegram.

        Returns:
            Load: Parsed external load object with 'history' stage.

        Raises:
            LoadMessageParseError: If message format is invalid or incomplete.
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
            parser_logger.error(f'Failed to parse load message: IndexError - {e}')
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
        Parse an internal load message into a Load object.

        Expected message format:
        0 new:internal
        1 Кривой Рог            # Start place
        2 Яссы                  # Finish place
        3
        4 Козак Григорий        # Driver name
        5 +380501231212         # Driver phone
        6
        7 Client: +380953459607 # Client phone

        Args:
            message: Raw message string from Telegram.

        Returns:
            Load: Parsed internal load object with 'history' stage.

        Raises:
            LoadMessageParseError: If message format is invalid or incomplete.
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
            parser_logger.error(f'Failed to parse load message: IndexError - {e}')
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
