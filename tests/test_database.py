
import pytest
from testcontainers.postgres import PostgresContainer
from app.loads.loads import Loads
import app.loads.queries as queries
from app.loads.load import Load, Stages


TEST_DB_NAME = 'test_loads'


@pytest.fixture(scope='session')
def docker_pg_instance():
    with PostgresContainer(
        'postgres:17',
        driver=None
    ) as pg_container:
        yield pg_container


@pytest.fixture(scope='session')
async def loads_instance(docker_pg_instance: PostgresContainer):
    url=docker_pg_instance.get_connection_url()
    async with Loads(db_connection_url=url) as loads:
        # Here goes cleaning and fake data injection
        await loads.execute_query(queries.DROP_ALL_TABLES)
        await loads.initialise_db_if_empty()
        await loads.execute_query(queries.ADD_FAKE_DATA)
        yield loads


@pytest.fixture(scope='session')
def load():
    return Load(
        type='external',
        stage='history',
        stages=Stages(
            start='Полтава',
            engage='Київ',
            clear='Плзень',
            finish='Варшава'
        ),
        client_num='380631231212',
        driver_name='Тарас',
        driver_num='380637776633'
    )


@pytest.fixture(scope='session')
def load2():
    return Load(
        type='internal',
        stage='start',
        stages=Stages(
            start='Полтава',
            engage='Київ',
            clear='Плзень',
            finish='Варшава'
        ),
        client_num='380631231212',
        driver_name='Тарас',
        driver_num='380637776633'
    )


@pytest.mark.integration
async def test_get_actives(loads_instance: Loads):
    active_loads = await loads_instance.get_actives()
    assert isinstance(active_loads, list)
    assert len(active_loads) == 2
    assert isinstance(active_loads[0], Load)
    assert isinstance(active_loads[1], Load)


@pytest.mark.integration
async def test_get_historicals(loads_instance: Loads):
    historical_loads = await loads_instance.get_historicals()
    assert isinstance(historical_loads, list)
    assert len(historical_loads) == 1
    assert isinstance(historical_loads[0], Load)


@pytest.mark.integration
async def test_add_load(loads_instance: Loads, load):
    load_id = await loads_instance.add(load)
    assert isinstance(load_id, str)
    assert len(load_id) == 32
    assert load_id == load.load_id


@pytest.mark.integration
async def test_add_load_twice(loads_instance: Loads, load):
    with pytest.raises(ValueError):
        await loads_instance.add(load)


@pytest.mark.integration
async def test_get_load_by_id(loads_instance, load):
    got_load = await loads_instance.get_load_by_id(load.load_id)
    assert isinstance(got_load, Load)
    assert got_load == load


@pytest.mark.integration
async def test_update_load(loads_instance: Loads, load):
    load.change_stage('finish')
    load_id = await loads_instance.update(load)
    got_load = await loads_instance.get_load_by_id(load_id)
    assert isinstance(got_load, Load)
    assert got_load == load


@pytest.mark.integration
async def test_update_missing_load(loads_instance: Loads, load2):
    with pytest.raises(ValueError):
        await loads_instance.update(load2)


@pytest.mark.integration
async def test_update_load_wrong_parameters(loads_instance: Loads, load):
    load.change_stage('wrong_parameter')
    with pytest.raises(ValueError):
        await loads_instance.update(load)

@pytest.mark.integration
async def test_get_load_by_id_fail(loads_instance: Loads):
    with pytest.raises(TypeError):
        await loads_instance.get_load_by_id(123)


@pytest.mark.integration
@pytest.mark.parametrize(
    'client_phone,expected_id', [
        ('380951234567', 6),
        ('380951234568', 7),
        ('380951234568', 7),
        ('380951234569', 9)
    ]
)
async def test_insert_client_ok(loads_instance, client_phone, expected_id):
    assert expected_id == await loads_instance._insert_client(client_phone)


@pytest.mark.integration
@pytest.mark.parametrize(
    'client_phone', [
        '3809512345678',  # too long
        '38095123456',    # too short
        '38095A234567',   # contains_char
        None              # null
    ]
)
async def test_insert_client_fail(loads_instance, client_phone):
    with pytest.raises(ValueError):
        await loads_instance._insert_client(client_phone)


@pytest.mark.integration
@pytest.mark.parametrize(
    'driver_name,driver_phone,expected_id', [
        ('Alice', '380951234567', 6),
        ('Bob', '380951234567', 7),
        ('Bob', '380951234567', 7),
        ('Diana', '380951234567', 9)
    ]
)
async def test_insert_driver_usert(loads_instance, driver_name, driver_phone, expected_id):
    assert expected_id == await loads_instance._insert_driver(driver_name, driver_phone)


@pytest.mark.integration
@pytest.mark.parametrize(
    'driver_name,driver_phone', [
        ('Alice', '3809512345678'),  # too long
        ('Bob', '38095123456'),      # too short
        ('Charlie', '38095A234567'), # contains char
        ('Diana', None)              # null
    ]
)
async def test_insert_driver_wrong_number(loads_instance, driver_name, driver_phone):
    with pytest.raises(ValueError):
        await loads_instance._insert_driver(driver_name, driver_phone)
