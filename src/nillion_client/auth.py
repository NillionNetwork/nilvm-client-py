import datetime
import secrets

from nillion_client_proto.nillion.membership.v1.cluster import NodeId
import secp256k1
from grpclib.events import SendRequest
from nillion_client_proto.nillion.auth.v1.public_key import PublicKey, PublicKeyType
from nillion_client_proto.nillion.auth.v1.token import Token, SignedToken

HEADER_NAME = "x-nillion-token-bin"
_TOKEN_EXPIRY = 60
_RENEWAL_THRESHOLD = 10


class AuthInterceptor:
    """An interceptor that adds a token to authenticate the user on every request."""

    def __init__(self, signing_key: secp256k1.PrivateKey, identity: NodeId):
        self._signing_key = signing_key
        self._identity = identity
        self._token = _create_token(signing_key, identity)
        self._token_expiry_time = None
        self._renew_token()

    def _renew_token(self):
        self._token = _create_token(self._signing_key, self._identity)
        now = datetime.datetime.now(datetime.timezone.utc)
        self._token_expiry_time = now + datetime.timedelta(seconds=_TOKEN_EXPIRY)

    def _is_token_expired_or_about_to_expire(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        return (
            self._token_expiry_time is None
            or (self._token_expiry_time - now).total_seconds() <= _RENEWAL_THRESHOLD
        )

    async def intercept_send_request(self, event: SendRequest):
        if self._is_token_expired_or_about_to_expire():
            self._renew_token()
        event.metadata[HEADER_NAME] = self._token


def _create_token(signing_key: secp256k1.PrivateKey, identity: NodeId):
    now = datetime.datetime.now(datetime.timezone.utc)
    expires_at = now + datetime.timedelta(seconds=_TOKEN_EXPIRY)

    token = Token(
        nonce=secrets.token_bytes(32),
        target_identity=identity,
        expires_at=expires_at,
    )

    public_key = PublicKey(
        key_type=PublicKeyType.SECP256K1,
        contents=signing_key.pubkey.serialize(),  # type: ignore
    )

    token = token.SerializeToString()
    signed_message = signing_key.ecdsa_sign(token)
    signature = signing_key.ecdsa_serialize_compact(signed_message)

    signed_token = SignedToken(
        serialized_token=token,
        public_key=public_key,
        signature=signature,
    )

    return signed_token.SerializeToString()
