REM This SQL script creates the necessary tables for the weather collection
REM and forecasting system.

CREATE TABLE sites (
    site	varchar(10) not null,
    city	varchar(50),
    state	varchar(2),
    CONSTRAINT site_pk PRIMARY KEY ( site )
);

CREATE TABLE observations (
    site		varchar(10) not null,
    time		datetime not null,
    temperature		integer,
    humidity		integer,
    wind_direction	integer,
    wind_speed		integer,
    pressure		integer,
    weather		varchar(100),
    CONSTRAINT obs_pk PRIMARY KEY ( site, time )
);

CREATE TABLE predicted (
    time		DATETIME not null,
    temperature		integer,
    humidity		integer,
    wind_direction	integer,
    wind_speed		integer,
    pressure		integer,
    weather		varchar(100),
    CONSTRAINT predicted_pk PRIMARY KEY ( time )
);

