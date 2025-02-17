import hashlib
import secp256k1
from nillion_client import Permissions
from nillion_client_proto.nillion.permissions.v1.permissions import (
    Permissions as ProtoPermissions,
    ComputePermissions as ProtoComputePermissions,
)

from nillion_client.ids import UserId
from nillion_client.permissions import (
    ComputePermission,
    ComputePermissionCommand,
    ComputePermissions,
    PermissionCommand,
)


def make_user_id(seed: str) -> UserId:
    raw_seed = hashlib.sha256(seed.encode("utf8")).digest()
    key = secp256k1.PrivateKey(raw_seed)
    return UserId.from_public_key(key.pubkey)  # type: ignore


def test_allow_retrieve():
    user = make_user_id("other")
    permissions = Permissions(owner=make_user_id("owner"))
    permissions.allow_retrieve(user)
    assert user in permissions.retrieve


def test_allow_delete():
    user = make_user_id("other")
    permissions = Permissions(owner=make_user_id("owner"))
    permissions.allow_delete(user)
    assert user in permissions.delete


def test_allow_update():
    user = make_user_id("other")
    permissions = Permissions(owner=make_user_id("owner"))
    permissions.allow_update(user)
    assert user in permissions.update


def test_allow_compute():
    user = make_user_id("user4")
    permissions = Permissions(owner=make_user_id("owner"))
    permissions.allow_compute(user, "program1")
    assert user in permissions.compute.permissions
    assert "program1" in permissions.compute.permissions[user].program_ids


def test_chained_methods():
    permissions = (
        Permissions(owner=make_user_id("owner"))
        .allow_retrieve(make_user_id("user1"))
        .allow_delete(make_user_id("user2"))
        .allow_update(make_user_id("user3"))
        .allow_compute(make_user_id("user4"), "program2")
    )
    assert make_user_id("user1") in permissions.retrieve
    assert make_user_id("user2") in permissions.delete
    assert make_user_id("user3") in permissions.update
    assert make_user_id("user4") in permissions.compute.permissions
    assert (
        "program2" in permissions.compute.permissions[make_user_id("user4")].program_ids
    )


def test_multiple_compute_permissions():
    user = make_user_id("other")
    permissions = (
        Permissions(owner=make_user_id("owner"))
        .allow_compute(user, "program3")
        .allow_compute(user, "program4")
    )
    user_permissions = permissions.compute.permissions[user]
    assert "program3" in user_permissions.program_ids
    assert "program4" in user_permissions.program_ids


def test_to_proto():
    owner = make_user_id("owner")
    user = make_user_id("other")
    permissions = Permissions(owner=owner)
    permissions.allow_retrieve(user)
    proto = permissions.to_proto()
    assert proto.owner.contents == owner.contents
    assert user.to_proto() in proto.retrieve


def test_from_proto():
    # Create a ProtoPermissions message for testing
    owner = make_user_id("owner")
    retrieve_user = make_user_id("retrieve")
    compute_user = make_user_id("compute")
    program_id = "program"
    proto = ProtoPermissions(
        owner=owner.to_proto(),
        retrieve=[retrieve_user.to_proto()],
        compute=[
            ProtoComputePermissions(
                user=compute_user.to_proto(), program_ids=[program_id]
            )
        ],
    )
    expected = (
        Permissions(owner=owner)
        .allow_retrieve(retrieve_user)
        .allow_compute(compute_user, program_id)
    )
    assert Permissions.from_proto(proto) == expected


def test_permissions_equality():
    user_id_1 = make_user_id("1")
    user_id_2 = make_user_id("2")

    # Create two identical Permissions objects
    permissions1 = Permissions.defaults_for_user(user_id_1)
    permissions2 = Permissions.defaults_for_user(user_id_1)

    assert (
        permissions1 == permissions2
    ), "Permissions objects should be equal when initialized identically"

    # Modify one Permissions object
    permissions2.allow_retrieve(user_id_2)

    assert (
        permissions1 != permissions2
    ), "Permissions objects should not be equal after modification"


def test_permission_command():
    command = PermissionCommand(
        grant=set([make_user_id("1"), make_user_id("2")]),
        revoke=set([make_user_id("1"), make_user_id("2")]),
    )
    decoded = PermissionCommand.from_proto(command.to_proto())
    assert decoded == command


def test_compute_permission_command():
    command = ComputePermissionCommand(
        grant=ComputePermissions(
            permissions={make_user_id("1"): ComputePermission(program_ids=set(["a"]))}
        ),
        revoke=ComputePermissions(
            permissions={make_user_id("2"): ComputePermission(program_ids=set(["b"]))}
        ),
    )
    decoded = ComputePermissionCommand.from_proto(command.to_proto())
    assert decoded == command
