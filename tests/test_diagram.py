from app.backend.diagram import _distribute_servers


def test_distribute_servers_even_split() -> None:
    assert _distribute_servers(6, 3) == [2, 2, 2]


def test_distribute_servers_remainder_goes_from_first_az() -> None:
    assert _distribute_servers(5, 3) == [2, 2, 1]


def test_distribute_servers_single_az() -> None:
    assert _distribute_servers(4, 1) == [4]
