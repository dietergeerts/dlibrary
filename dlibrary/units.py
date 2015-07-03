import vs


def __get_length_units_per_inch() -> float:
    return vs.GetPrefReal(152)


def __get_area_units_per_square_inch() -> float:
    return vs.GetPrefReal(176)


def __get_volume_units_per_cubic_inch() -> float:
    return vs.GetPrefReal(180)


def to_inches(length_in_length_units: float) -> float:
    return length_in_length_units / __get_length_units_per_inch()


def to_length_units(length_in_inches: float) -> float:
    return length_in_inches * __get_length_units_per_inch()


def to_square_inches(area_in_area_units: float) -> float:
    return area_in_area_units / __get_area_units_per_square_inch()


def to_area_units(area_in_square_inches: float) -> float:
    return area_in_square_inches * __get_area_units_per_square_inch()


def to_cubic_inches(volume_in_volume_units: float) -> float:
    return volume_in_volume_units / __get_volume_units_per_cubic_inch()


def to_volume_units(volume_in_cubic_inches: float) -> float:
    return volume_in_cubic_inches * __get_volume_units_per_cubic_inch()
