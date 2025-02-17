import hashlib
from uuid import UUID

from dataclasses import dataclass
import secp256k1

from nillion_client_proto.nillion.auth.v1.user import (
    UserId as ProtoUserId,
)

USER_ID_LENGTH = 20


@dataclass(eq=True, frozen=True)
class UserId:
    """
    A user identifier.

    User identifiers are derived from the public key used for authentication when performing operations in the
    network. User identifiers are non sensitive and can be shared with other users.
    """

    contents: bytes

    @staticmethod
    def parse(hex_bytes: str) -> "UserId":
        """
        Parse a user identifier from a hex encoded string.

        Arguments
        ---------
        hex_bytes
            The hex bytes that represent the user id.

        Returns
        -------
            The parsed user id.

        Example
        -------

        .. code-block:: py3

            user = UserId.parse("3113a1170de795e4b725b84d1e0b4cfd9ec58ce9")
        """
        try:
            contents = bytes.fromhex(hex_bytes)
        except Exception as ex:
            raise InvalidUserId(str(ex))
        if len(contents) != USER_ID_LENGTH:
            raise InvalidUserId(f"length should be {USER_ID_LENGTH} bytes")
        return UserId(contents)

    @staticmethod
    def from_public_key(public_key: secp256k1.PublicKey) -> "UserId":
        """
        Creates a user identifier from a public key.

        User identifiers are defined as the last 20 bytes of the SHA256 hash of the public key.

        Returns
        -------
            The user id.

        Example
        -------

        .. code-block:: py3

            import secp256k1

            private_key = secp256k1.PrivateKey()
            user = UserId.from_public_key(private_key.pubkey)
        """
        raw_key = public_key.serialize()

        # Sha256-hash it
        hashed_key = hashlib.sha256(raw_key).digest()

        # Keep the last 20 bytes.
        contents = hashed_key[len(hashed_key) - 20 :]
        return UserId(contents)

    def to_proto(self) -> ProtoUserId:
        """
        Convert a user identifier to its protobuf representation.
        """
        return ProtoUserId(contents=self.contents)

    @classmethod
    def from_proto(cls, proto: ProtoUserId) -> "UserId":
        """
        Create a user identifier instance from its protobuf representation.
        """
        return UserId(contents=proto.contents)

    def __str__(self) -> str:
        return self.contents.hex()


class InvalidUserId(Exception):
    """
    An exception thrown when the string representation of a user identifier is invalid
    """

    pass


@dataclass(frozen=True)
class UuidIdentifier:
    contents: bytes

    def __str__(self) -> str:
        return str(UUID(bytes=self.contents))

    def __bytes__(self) -> bytes:
        return self.contents


ProgramId = str
"""Program identifier."""

ValuesId = UUID
"""Values identifier."""

ComputeId = UUID
"""Identifier of a computation."""
