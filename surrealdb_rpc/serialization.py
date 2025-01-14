import datetime
import decimal
import json

import msgpack

from surrealdb_rpc.data_model import UUID, DateTime, Decimal, Duration, Table, Thing


def msgpack_encode(obj):
    match obj:
        case None:
            return msgpack.ExtType(1, b"")
        case uuid if isinstance(uuid, UUID):
            return msgpack.ExtType(2, uuid.encode("utf-8"))
        case i if isinstance(i, (decimal.Decimal, Decimal)):
            return msgpack.ExtType(3, str(i).encode("utf-8"))
        case td if isinstance(td, (datetime.timedelta, Duration)):
            return msgpack.ExtType(4, Duration.__str__(td).encode("utf-8"))
        case dt if isinstance(dt, (datetime.datetime, DateTime)):
            return msgpack.ExtType(5, DateTime.__str__(dt).encode("utf-8"))
        # BUG: tables / table names serialized as Thing ExtTypes are rejected by SurrealDB <=2.1.4?
        case table if type(table) is Table:
            return table.table
        case thing if isinstance(thing, Thing):
            return msgpack.ExtType(6, thing.__pack__().encode("utf-8"))
        case _:
            return obj


def msgpack_decode(code, data):
    match code:
        case 1:  # NONE
            return None
        case 2:  # UUID
            return UUID(data.decode("utf-8"))
        case 3:  # Decimal
            return Decimal.from_str(data.decode("utf-8"))
        case 4:  # Duration
            return Duration.from_str(data.decode("utf-8"))
        case 5:  # DateTime
            return DateTime.from_str(data.decode("utf-8"))
        case 6:  # SurrealDB record ID
            return Thing.from_str(data.decode("utf-8"), escaped=True)
        case _:
            raise ValueError(f"Unknown msgpack extension code: {code}")


class SurrealJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        match obj:
            case uuid if isinstance(uuid, UUID):
                return str(uuid)
            case i if isinstance(i, (decimal.Decimal, Decimal)):
                return str(i)
            case td if isinstance(td, (datetime.timedelta, Duration)):
                return Duration.__str__(td)
            case dt if isinstance(dt, (datetime.datetime, DateTime)):
                return DateTime.__str__(dt)
            case thing if isinstance(thing, Thing):
                return thing.__pack__()
            case _:
                return super().default(obj)