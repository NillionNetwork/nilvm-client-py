from nada_dsl import Party, SecretInteger, Input, Output


def nada_main():
    party1 = Party("Party1")
    my_int1 = SecretInteger(Input(name="my_int1", party=party1))  # type: ignore
    my_int2 = SecretInteger(Input(name="my_int2", party=party1))  # type: ignore
    sum = my_int1 + my_int2
    return [Output(sum, "sum", party1)]
