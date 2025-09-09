
from typing import Optional, Any
from app.loads.load import Load, Stages
from psycopg import AsyncConnection
from psycopg.errors import DataError, IntegrityError
from app.loads import queries

# TMP_PG_RUN_CMD = 'docker run --name dev-postgres -e POSTGRES_DB=pstgrs -e POSTGRES_USER=olvr -e POSTGRES_PASSWORD=msVWXP -p 127.0.0.1:5432:5432 -d postgres'
# TODO REMOVE TMP_PG_RUN_CMD AND SET UP DOCKER COMPOSE
# TODO DO NOT FORGET TO ADD PERSISTENT VOLUME



class Loads:

    def __init__(self, db_connection_url: str):

        self.db_connection_url = db_connection_url
        self.connection: Optional[AsyncConnection] = None

    async def __aenter__(self):
        self.connection = await AsyncConnection.connect(self.db_connection_url)
        await self.initialise_db_if_empty()

        # active = await self.get_actives()
        # historical = await self.get_historicals()
        # await self.add(active[0])
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            await self.connection.close()

    async def get_load_by_id(self, load_id: str) -> Optional[Load]:
        if not isinstance(load_id, str):
            raise TypeError('load_id must be a string')
        rows = await self.execute_query(
            queries.CTE_SELECT_ALL_LOADS +
            queries.FILTER_SINGLE_LOAD,
            load_id
        )
        if rows is not None and len(rows) > 0:
            return self._convert_cte_row_to_load(rows[0])
        return None

    async def get_qty_of_actives(self):
        rows = await self.execute_query(query=queries.COUNT_ACTIVE_LOADS)
        return rows[0][0]

    async def get_qty_of_historicals(self):
        rows = await self.execute_query(query=queries.COUNT_HISTORICAL_LOADS)
        return rows[0][0]

    async def get_actives(self) -> list[Load]:
        return await self._get_loads_by_fq(filter_query=queries.FILTER_ACTIVE_LOADS)

    async def get_historicals(self) -> list[Load]:
        return await self._get_loads_by_fq(filter_query=queries.FILTER_HISTORY_LOADS)

    async def add(self, load: Load) -> str:

        client_id = await self._insert_client(load.client_num)
        driver_id = await self._insert_driver(
            name=load.driver_name,
            phone_num=load.driver_num
        )
        load_id = await self._insert_load(
            load=load,
            client_id=client_id,
            driver_id=driver_id
        )
        return load_id

    async def update(self, load: Load) -> str:

        return await self._update_load(load)

    async def _get_loads_by_fq(self, filter_query: str) -> list[Load]:
        rows = await self.execute_query(query=queries.CTE_SELECT_ALL_LOADS + filter_query)
        loads = []
        for row in rows:
            loads.append(
                self._convert_cte_row_to_load(row)
            )
        return loads

    async def _insert_client(self, phone_number: str) -> int:
        try:
            rows = await self.execute_query(queries.INSERT_CLIENT, phone_number)
            return rows[0][0]
        except (DataError, IntegrityError, IndexError) as e:
            raise ValueError from e

    async def _insert_driver(self, name: str, phone_num: str) -> int:
        try:
            rows = await self.execute_query(queries.INSERT_DRIVER, name, phone_num)
            return rows[0][0]
        except (DataError, IntegrityError, IndexError) as e:
            raise ValueError from e

    async def _insert_load(self, load: Load, client_id, driver_id) -> str:
        try:
            rows = await self.execute_query(
                queries.INSERT_LOAD,
                load.load_id,
                load.last_update,
                load.load_type,
                client_id,
                driver_id,
                load.stage,
                load.stages.start,
                load.stages.engage,
                load.stages.clear,
                load.stages.finish
            )
            return rows[0][0]
        except (DataError, IntegrityError, IndexError) as e:
            raise ValueError from e

    async def _update_load(self, load: Load) -> str:
        try:
            rows = await self.execute_query(
                queries.UPDATE_LOAD,
                load.last_update,
                load.stage,
                load.load_id
            )
            return rows[0][0]
        except (DataError, IntegrityError, IndexError) as e:
            raise ValueError('Given load is not present in the database. '
                             'Try first add it') from e

    @staticmethod
    def _convert_cte_row_to_load(row) -> Load:
        return Load(
            type=row[3],
            stage=row[7],
            stages=Stages(
                start=row[8],
                engage=row[9],
                clear=row[10],
                finish=row[11]
            ),
            client_num=row[4],
            driver_name=row[5],
            driver_num=row[6],
            id=row[0],
            last_update=row[2].replace(tzinfo=None)
        )

    async def initialise_db_if_empty(self):
        await self.execute_query(queries.INITIALIZE_DB)

    async def execute_query(self, query: str, *params) -> list[tuple[Any, ...]]:
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute(query, params)
                rows = []
                if cursor.description:
                    rows = await cursor.fetchall()
                await self.connection.commit()
                return rows
        except Exception as e:
            await self.connection.rollback()
            raise e

