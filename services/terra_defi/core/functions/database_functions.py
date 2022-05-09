from datetime import datetime
from typing import Union, Any


def getStrOrNone(value: Any) -> Union[str, None]:
    return str(value) if value is not None else None


def getTimestampOrNone(value: Any) -> Union[float, None]:
    if value is None:
        return None
    else:
        result = datetime.timestamp(value) * 1e3
        return result


def getIntOrNone(value: Any) -> Union[int, None]:
    return int(value) if value is not None else None


def getFloatOrNone(value: Any) -> Union[float, None]:
    return float(value) if value is not None else None


def getBoolOrNone(value: Any) -> Union[bool, None]:
    return bool(value) if value is not None else None
