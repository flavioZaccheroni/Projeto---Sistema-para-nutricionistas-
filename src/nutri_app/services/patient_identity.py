from __future__ import annotations


def digits_only(value: str) -> str:
    return "".join(character for character in value if character.isdigit())


def normalize_cpf(value: str) -> str:
    return digits_only(value)


def normalize_cns(value: str) -> str:
    return digits_only(value)


def is_valid_cpf(value: str) -> bool:
    cpf = normalize_cpf(value)
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False

    numbers = [int(character) for character in cpf]
    first_sum = sum(
        number * weight for number, weight in zip(numbers[:9], range(10, 1, -1), strict=True)
    )
    first_digit = 0 if first_sum % 11 < 2 else 11 - (first_sum % 11)
    if numbers[9] != first_digit:
        return False

    second_sum = sum(
        number * weight for number, weight in zip(numbers[:10], range(11, 1, -1), strict=True)
    )
    second_digit = 0 if second_sum % 11 < 2 else 11 - (second_sum % 11)
    return numbers[10] == second_digit


def is_valid_cns(value: str) -> bool:
    cns = normalize_cns(value)
    if len(cns) != 15 or len(set(cns)) == 1:
        return False
    weighted_sum = sum(
        int(number) * weight for number, weight in zip(cns, range(15, 0, -1), strict=True)
    )
    return weighted_sum % 11 == 0
