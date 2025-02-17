from dataclasses import dataclass, field
from typing import Set, Dict, List
from nillion_client_proto.nillion.permissions.v1.permissions import (
    Permissions as ProtoPermissions,
    ComputePermissions as ProtoComputePermissions,
)
from nillion_client_proto.nillion.permissions.v1.update import (
    PermissionCommand as ProtoPermissionCommand,
    ComputePermissionCommand as ProtoComputePermissionCommand,
)
from nillion_client import UserId, ProgramId


@dataclass
class ComputePermission:
    """
    A record of compute permissions.
    """

    program_ids: Set[ProgramId] = field(default_factory=set)


@dataclass
class ComputePermissions:
    """
    A collection of compute permissions, mapping user IDs to their permissions.
    """

    permissions: Dict[UserId, ComputePermission] = field(default_factory=dict)

    def to_proto(self) -> List[ProtoComputePermissions]:
        """
        Convert this ComputePermissions instance to a list of ProtoComputePermissions messages.
        """
        return [
            ProtoComputePermissions(
                user=user_id.to_proto(), program_ids=list(permission.program_ids)
            )
            for user_id, permission in self.permissions.items()
        ]

    @classmethod
    def from_proto(
        cls, proto_list: List[ProtoComputePermissions]
    ) -> "ComputePermissions":
        """
        Create a ComputePermissions instance from a list of ProtoComputePermissions messages.
        """
        permissions = {
            UserId.from_proto(proto_perm.user): ComputePermission(
                program_ids=set(proto_perm.program_ids)
            )
            for proto_perm in proto_list
        }
        return cls(permissions)


@dataclass
class Permissions:
    """
    The permissions associated with a set of stored values.
    """

    owner: UserId
    retrieve: Set[UserId] = field(default_factory=set)
    update: Set[UserId] = field(default_factory=set)
    delete: Set[UserId] = field(default_factory=set)
    compute: ComputePermissions = field(default_factory=ComputePermissions)

    @classmethod
    def defaults_for_user(cls, user_id: UserId) -> "Permissions":
        """Returns a Permissions object with update, retrieve and delete permissions for a user."""
        retrieve = {user_id}
        update = {user_id}
        delete = {user_id}
        compute = ComputePermissions()
        return cls(
            owner=user_id,
            retrieve=retrieve,
            update=update,
            delete=delete,
            compute=compute,
        )

    def allow_retrieve(self, user_id: UserId) -> "Permissions":
        """
        Allow a user to retrieve these values.
        """
        self.retrieve.add(user_id)
        return self

    def allow_delete(self, user_id: UserId) -> "Permissions":
        """
        Allow a user to delete these values.
        """
        self.delete.add(user_id)
        return self

    def allow_update(self, user_id: UserId) -> "Permissions":
        """
        Allow a user to update these values.
        """
        self.update.add(user_id)
        return self

    def allow_compute(self, user_id: UserId, program_id: ProgramId) -> "Permissions":
        """
        Allow a user to use these values on an execution of the given program id.
        """
        if user_id not in self.compute.permissions:
            self.compute.permissions[user_id] = ComputePermission()
        self.compute.permissions[user_id].program_ids.add(program_id)
        return self

    def to_proto(self) -> ProtoPermissions:
        """
        Convert this Permissions instance to a ProtoPermissions message.
        """
        return ProtoPermissions(
            owner=self.owner.to_proto(),
            retrieve=[user_id.to_proto() for user_id in self.retrieve],
            update=[user_id.to_proto() for user_id in self.update],
            delete=[user_id.to_proto() for user_id in self.delete],
            compute=self.compute.to_proto(),
        )

    @classmethod
    def from_proto(cls, proto: ProtoPermissions) -> "Permissions":
        """
        Create a Permissions instance from a ProtoPermissions message.
        """
        return cls(
            owner=UserId.from_proto(proto.owner),
            retrieve=set([UserId.from_proto(user_id) for user_id in proto.retrieve]),
            update=set([UserId.from_proto(user_id) for user_id in proto.update]),
            delete=set([UserId.from_proto(user_id) for user_id in proto.delete]),
            compute=ComputePermissions.from_proto(proto.compute),
        )


@dataclass
class PermissionCommand:
    """A command to grant/revoke permissions"""

    grant: Set[UserId] = field(default_factory=set)
    revoke: Set[UserId] = field(default_factory=set)

    def to_proto(self) -> ProtoPermissionCommand:
        """Convert an instance to its protobuf representation"""
        return ProtoPermissionCommand(
            grant=[user.to_proto() for user in self.grant],
            revoke=[user.to_proto() for user in self.revoke],
        )

    @staticmethod
    def from_proto(proto: ProtoPermissionCommand) -> "PermissionCommand":
        """Construct an instance from its protobuf representation"""
        return PermissionCommand(
            grant=set([UserId.from_proto(user) for user in proto.grant]),
            revoke=set([UserId.from_proto(user) for user in proto.revoke]),
        )


@dataclass
class ComputePermissionCommand:
    """A command to grant/revoke compute permissions"""

    grant: ComputePermissions = field(default_factory=ComputePermissions)
    revoke: ComputePermissions = field(default_factory=ComputePermissions)

    def to_proto(self) -> ProtoComputePermissionCommand:
        """Convert an instance to its protobuf representation"""
        return ProtoComputePermissionCommand(
            grant=self.grant.to_proto(),
            revoke=self.revoke.to_proto(),
        )

    @staticmethod
    def from_proto(proto: ProtoComputePermissionCommand) -> "ComputePermissionCommand":
        """Construct an instance from its protobuf representation"""
        return ComputePermissionCommand(
            grant=ComputePermissions.from_proto(proto.grant),
            revoke=ComputePermissions.from_proto(proto.revoke),
        )


@dataclass
class PermissionsDelta:
    """A delta of permission grants/revokes to be applied"""

    retrieve: PermissionCommand = field(default_factory=PermissionCommand)
    update: PermissionCommand = field(default_factory=PermissionCommand)
    delete: PermissionCommand = field(default_factory=PermissionCommand)
    compute: ComputePermissionCommand = field(default_factory=ComputePermissionCommand)
