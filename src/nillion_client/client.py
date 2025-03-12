import asyncio
import logging
import enum
import hashlib
import ssl
import secrets
from typing import List, Dict, Optional, Mapping, Callable
from urllib.parse import urlparse

from grpclib.events import SendRequest, listen
from grpclib.client import Channel
from betterproto.lib.google.protobuf import Empty
import secp256k1
from nillion_client_proto.nillion.compute.v1.invoke import (
    InvokeComputeRequest,
)
from nillion_client_proto.nillion.compute.v1.retrieve import (
    RetrieveResultsRequest,
    RetrieveResultsResponse,
)
from nillion_client_proto.nillion.compute.v1 import ComputeStub
from nillion_client_proto.nillion.leader_queries.v1.pool_status import (
    PreprocessingOffsets,
    PoolStatusRequest,
)
from nillion_client_proto.nillion.leader_queries.v1 import LeaderQueriesStub
from nillion_client_proto.nillion.membership.v1.cluster import (
    Cluster,
    ClusterMember,
    Prime,
)
from nillion_client_proto.nillion.membership.v1 import MembershipStub
from nillion_client_proto.nillion.payments.v1.quote import (
    SignedQuote,
    PriceQuoteRequest,
    StoreValues,
    InvokeCompute,
    RetrieveValues,
    PreprocessingRequirement,
    StoreProgram,
    RetrievePermissions,
    OverwritePermissions,
    UpdatePermissions,
    ProgramMetadata,
)
from nillion_client_proto.nillion.payments.v1.balance import (
    AccountBalanceResponse,
    AddFundsPayload,
    AddFundsRequest,
)
from nillion_client_proto.nillion.payments.v1.receipt import (
    PaymentReceiptRequest,
    SignedReceipt,
)
from nillion_client_proto.nillion.payments.v1 import PaymentsStub
from nillion_client_proto.nillion.permissions.v1.retrieve import (
    RetrievePermissionsRequest,
)
from nillion_client_proto.nillion.permissions.v1 import PermissionsStub
from nillion_client_proto.nillion.permissions.v1.overwrite import (
    OverwritePermissionsRequest,
)
from nillion_client_proto.nillion.permissions.v1.update import UpdatePermissionsRequest
from nillion_client_proto.nillion.preprocessing.v1.element import PreprocessingElement
from nillion_client_proto.nillion.programs.v1 import ProgramsStub
from nillion_client_proto.nillion.programs.v1.store import StoreProgramRequest
from nillion_client_proto.nillion.values.v1.delete import DeleteValuesRequest
from nillion_client_proto.nillion.values.v1.retrieve import RetrieveValuesRequest
from nillion_client_proto.nillion.values.v1 import ValuesStub
from nillion_client_proto.nillion.values.v1.store import StoreValuesRequest
from nillion_client_core import (
    EncryptedNadaValue,
    PartyId,
    SecretMasker,
    extract_program_metadata,
)

from nillion_client.values import (
    encrypted_nada_value_from_protobuf,
    encrypted_nada_values_to_protobuf,
)
from .errors import PartyError

from .ids import UserId, ValuesId, ProgramId, ComputeId
from .network import Network
from .auth import AuthInterceptor
from .payer import Payer
from .permissions import Permissions, PermissionsDelta
from .vm_operation import (
    Operation,
    StoreValuesOperation,
    OverwritePermissionsOperation,
    RetrievePermissionsOperation,
    RetrieveValuesOperation,
    DeleteValuesOperation,
    StoreProgramOperation,
    ComputeOperation,
    RetrieveComputeResultsOperation,
    PoolStatusOperation,
    PayableOperation,
    InputPartyBinding,
    OutputPartyBinding,
    UpdatePermissionsOperation,
    NadaValue,
)
from .client_retry import _invoke_with_retry


class InternalError(Exception):
    """Exception raised for internal errors in the library."""


class NotFoundError(Exception):
    """Exception raised when values are not found."""


class PermissionDeniedError(Exception):
    """Exception raised a permission to run an operation has been denied."""


class PaymentMode(enum.Enum):
    """The payment mode to be used"""

    """
    Pay per operation, making a payment on nilchain every time an operation is ran.
    """
    PAY_PER_OPERATION = enum.auto()

    """
    Pay from the balance in the nilvm network, if any. If not enough balance is available, this will fall back
    to a payment per operation.
    """
    FROM_BALANCE = enum.auto()


class _ClusterMember:
    def __init__(self, member: ClusterMember, channel: Channel, party_id: PartyId):
        self.member = member
        self.channel = channel
        self.party_id = party_id
        self.values_service = ValuesStub(channel)
        self.permissions_service = PermissionsStub(channel)
        self.programs_service = ProgramsStub(channel)
        self.compute_service = ComputeStub(channel)


class _ClusterMemberLeader(_ClusterMember):
    def __init__(self, member: ClusterMember, channel: Channel, party_id: PartyId):
        super().__init__(member, channel, party_id)
        self.leader_queries_service = LeaderQueriesStub(channel)
        self.payment_service = PaymentsStub(channel)


def _sha256(data: bytes):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(data)
    return sha256_hash.digest()


def _check_responses_equals(responses):
    if not responses:
        raise RuntimeError("Expected a responses list")

    first_element = responses[0]

    if all(element == first_element for element in responses[1:]):
        return first_element

    raise ValueError(f"Expected all nodes to return the same result: {responses}")


def wrap_party_error(party_id, func) -> Callable:
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            raise PartyError(
                f"Error invoking {func.__name__} on {party_id}: {e}"
            ) from e

    return wrapper


class VmClient:
    """
    A class to interact with the Nillion network.

    This class allows performing all operations on the Nillion network, such as storing and retrieving secrets,
    uploading programs, invoking computations, etc.

    Example
    -------

    .. code-block:: py3

        import os
        from nillion_client import PrivateKey, Network, NilChainPayer, NilChainPrivateKey, VmClient

        # The private key that will represent the identity of the user performing actions in the network.
        private_key = PrivateKey()

        # Load the config dumped by the `nillion-devnet` automatically on start and use it as the network.
        network = Network.from_config("devnet")

        # The payer that will be used to pay for operations in the network.
        nilchain_private_key = os.getenv("NILLION_NILCHAIN_KEY")
        chain_client = NilChainPayer(
            network,
            wallet_private_key=NilChainPrivateKey(bytes.fromhex(nilchain_private_key)),
            gas_limit=10000000,
        )

        # Finally, create the client
        client = await VmClient.create(private_key, network, payer)
    """

    user_id: UserId
    """The user identifier associated with this client."""

    network: Network
    """The network used by this client."""

    cluster: Cluster
    """The cluster definition that this client is using."""

    payment_mode: PaymentMode
    """The payment mode to be used."""

    def __init__(
        self,
        key: secp256k1.PrivateKey,
        network: Network,
        payer: Payer,
        payment_mode: PaymentMode,
        _raise_if_called=True,
    ):
        """
        Constructs a new instance of the client.

        Users should not directly use this function and should use the :meth:`VmClient.create` function instead.

        :meta private:
        """
        if _raise_if_called:
            raise Exception("VmClient must be initialized via VmClient.create")
        if not key.pubkey:
            raise ValueError("Key must have a public key")
        self._key = key
        self._members = []
        self._payer = payer
        self.payment_mode = payment_mode
        self.user_id = UserId.from_public_key(key.pubkey)
        self.network = network
        self.cluster = Cluster()

    def _create_channel(self, url: str, interceptors=None) -> Channel:
        grpc_endpoint_url = urlparse(url)
        use_tls = grpc_endpoint_url.scheme == "https"

        if use_tls:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ssl_context.load_default_certs()
        else:
            ssl_context = None

        channel = Channel(
            host=grpc_endpoint_url.hostname,
            port=grpc_endpoint_url.port,
            ssl=ssl_context,
        )

        if interceptors:

            async def send_request_interceptors(event: SendRequest):
                for interceptor in interceptors:
                    await _invoke_with_retry(interceptor.intercept_send_request)(event)

            listen(channel, SendRequest, send_request_interceptors)

        return channel

    async def _async_init(self):
        bootnode_channel = self._create_channel(self.network.nilvm_grpc_endpoint)

        membership_service = MembershipStub(bootnode_channel)
        request = Empty()
        self.cluster = await _invoke_with_retry(
            wrap_party_error("bootnode", membership_service.cluster)
        )(request)

        parties = []

        # Create a token and a communication channel to each member
        for member in self.cluster.members:
            channel = self._create_channel(
                member.grpc_endpoint,
                interceptors=[AuthInterceptor(self._key, member.identity)],
            )
            party_id = PartyId.from_bytes(member.identity.contents)
            self._members.append(
                _ClusterMember(
                    member=member,
                    channel=channel,
                    party_id=party_id,
                )
            )
            parties.append(party_id)

        # The leader is currently part of the cluster but that won't necessarily always be the case.
        leader_channel = self._create_channel(
            self.cluster.leader.grpc_endpoint,
            interceptors=[AuthInterceptor(self._key, self.cluster.leader.identity)],
        )

        self.leader = _ClusterMemberLeader(
            member=self.cluster.leader,
            channel=leader_channel,
            party_id=PartyId.from_bytes(self.cluster.leader.identity.contents),
        )

        # Make sure the node actually supports in-network balances.
        if self.payment_mode == PaymentMode.FROM_BALANCE:
            version = await _invoke_with_retry(
                wrap_party_error("bootnode", membership_service.node_version)
            )(Empty())
            semver = version.version
            # 0.8.0+ supports this and we consider no version to be devnet, which also supports it
            supports_balances = not semver or semver.major > 0 or semver.minor >= 8
            if not supports_balances:
                logging.warning(
                    "Falling back to paying per operation as network does not support this"
                )
                self.payment_mode = PaymentMode.PAY_PER_OPERATION

        bootnode_channel.close()

        # Create a secret masker with a prime that corresponds to the cluster's.
        match self.cluster.prime:
            case Prime.SAFE_64_BITS:
                self.secret_masker = SecretMasker.new_64_bit_safe_prime(
                    self.cluster.polynomial_degree, parties
                )
            case Prime.SAFE_128_BITS:
                self.secret_masker = SecretMasker.new_128_bit_safe_prime(
                    self.cluster.polynomial_degree, parties
                )
            case Prime.SAFE_256_BITS:
                self.secret_masker = SecretMasker.new_256_bit_safe_prime(
                    self.cluster.polynomial_degree, parties
                )

    @classmethod
    async def create(
        cls,
        key: secp256k1.PrivateKey,
        network: Network,
        payer: Payer,
        payment_mode: PaymentMode = PaymentMode.FROM_BALANCE,
    ) -> "VmClient":
        """
        Create a new Nillion client.

        Arguments
        ---------
        key
            The private key that will represent the client's identity in the network.
        network
            The network the client should connect to.
        payer
            The payer that will pay for all operations performed in the network.

        Example
        -------

        .. code-block:: py3

            client = await VmClient.create(private_key, network, payer)
        """
        client = cls(key, network, payer, payment_mode, _raise_if_called=False)
        await client._async_init()
        return client

    async def request_quote(self, operation: Operation) -> SignedQuote:
        """
        Requests a quote for an operation.

        Users should generally not use this function directly and should instead use the concrete function
        for the action they're trying to perform, such as :meth:`VmClient.store_values`,
        """
        from . import vm_operation as operations

        if isinstance(operation, operations.StoreValuesOperation):
            request = PriceQuoteRequest(
                store_values=StoreValues(
                    secret_shared_count=operation.classification.shares,
                    public_values_count=operation.classification.public,
                    ttl_days=operation.ttl_days,
                    payload_size=self._compute_values_size(operation.encrypted_values),
                )
            )
        elif isinstance(operation, operations.ComputeOperation):
            request = PriceQuoteRequest(
                invoke_compute=InvokeCompute(
                    program_id=operation.program_id,
                    values_payload_size=self._compute_values_size(
                        operation.encrypted_values
                    ),
                )
            )
        elif isinstance(operation, operations.RetrieveValuesOperation):
            request = PriceQuoteRequest(
                retrieve_values=RetrieveValues(values_id=operation.values_id.bytes)
            )
        elif isinstance(operation, operations.StoreProgramOperation):
            program_metadata = extract_program_metadata(operation.program)
            program_size = len(operation.program)
            program_sha256 = _sha256(operation.program)

            preprocessing_requirements = []

            for (
                key,
                value,
            ) in program_metadata.preprocessing_requirements.runtime_elements.items():
                match key:
                    case "Compare":
                        element = PreprocessingElement.COMPARE
                    case "DivisionIntegerSecret":
                        element = PreprocessingElement.DIVISION_SECRET_DIVISOR
                    case "EqualsIntegerSecret":
                        element = PreprocessingElement.EQUALITY_SECRET_OUTPUT
                    case "Modulo":
                        element = PreprocessingElement.MODULO
                    case "PublicOutputEquality":
                        element = PreprocessingElement.EQUALITY_PUBLIC_OUTPUT
                    case "TruncPr":
                        element = PreprocessingElement.TRUNC_PR
                    case "Trunc":
                        element = PreprocessingElement.TRUNC
                    case _:
                        raise InternalError(f"unknown preprocessing element: '{key}'")
                preprocessing_requirements.append(
                    PreprocessingRequirement(element=element, count=int(value))
                )

            request = PriceQuoteRequest(
                store_program=StoreProgram(
                    metadata=ProgramMetadata(
                        program_size=program_size,
                        memory_size=program_metadata.memory_size,
                        instruction_count=program_metadata.total_instructions,
                        instructions=program_metadata.instructions,
                        preprocessing_requirements=preprocessing_requirements,
                    ),
                    contents_sha256=program_sha256,
                    name=operation.program_name,
                )
            )
        elif isinstance(operation, operations.RetrievePermissionsOperation):
            request = PriceQuoteRequest(
                retrieve_permissions=RetrievePermissions(
                    values_id=operation.values_id.bytes
                )
            )
        elif isinstance(operation, operations.PoolStatusOperation):
            request = PriceQuoteRequest(pool_status=Empty())
        elif isinstance(operation, operations.OverwritePermissionsOperation):
            request = PriceQuoteRequest(
                overwrite_permissions=OverwritePermissions(
                    values_id=operation.values_id.bytes
                )
            )
        elif isinstance(operation, operations.UpdatePermissionsOperation):
            request = PriceQuoteRequest(
                update_permissions=UpdatePermissions(
                    values_id=operation.values_id.bytes
                )
            )
        else:
            raise InternalError(f"unknown operation: '{type(operation)}'")

        result = await _invoke_with_retry(
            wrap_party_error("leader", self.leader.payment_service.price_quote)
        )(request)
        return result

    def store_values(
        self,
        values: Mapping[str, NadaValue],
        ttl_days: int,
        permissions: Optional["Permissions"] = None,
        update_identifier: Optional[ValuesId] = None,
    ) -> PayableOperation[ValuesId]:
        """
        Store a set of values in the network.

        Any secret values will be masked automatically before uploading them.

        Arguments
        ---------
        values
            The values to store.

        ttl_days
            The number of days after which the values should be deleted. The higher this value, the higher the
            operation cost will be.

        permissions
            The permissions to be set for the uploaded values. By default only the uploader will have read and update
            permissions.

        update_identifier
            An identifier of the secret to be updated. If set, this turns this operation into an update.

        Returns
        -------
            An operation that once invoked returns an identifier that uniquely identifies the uploaded values.

        Example
        -------

        .. code-block:: py3

            values = {
                "foo": SecretInteger(42),
                "bar": Integer(1337),
            }
            await client.store_values(values, ttl_days=1).invoke()
        """
        encrypted_values = self.secret_masker.mask(values)
        classification = self.secret_masker.classify_values(values)
        return PayableOperation(
            StoreValuesOperation(
                self,
                encrypted_values,
                classification,
                ttl_days,
                permissions=permissions,
                update_identifier=update_identifier,
            )
        )

    def overwrite_permissions(
        self, values_id: ValuesId, permissions: Permissions
    ) -> PayableOperation[None]:
        """
        Overwrites the permissions on the given values id.

        This operation requires the user to have "update" permissions on the given values identifier.

        Arguments
        ---------
        values_id
            The identifier of the uploaded values for which permissions should be updated.

        permissions
            The permissions to be set.

        Returns
        -------
        An operation that once invoked will overwrite the permissions for the given values.

        Example
        -------

        .. code-block:: py3

            permissions = Permissions.default_for_user(user_id)
            await client.overwrite_permissions(values_id, permissions).invoke()
        """
        return OverwritePermissionsOperation(self, values_id, permissions).to_payable()

    def update_permissions(
        self, values_id: ValuesId, delta: PermissionsDelta
    ) -> PayableOperation[None]:
        """
        Updates the permissions on the given values id with the given delta. As opposed to
        :meth:`VmClient.overwrite_permissions`, this operation allows granting and revoking individual permissions
        without overwriting the entire set.

        This operation can only be invoked by the owner of the stored values.

        Arguments
        ---------
        values_id
            The identifier of the uploaded values for which permissions should be updated.

        delta
            The permissions to be granted and revoked.

        Returns
        -------
        An operation that once invoked will update the permissions for the given values.

        Example
        -------

        .. code-block:: py3

            # Grant permissions to retrieve these values to `other_user_id`.
            delta = PermissionsDelta(retrieve=PermissionCommand(grant=set([other_user_id])))
            await client.update_permissions(values_id, delta).invoke()
        """
        return UpdatePermissionsOperation(self, values_id, delta).to_payable()

    def retrieve_permissions(
        self, values_id: ValuesId
    ) -> PayableOperation[Permissions]:
        """
        Retrieves the permissions for the given values identifier.

        This operation requires the user to have "retrieve" permissions on the given values identifier.

        Arguments
        ---------
        values_id
            The identifier of the uploaded values for which permissions should be retrieved.

        Returns
        -------
            An operation that once invoked will retrieve the set of permissions currently associated with the values.

        Example
        -------

        .. code-block:: py3

            await client.retrieve_permissions(values_id).invoke()
        """
        return RetrievePermissionsOperation(self, values_id).to_payable()

    def retrieve_values(
        self, values_id: ValuesId
    ) -> PayableOperation[Dict[str, NadaValue]]:
        """
        Retrieves the values with the given identifier, performing unmasking to recover any secrets
        in the given set of values.

        This operation requires the user to have "retrieve" permissions on the given values identifier.

        Arguments
        ---------
        values_id
            The identifier of the uploaded values that should be retrieved.

        Returns
        -------
            An operation that once invoked will retrieve the stored values.

        Example
        -------

        .. code-block:: py3

            await client.retrieve_values(values_id).invoke()
        """
        return RetrieveValuesOperation(self, values_id).to_payable()

    def delete_values(self, values_id: ValuesId) -> DeleteValuesOperation:
        """
        Deletes the values with the given identifier.

        This operation requires the user to have "delete" permissions on the given values identifier.

        Arguments
        ---------
        values_id
            The identifier of the uploaded values that should be deleted.

        Returns
        -------
            An operation that once invoked will delete the stored values.

        Example
        -------

        .. code-block:: py3

            await client.delete_values(values_id).invoke()
        """
        return DeleteValuesOperation(self, values_id)

    def store_program(
        self, program_name: str, program: bytes
    ) -> PayableOperation[ProgramId]:
        """
        Stores a program in the network.

        Stored programs can by default be invoked by anyone, although their identifier is only known to the invoker
        and node operators.

        Arguments
        ---------
        program_name
            The name of the program being uploaded.

        program
            The contents of the `.nada.bin` file generated from an invocation to `pynadac`.

        Returns
        -------
            An operation that once invoked will return an identifier that can be used to reference this program
            in invocations to `compute` and when setting up values permissions for compute operations.

        Example
        -------

        .. code-block:: py3

            contents = open("/tmp/program.nada.bin", "rb").read()
            await client.store_program(program_name="my-test-program", program=contents).invoke()
        """
        return StoreProgramOperation(self, program_name, program).to_payable()

    def compute(
        self,
        program_id: ProgramId,
        input_bindings: List[InputPartyBinding],
        output_bindings: List[OutputPartyBinding],
        values: Mapping[str, NadaValue],
        value_ids: List[ValuesId] | None = None,
    ) -> PayableOperation[ComputeId]:
        """
        Invokes a computation.

        This operation returns immediately as soon as all initial validations for the program invocation are performed.

        The results for a computation should be fetched by output parties via the
        :meth:`VmClient.retrieve_compute_results` function.

        The name of the input and output parties must match the defined parties in the program being invoked.

        Arguments
        ---------
        program_id
            The identifier of the program being invoked.

        input_bindings
            The list of bindings that associate input parties in the program with Nillion user identifiers.

        output_bindings
            The list of bindings that associate output parties in the program with Nillion user identifiers.

        values
            The values to be used as compute time secrets. These values will only be used during the computation and
            will be discarded afterwards.

        value_ids
            The list of value identifiers to be used as inputs to this computation.

        Returns
        -------
            An operation that once invoked will return an identifier that can be used to fetch computation
            results via :meth:`VmClient.retrieve_compute_results`

        Example
        -------

        .. code-block:: py3

            values = {
                "foo": SecretInteger(40),
                "bar": SecretInteger(2),
            }

            # Invoke a program using the given input and output bindings. In this case we are the only party providing
            # inputs and we are the only party receiving outputs.
            compute_id = await client.compute(
                program_id,
                input_bindings=[
                    nillion_client.InputPartyBinding(party_name="Party1", user=client.user_id)
                ],
                output_bindings=[
                    nillion_client.OutputPartyBinding(
                        party_name="Party1", users=[client.user_id]
                    )
                ],
                values=values,
            ).invoke()

            # Now fetch the results.
            results = await client.retrieve_compute_results(compute_id).invoke()
        """
        encrypted_values = self.secret_masker.mask(values)
        classification = self.secret_masker.classify_values(values)
        return ComputeOperation(
            self,
            program_id,
            input_bindings,
            output_bindings,
            encrypted_values,
            classification,
            value_ids,
        ).to_payable()

    def retrieve_compute_results(
        self, compute_id: ComputeId
    ) -> RetrieveComputeResultsOperation:
        """
        Retrieve the results of a compute operation.

        If the compute operation has finished, this will return the result immediately. If the operation is still
        ongoing, this will block until the operation finishes.

        The invoker user must have been set as an output binding in the :meth:`VmClient.compute` invocation. If the
        invoker was bound as an output party, it will only retrieve the subset of the outputs that belong to it
        based on the configured bindings.

        Arguments
        ---------
        compute_id
            The identifier of the compute instance to fetch the results for.

        Returns
        -------
            An operation that once invoked will return the result of the computation.

        Example
        -------

        .. code-block:: py3

            results = await client.retrieve_compute_results(compute_id).invoke()
        """
        return RetrieveComputeResultsOperation(self, compute_id)

    def pool_status(self) -> PayableOperation[List[PreprocessingOffsets]]:
        """
        Fetch the preprocessing pool status.

        Returns
        -------
            The available offsets for every preprocessing element.

        Example
        -------

        .. code-block:: py3

            offsets = await client.pool_status(compute_id)
        """
        return PoolStatusOperation(self).to_payable()

    async def get_payment_receipt(
        self, signed_quote: SignedQuote, tx_hash: str | None
    ) -> SignedReceipt:
        """
        Request to get a payment receipt for a paid operation.

        Arguments
        ---------
        signed_quote
            The quote to get a payment receipt for.

        tx_hash
            The transaction hash where the payment was made.

        Returns
        -------
            A signed receipt that can be used to prove to all nodes that the payment was made.
        """
        request = PaymentReceiptRequest(
            signed_quote=signed_quote, tx_hash=tx_hash or ""
        )
        result = await _invoke_with_retry(
            wrap_party_error("leader", self.leader.payment_service.payment_receipt)
        )(request)
        return result

    async def invoke_store_values(
        self,
        receipt: SignedReceipt,
        encrypted_values: Mapping[PartyId, Mapping[str, EncryptedNadaValue]],
        permissions: Optional[Permissions] = None,
        update_identifier: Optional[ValuesId] = None,
    ) -> ValuesId:
        """
        Invoke a store values operation in the network.

        Arguments
        ---------
        receipt
            A receipt that proves the payment was made.

        encrypted_values
            The values to store.

        ttl_days
            The number of days after which the values should be deleted. The higher this value, the higher the
            operation cost will be.

        permissions
            The permissions to be set for the uploaded values. By default only the uploader will have read and update
            permissions.

        update_identifier
            An identifier of the secret to be updated. If set, this turns this operation into an update.

        Returns
        -------
            The identifier for the uploaded values.

        Example
        -------

        .. code-block:: py3

            values = {
                "foo": SecretInteger(42),
                "bar": Integer(1337),
            }
            await client.store_values(receipt, values, ttl_days=1).invoke()

        .. note:: users should use generally use :meth:`VmClient.store_values` unless the API provided by that function
            doesn't satisfy their use cases.
        """

        if permissions is None:
            permissions = Permissions.defaults_for_user(self.user_id)

        response_futs = []
        for member in self._members:
            values = encrypted_values[member.party_id]
            encoded_values = encrypted_nada_values_to_protobuf(values)
            request = StoreValuesRequest(
                signed_receipt=receipt,
                values=encoded_values,
                permissions=permissions.to_proto(),
                update_identifier=update_identifier.bytes if update_identifier else b"",
            )
            response_futs.append(
                _invoke_with_retry(
                    wrap_party_error(
                        member.party_id, member.values_service.store_values
                    )
                )(request)
            )

        responses = await asyncio.gather(*response_futs)
        result = _check_responses_equals(responses)
        return ValuesId(bytes=result.values_id)

    async def invoke_overwrite_permissions(
        self, receipt: SignedReceipt, permissions: Permissions
    ):
        """
        Invokes an overwrite permissions operation for the given values id.

        Arguments
        ---------
        receipt
            A receipt that proves the payment was made.

        values_id
            The identifier of the uploaded values for which permissions should be updated.

        permissions
            The permissions to be set.

        Example
        -------

        .. code-block:: py3

            permissions = Permissions.default_for_user(user_id)
            await client.overwrite_permissions(receipt, values_id, permissions).invoke()

        .. note:: users should use generally use :meth:`VmClient.overwrite_permissions` unless the API provided by
            that function doesn't satisfy their use cases.
        """
        response_futs = []
        for member in self._members:
            request = OverwritePermissionsRequest(
                signed_receipt=receipt, permissions=permissions.to_proto()
            )
            response_futs.append(
                _invoke_with_retry(
                    wrap_party_error(
                        member.party_id,
                        member.permissions_service.overwrite_permissions,
                    )
                )(request)
            )

        await asyncio.gather(*response_futs)

    async def invoke_update_permissions(
        self, receipt: SignedReceipt, delta: PermissionsDelta
    ):
        """
        Invokes an updates the permissions on the given values.

        Arguments
        ---------
        receipt
            A receipt that proves the payment was made.

        values_id
            The identifier of the uploaded values for which permissions should be updated.

        delta
            The permissions to be granted and revoked.

        Example
        -------

        .. code-block:: py3

            # Grant permissions to retrieve these values to `other_user_id`.
            delta = PermissionsDelta(retrieve=PermissionCommand(grant=set([other_user_id])))
            await client.update_permissions(receipt, values_id, delta).invoke()

        .. note:: users should use generally use :meth:`VmClient.update_permissions` unless the API provided by
            that function doesn't satisfy their use cases.
        """
        response_futs = []
        for member in self._members:
            request = UpdatePermissionsRequest(
                signed_receipt=receipt,
                retrieve=delta.retrieve.to_proto(),
                update=delta.update.to_proto(),
                delete=delta.delete.to_proto(),
                compute=delta.compute.to_proto(),
            )
            response_futs.append(
                _invoke_with_retry(
                    wrap_party_error(
                        member.party_id, member.permissions_service.update_permissions
                    )
                )(request)
            )

        await asyncio.gather(*response_futs)

    async def invoke_retrieve_permissions(self, receipt: SignedReceipt) -> Permissions:
        """
        Invokes a retrieve permissions operation in the network.

        Arguments
        ---------
        receipt
            A receipt that proves the payment was made.

        values_id
            The identifier of the uploaded values for which permissions should be retrieved.

        Returns
        -------
            The set of permissions currently associated with the values.

        Example
        -------

        .. code-block:: py3

            await client.retrieve_permissions(receipt, values_id).invoke()

        .. note:: users should use generally use :meth:`VmClient.retrieve_permissions` unless the API provided by
            that function doesn't satisfy their use cases.
        """
        response_futs = []
        for member in self._members:
            request = RetrievePermissionsRequest(signed_receipt=receipt)
            response_futs.append(
                _invoke_with_retry(
                    wrap_party_error(
                        member.party_id, member.permissions_service.retrieve_permissions
                    )
                )(request)
            )

        responses = await asyncio.gather(*response_futs)
        responses = [Permissions.from_proto(response) for response in responses]
        response = _check_responses_equals(responses)
        return response

    async def invoke_retrieve_values(
        self, receipt: SignedReceipt
    ) -> Dict[str, NadaValue]:
        """
        Invokes a retrieve values operation.

        Arguments
        ---------
        receipt
            A receipt that proves the payment was made.

        values_id
            The identifier of the uploaded values that should be retrieved.

        Returns
        -------
            The stored values.

        Example
        -------

        .. code-block:: py3

            await client.retrieve_values(receipt, values_id).invoke()

        .. note:: users should use generally use :meth:`VmClient.retrieve_values` unless the API provided by
            that function doesn't satisfy their use cases.
        """
        party_jar = self.secret_masker.build_jar()
        response_futs = []

        async def retrieve_values(receipt, member):
            request = RetrieveValuesRequest(signed_receipt=receipt)
            response = await _invoke_with_retry(
                wrap_party_error(member.party_id, member.values_service.retrieve_values)
            )(request)
            return member.party_id, response

        for member in self._members:
            response_futs.append(retrieve_values(receipt, member))

        responses = await asyncio.gather(*response_futs)

        for party_id, result in responses:
            encrypted_values = dict(
                (v.name, encrypted_nada_value_from_protobuf(v.value))
                for v in result.values
            )
            party_jar.add_element(party_id, encrypted_values)

        return self.secret_masker.unmask(party_jar)

    async def invoke_delete_values(self, values_id: ValuesId) -> None:
        """
        Invoke a delete values operation in the network.

        Arguments
        ---------
        receipt
            A receipt that proves the payment was made.

        values_id
            The identifier of the uploaded values that should be deleted.

        Example
        -------

        .. code-block:: py3

            await client.delete_values(receipt, values_id).invoke()

        .. note:: users should use generally use :meth:`VmClient.delete_values` unless the API provided by
            that function doesn't satisfy their use cases.
        """
        response_futs = []
        for member in self._members:
            request = DeleteValuesRequest(values_id=values_id.bytes)
            response_futs.append(
                _invoke_with_retry(
                    wrap_party_error(
                        member.party_id, member.values_service.delete_values
                    )
                )(request)
            )

        await asyncio.gather(*response_futs)

    async def invoke_store_program(
        self, receipt: SignedReceipt, program: bytes
    ) -> ProgramId:
        """
        Invokes a store program operation in the network.

        Arguments
        ---------
        receipt
            A receipt that proves the payment was made.

        program_name
            The name of the program being uploaded.

        program
            The contents of the `.nada.bin` file generated from an invocation to `pynadac`.

        Returns
        -------
            The stored program's identifier.

        Example
        -------

        .. code-block:: py3

            contents = open("/tmp/program.nada.bin", "rb").read()
            await client.store_program(receipt, program_name="my-test-program", program=contents).invoke()

        .. note:: users should use generally use :meth:`VmClient.store_program` unless the API provided by
            that function doesn't satisfy their use cases.
        """
        response_futs = []
        for member in self._members:
            request = StoreProgramRequest(program=program, signed_receipt=receipt)
            response_futs.append(
                _invoke_with_retry(
                    wrap_party_error(
                        member.party_id, member.programs_service.store_program
                    )
                )(request)
            )

        responses = await asyncio.gather(*response_futs)
        result = _check_responses_equals(responses)
        return ProgramId(result.program_id)

    async def invoke_compute(
        self,
        receipt: SignedReceipt,
        input_bindings: List[InputPartyBinding],
        output_bindings: List[OutputPartyBinding],
        encrypted_party_values: Mapping[PartyId, Mapping[str, EncryptedNadaValue]],
        value_ids: List[ValuesId] | None = None,
    ) -> ComputeId:
        """
        Invokes a compute operation in the network.

        Arguments
        ---------
        receipt
            A receipt that proves the payment was made.

        program_id
            The identifier of the program being invoked.

        input_bindings
            The list of bindings that associate input parties in the program with Nillion user identifiers.

        output_bindings
            The list of bindings that associate output parties in the program with Nillion user identifiers.

        encrypted_party_values
            The values to be used as compute time secrets. These values will only be used during the computation and
            will be discarded afterwards.

        value_ids
            The list of value identifiers to be used as inputs to this computation.

        Returns
        -------
            An identifier for the compute operation.

        Example
        -------

        .. code-block:: py3

            values = {
                "foo": SecretInteger(40),
                "bar": SecretInteger(2),
            }

            # Invoke a program using the given input and output bindings. In this case we are the only party providing
            # inputs and we are the only party receiving outputs.
            compute_id = await client.compute(
                program_id,
                input_bindings=[
                    nillion_client.InputPartyBinding(party_name="Party1", user=client.user_id)
                ],
                output_bindings=[
                    nillion_client.OutputPartyBinding(
                        party_name="Party1", users=[client.user_id]
                    )
                ],
                values=values,
            ).invoke()

            # Now fetch the results.
            results = await client.retrieve_compute_results(receipt, compute_id).invoke()

        .. note:: users should use generally use :meth:`VmClient.compute` unless the API provided by
            that function doesn't satisfy their use cases.
        """

        value_ids = value_ids or []
        response_futs = []
        for member in self._members:
            encrypted_values = encrypted_party_values[member.party_id]
            request = InvokeComputeRequest(
                signed_receipt=receipt,
                value_ids=[values_id.bytes for values_id in value_ids],
                values=encrypted_nada_values_to_protobuf(encrypted_values),
                input_bindings=[binding.to_proto() for binding in input_bindings],
                output_bindings=[binding.to_proto() for binding in output_bindings],
            )
            response_futs.append(
                _invoke_with_retry(
                    wrap_party_error(
                        member.party_id, member.compute_service.invoke_compute
                    )
                )(request)
            )

        responses = await asyncio.gather(*response_futs)
        result = _check_responses_equals(responses)
        return ComputeId(bytes=result.compute_id)

    async def invoke_retrieve_compute_results(
        self, compute_id: ComputeId
    ) -> Dict[str, NadaValue]:
        """
        Invoke a retrieve compute results operation in the network.

        Arguments
        ---------
        receipt
            A receipt that proves the payment was made.

        compute_id
            The identifier of the compute instance to fetch the results for.

        Returns
        -------
            The result of the computation.

        Example
        -------

        .. code-block:: py3

            results = await client.retrieve_compute_results(receipt, compute_id).invoke()

        .. note:: users should use generally use :meth:`VmClient.retrieve_compute_results` unless the API provided by
            that function doesn't satisfy their use cases.
        """

        async def retrieve_results(
            compute_id: ComputeId, member: _ClusterMember
        ) -> tuple[PartyId, Mapping[str, EncryptedNadaValue]]:
            request = RetrieveResultsRequest(compute_id=compute_id.bytes)
            response_stream = member.compute_service.retrieve_results(request)
            async for response in response_stream:
                match response:
                    case RetrieveResultsResponse(waiting_computation=_):
                        continue
                    case RetrieveResultsResponse(success=result):
                        encrypted_values = dict(
                            (v.name, encrypted_nada_value_from_protobuf(v.value))
                            for v in result.values
                        )
                        return member.party_id, encrypted_values
                    case RetrieveResultsResponse(error=error):
                        raise RuntimeError(f"Received error from cluster: {error}")
            raise Exception("Unreachable")

        results = await asyncio.gather(
            *[
                _invoke_with_retry(wrap_party_error(member.party_id, retrieve_results))(
                    compute_id, member
                )
                for member in self._members
            ]
        )

        party_jar = self.secret_masker.build_jar()
        for party_id, encrypted_values in results:
            party_jar.add_element(party_id, encrypted_values)

        return self.secret_masker.unmask(party_jar)

    async def invoke_pool_status(
        self, receipt: SignedReceipt
    ) -> List[PreprocessingOffsets]:
        """
        Invokes a preprocessing pool status operation in the network.

        Arguments
        ---------
        receipt
            A receipt that proves the payment was made.

        .. note:: users should use generally use :meth:`VmClient.pool_status` unless the API provided by
            that function doesn't satisfy their use cases.
        """

        request = PoolStatusRequest(signed_receipt=receipt)
        result = await _invoke_with_retry(
            wrap_party_error("leader", self.leader.leader_queries_service.pool_status)
        )(request)
        return result.offsets

    async def balance(self) -> AccountBalanceResponse:
        """
        Gets the balance associated with the user's account in the network.

        This balance will be preferred when running operations and can be topped up by calling
        :meth:`VmClient.add_funds`.
        """
        return await _invoke_with_retry(
            wrap_party_error("leader", self.leader.payment_service.account_balance)
        )(Empty())

    async def add_funds(self, amount_unil: int, target_user: UserId | None = None):
        """
        Add funds to a user's account on the nillion network.

        By default this will fund the account tied to the user this client is currently using.

        Funds will be automatically used when performing payments unless the payment mode in the client is
        changed.

        .. note:: Funds will expire after 30 days regardless of use so don't add more funds than you intend to use
            in the short term
        """
        payments_config = await _invoke_with_retry(
            wrap_party_error("leader", self.leader.payment_service.payments_config)
        )(Empty())
        if amount_unil < payments_config.minimum_add_funds_payment:
            raise Exception(
                f"can't add less than {payments_config.minimum_add_funds_payment} unil"
            )
        nonce = secrets.token_bytes(32)
        payload = AddFundsPayload(
            recipient=(target_user or self.user_id).to_proto(),
            nonce=nonce,
            leader_public_key=self.cluster.leader.public_key,
        ).SerializeToString()
        payload_hash = hashlib.sha256(payload).digest()
        tx_hash = await self._payer.submit_payment(amount_unil, payload_hash)
        request = AddFundsRequest(payload, tx_hash)
        await _invoke_with_retry(
            wrap_party_error("leader", self.leader.payment_service.add_funds)
        )(request)

    def close(self):
        """
        Closes the client and releases all resources associated with it.
        """
        for member in self._members:
            member.channel.close()
        self.leader.channel.close()

    def __del__(self):
        self.close()

    def _compute_values_size(
        self, encrypted_values: Mapping[PartyId, Mapping[str, EncryptedNadaValue]]
    ) -> int:
        first = next(iter(encrypted_values.values()))
        proto_values = encrypted_nada_values_to_protobuf(first)
        return sum(
            [len(p.name) + len(p.value.SerializeToString()) for p in proto_values]
        )
