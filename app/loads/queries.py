

INITIALIZE_DB = """
    begin;

    create table if not exists clients(
        clients_id serial primary key,
        phone_num varchar(12) not null unique,
        check(char_length(phone_num) = 12),
        check(phone_num ~ '^[0-9]+$')
    );

    create table if not exists drivers(
        drivers_id serial primary key,
        name_surname text not null,
        phone_num varchar(12) not null,
        check(char_length(phone_num) = 12),
        check(phone_num ~ '^[0-9]+$'),
        unique(name_surname, phone_num)
    );

    create table if not exists load_statuses(
        load_status_id serial primary key,
        status varchar(10) not null unique
    );

    create table if not exists load_types(
        load_types_id serial primary key,
        load_type varchar(8) not null unique
    );

    create table if not exists loads(
        loads_id char(32) primary key,
        created_at timestamptz not null default now(),
        modified_at timestamptz not null, -- This field is filling up from the Pydantic Load model
        load_type_id int4 not null references load_types(load_types_id),
        client_id int4 not null references clients(clients_id),
        driver_id int4 not null references drivers(drivers_id),
        current_status_id int2 not null references load_statuses(load_status_id),
        start_city text not null,
        engage_city text,
        clear_city text,
        finish_city text not null
    );

    insert into load_statuses (status) 
    values 
        ('start'),
        ('engage'), 
        ('drive'),
        ('clear'),
        ('finish'), 
        ('history')
    on conflict (status) do nothing;

    insert into load_types (load_type)
    values ('external'), ('internal')
    on conflict (load_type) do nothing;

    commit;
"""

DROP_ALL_TABLES = """
    DROP TABLE IF EXISTS loads;
    DROP TABLE IF EXISTS load_statuses;
    DROP TABLE IF EXISTS load_types;
    DROP TABLE IF EXISTS clients;
    DROP TABLE IF EXISTS drivers;
"""

ADD_FAKE_DATA = """

    insert into clients (phone_num)
    values
        ('380951234561'),
        ('380951234532'),
        ('380501234533');

    insert into drivers (name_surname, phone_num)
    values
        ('Микола', '380951234567'),
        ('Василь', '380951234568'),
        ('Дмитро', '380951234569');

    insert into loads (
        loads_id,
        created_at,
        modified_at,
        load_type_id,
        client_id,
        driver_id,
        current_status_id,
        start_city,
        engage_city,
        clear_city,
        finish_city
    )
    values 
        ('9264575ff59944ebac30d8ffc38280ba', now(), now(), 1, 1, 1, 1, 'Полтава', 'Київ', 'Плзень', 'Варшава'),
        ('9264575ff59944ebac30d8ffc38280bb', now(), now(), 2, 2, 2, 3, 'Полтава', 'Київ', 'Плзень', 'Варшава'),
        ('9264575ff59944ebac30d8ffc38280bc', now(), now(), 1, 3, 3, 6, 'Полтава', 'Київ', 'Плзень', 'Варшава');
"""

CTE_SELECT_ALL_LOADS = """
    with all_loads as (
    select
        l.loads_id,
        l.created_at,
        l.modified_at,
        lt.load_type,
        c.phone_num as client_number,
        d.name_surname as driver_name,
        d.phone_num as driver_phone,
        ls.status as current_status,
        l.start_city,
        l.engage_city,
        l.clear_city,
        l.finish_city
    from loads l
    join clients c
        on l.client_id = c.clients_id
    join drivers d
        on l.driver_id = d.drivers_id
    join load_statuses ls
        on l.current_status_id = ls.load_status_id
    join load_types lt
		on l.load_type_id = lt.load_types_id
    order by modified_at
)
"""

FILTER_ACTIVE_LOADS = """
    select * from all_loads
    where current_status != 'history'
"""

FILTER_HISTORY_LOADS = """
    select * from all_loads
    where current_status = 'history'
"""

FILTER_SINGLE_LOAD = """
    select * from all_loads
    where loads_id = %s
"""

INSERT_CLIENT = """
    insert into clients (phone_num)
    values (%s)
    on conflict (phone_num) 
    do update
    set phone_num = excluded.phone_num
    returning clients_id;
"""

INSERT_DRIVER = """
    insert into drivers (name_surname, phone_num)
    values (%s, %s)
    on conflict (name_surname, phone_num)
    do update
    set 
        name_surname = excluded.name_surname,
        phone_num = excluded.phone_num
    returning drivers_id
"""

INSERT_LOAD = """
    insert into loads (
        loads_id,
        modified_at,
        load_type_id,
        client_id,
        driver_id,
        current_status_id,
        start_city,
        engage_city,
        clear_city,
        finish_city
    )
    values (
        %s, --loads_id
        %s, --modified_at
        (select load_types_id from load_types where load_type = %s), -- load_type
        %s, -- client_id
        %s, -- driver_id
        (select load_status_id from load_statuses where status = %s), -- current_status
        %s, -- start_city
        %s, -- engage_city
        %s, -- clear_city
        %s  -- finish_city
    )
    returning loads_id;
"""

UPDATE_LOAD = """
    update loads l
    set
        modified_at = %s,
        current_status_id = (select load_status_id from load_statuses ls where ls.status = %s)
    where
        l.loads_id = %s
    returning l.loads_id
"""