
from typing import Optional, Any
from app.loads.load import Load, Stages
from psycopg import AsyncConnection
from psycopg.errors import DataError, IntegrityError
from app.loads import queries
from app.logger import db_logger

# TMP_PG_RUN_CMD = 'docker run --name dev-postgres -e POSTGRES_DB=pstgrs -e POSTGRES_USER=olvr -e POSTGRES_PASSWORD=msVWXP -p 127.0.0.1:5432:5432 -d postgres'
# TODO REMOVE TMP_PG_RUN_CMD AND SET UP DOCKER COMPOSE
# TODO DO NOT FORGET TO ADD PERSISTENT VOLUME



class Loads:
    """
    Database manager for handling load operations.

    Provides async database operations for managing transportation loads,
    including CRUD operations, stage management, and data persistence.
    Implements async context manager for proper connection handling.
    """

    def __init__(self, db_connection_url: str):
        """
        Initialize the Loads manager with database connection.

        Args:
            db_connection_url: PostgreSQL connection URL for database access.
        """

        self.db_connection_url = db_connection_url
        self.connection: Optional[AsyncConnection] = None

    async def __aenter__(self):
        """
        Async context manager entry.

        Establishes database connection and initializes tables if needed.

        Returns:
            self: The Loads instance for use in async context.
        """
        db_logger.info(f"Connecting to database: {self.db_connection_url}")
        try:
            self.connection = await AsyncConnection.connect(self.db_connection_url)
            db_logger.info("Database connection established successfully")

            db_logger.debug("Initializing database schema if needed")
            await self.initialise_db_if_empty()
            db_logger.info("Database initialization completed")

            return self
        except Exception as e:
            db_logger.error(f"Failed to connect to database: {e}")
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit.

        Closes the database connection and cleans up resources.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.
        """
        if self.connection:
            db_logger.info("Closing database connection")
            try:
                await self.connection.close()
                db_logger.info("Database connection closed successfully")
            except Exception as e:
                db_logger.error(f"Error closing database connection: {e}")

    async def get_load_by_id(self, load_id: str) -> Optional[Load]:
        """
        Retrieve a specific load by its unique identifier.

        Args:
            load_id: Unique identifier for the load.

        Returns:
            Optional[Load]: The load object if found, None otherwise.

        Raises:
            TypeError: If load_id is not a string.
        """
        db_logger.debug(f"Retrieving load by ID: {load_id}...")

        if not isinstance(load_id, str):
            db_logger.error(f"Invalid load_id type: {type(load_id).__name__}, expected str")
            raise TypeError('load_id must be a string')

        try:
            rows = await self.execute_query(
                queries.CTE_SELECT_ALL_LOADS +
                queries.FILTER_SINGLE_LOAD,
                load_id
            )

            if rows is not None and len(rows) > 0:
                load = self._convert_cte_row_to_load(rows[0])
                db_logger.debug(f"Load found: {load_id}... (stage: {load.stage})")
                return load
            else:
                db_logger.debug(f"Load not found: {load_id}...")
                return None
        except Exception as e:
            db_logger.error(f"Error retrieving load by ID {load_id}...: {e}")
            raise

    async def get_qty_of_actives(self):
        """
        Get the count of active loads.

        Returns:
            int: Number of loads not in 'history' stage.
        """
        rows = await self.execute_query(query=queries.COUNT_ACTIVE_LOADS)
        return rows[0][0]

    async def get_qty_of_historicals(self):
        """
        Get the count of historical loads.

        Returns:
            int: Number of loads in 'history' stage.
        """
        rows = await self.execute_query(query=queries.COUNT_HISTORICAL_LOADS)
        return rows[0][0]

    async def get_actives(self) -> list[Load]:
        """
        Retrieve all active loads from the database.

        Returns:
            list[Load]: List of loads not in 'history' stage.
        """
        return await self._get_loads_by_fq(filter_query=queries.FILTER_ACTIVE_LOADS)

    async def get_historicals(self) -> list[Load]:
        """
        Retrieve all historical loads from the database.

        Returns:
            list[Load]: List of loads in 'history' stage.
        """
        return await self._get_loads_by_fq(filter_query=queries.FILTER_HISTORY_LOADS)

    async def add(self, load: Load) -> str:
        """
        Add a new load to the database.

        Creates client and driver records if they don't exist,
        then creates the load record.

        Args:
            load: Load object to add to the database.

        Returns:
            str: The load ID of the created load.
        """
        db_logger.info(f"Adding new load: {load.load_id}... (type: {load.load_type}, stage: {load.stage})")

        try:
            db_logger.debug(f"Inserting client: {load.client_num[:6]}...")
            client_id = await self._insert_client(load.client_num)

            db_logger.debug(f"Inserting driver: {load.driver_name}")
            driver_id = await self._insert_driver(
                name=load.driver_name,
                phone_num=load.driver_num
            )

            db_logger.debug(f"Inserting load: {load.load_id}...")
            load_id = await self._insert_load(
                load=load,
                client_id=client_id,
                driver_id=driver_id
            )

            db_logger.info(f"Load successfully added: {load_id}...")
            return load_id
        except Exception as e:
            db_logger.error(f"Error adding load {load.load_id}...: {e}")
            raise

    async def change_stage(self, load: Load, new_stage) -> Load:
        """
        Update a load's stage and save changes to database.

        Args:
            load: Load object to update.
            new_stage: New stage to set for the load.

        Returns:
            Load: Updated load object with new stage and timestamp.
        """
        old_stage = load.stage
        db_logger.info(f"Changing load stage: {load.load_id}... from '{old_stage}' to '{new_stage}'")

        try:
            load.change_stage(new_stage)
            await self.update(load)
            db_logger.info(f"Load stage successfully updated: {load.load_id}...")
            return load
        except Exception as e:
            db_logger.error(f"Error changing stage for load {load.load_id}...: {e}")
            raise

    async def update(self, load: Load) -> str:
        """
        Update an existing load in the database.

        Args:
            load: Load object with updated data.

        Returns:
            str: The load ID of the updated load.
        """

        return await self._update_load(load)

    async def _get_loads_by_fq(self, filter_query: str) -> list[Load]:
        """
        Internal method to get loads using a filter query.

        Args:
            filter_query: SQL filter condition for the loads query.

        Returns:
            list[Load]: List of loads matching the filter criteria.
        """
        rows = await self.execute_query(query=queries.CTE_SELECT_ALL_LOADS + filter_query)
        loads = []
        for row in rows:
            loads.append(
                self._convert_cte_row_to_load(row)
            )
        return loads

    async def _insert_client(self, phone_number: str) -> int:
        """
        Insert a new client or get existing client ID.

        Args:
            phone_number: Client's phone number.

        Returns:
            int: Client ID from the database.

        Raises:
            ValueError: If database operation fails.
        """
        try:
            rows = await self.execute_query(queries.INSERT_CLIENT, phone_number)
            return rows[0][0]
        except (DataError, IntegrityError, IndexError) as e:
            raise ValueError from e

    async def _insert_driver(self, name: str, phone_num: str) -> int:
        """
        Insert a new driver or get existing driver ID.

        Args:
            name: Driver's name.
            phone_num: Driver's phone number.

        Returns:
            int: Driver ID from the database.

        Raises:
            ValueError: If database operation fails.
        """
        try:
            rows = await self.execute_query(queries.INSERT_DRIVER, name, phone_num)
            return rows[0][0]
        except (DataError, IntegrityError, IndexError) as e:
            raise ValueError from e

    async def _insert_load(self, load: Load, client_id, driver_id) -> str:
        """
        Insert a new load record into the database.

        Args:
            load: Load object to insert.
            client_id: ID of the associated client.
            driver_id: ID of the associated driver.

        Returns:
            str: The load ID of the inserted load.

        Raises:
            ValueError: If database operation fails.
        """
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
        """
        Update an existing load record in the database.

        Args:
            load: Load object with updated data.

        Returns:
            str: The load ID of the updated load.

        Raises:
            ValueError: If load doesn't exist in database.
        """
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
        """
        Convert a database row from the loads CTE query to a Load object.

        Args:
            row: Database row with load data from the CTE query.

        Returns:
            Load: Load object created from the database row.
        """
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
        """
        Initialize database tables if they don't exist.

        Creates the necessary database schema for clients, drivers, and loads.
        """
        await self.execute_query(queries.INITIALIZE_DB)

    async def execute_query(self, query: str, *params) -> list[tuple[Any, ...]]:
        """
        Execute a database query with parameters.

        Handles connection management, commits successful queries,
        and rolls back on errors.

        Args:
            query: SQL query string to execute.
            *params: Query parameters to bind.

        Returns:
            list[tuple[Any, ...]]: Query results as list of tuples.

        Raises:
            Exception: Re-raises any database exceptions after rollback.
        """
        # Log query execution (truncate long queries)
        query_preview = query[:100] + "..." if len(query) > 100 else query
        db_logger.debug(f"Executing query: {query_preview} with {len(params)} parameters")

        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute(query, params)
                rows = []
                if cursor.description:
                    rows = await cursor.fetchall()
                    db_logger.debug(f"Query returned {len(rows)} rows")
                else:
                    db_logger.debug("Query executed (no return data)")

                await self.connection.commit()
                return rows
        except Exception as e:
            db_logger.error(f"Database query failed: {e}")
            db_logger.debug(f"Failed query: {query_preview}")
            await self.connection.rollback()
            raise e

