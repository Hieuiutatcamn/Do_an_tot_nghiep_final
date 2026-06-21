from sqlalchemy import Boolean, TypeDecorator
from sqlalchemy.dialects import mysql


class BitBoolean(TypeDecorator):
    impl = Boolean
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "mysql":
            return dialect.type_descriptor(mysql.BIT(1))
        return dialect.type_descriptor(Boolean())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "mysql":
            return 1 if value else 0
        return bool(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, bytes):
            return int.from_bytes(value, byteorder="big") == 1
        return bool(value)
