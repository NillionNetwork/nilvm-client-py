import re
import logging
from grpclib import GRPCError, Status
from typing import Dict, Optional, List, Union, Generic, TypeVar, TYPE_CHECKING, Mapping
from dataclasses import dataclass

from nillion_client_core import (
    EncryptedNadaValue,
    Integer,
    NadaValuesClassification,
    PartyId,
    SecretInteger,
    SecretUnsignedInteger,
    Boolean,
    SecretBoolean,
    SecretBlob,
    Array,
    UnsignedInteger,
    EcdsaPrivateKey,
    EcdsaDigestMessage,
    EcdsaSignature,
    EcdsaPublicKey,
    EddsaPrivateKey,
    EddsaSignature,
    EddsaPublicKey,
    EddsaMessage,
    StoreId,
)

from google.rpc.error_details_pb2 import PreconditionFailure  # type: ignore
from nillion_client_proto.nillion.payments.v1.quote import SignedQuote, PriceQuote
from nillion_client_proto.nillion.payments.v1.receipt import SignedReceipt
from nillion_client_proto.nillion.leader_queries.v1.pool_status import (
    PreprocessingOffsets,
)
from nillion_client_proto.nillion.compute.v1.invoke import (
    InputPartyBinding as ProtoInputPartyBinding,
    OutputPartyBinding as ProtoOutputPartyBinding,
)
from .errors import PartyError

from .ids import ValuesId, ProgramId, ComputeId, UserId

PROGRAM_NAME_REGEX = re.compile("[a-zA-Z0-9+.:_-]{1,128}")

if TYPE_CHECKING:
    from . import VmClient, Permissions, PermissionsDelta

NadaValue = Union[
    Integer,
    SecretInteger,
    SecretUnsignedInteger,
    Boolean,
    SecretBoolean,
    SecretBlob,
    Array,
    UnsignedInteger,
    EcdsaPrivateKey,
    EcdsaDigestMessage,
    EcdsaSignature,
    EcdsaPublicKey,
    EddsaPrivateKey,
    EddsaSignature,
    EddsaPublicKey,
    EddsaMessage,
    StoreId,
]


@dataclass
class InputPartyBinding:
    """Represents the binding of a named input party in a program to a user id"""

    party_name: str
    user: UserId

    def to_proto(self) -> ProtoInputPartyBinding:
        """Converts an instance to its protobuf representation"""
        return ProtoInputPartyBinding(
            party_name=self.party_name, user=self.user.to_proto()
        )

    @staticmethod
    def from_proto(proto: ProtoInputPartyBinding) -> "InputPartyBinding":
        """Constructs an instance from its protobuf representation"""
        return InputPartyBinding(
            party_name=proto.party_name, user=UserId.from_proto(proto.user)
        )


@dataclass
class OutputPartyBinding:
    """Represents the binding of a named output party in a program to a user id"""

    party_name: str
    users: List[UserId]

    def to_proto(self) -> ProtoOutputPartyBinding:
        """Converts an instance to its protobuf representation"""
        return ProtoOutputPartyBinding(
            party_name=self.party_name, users=[user.to_proto() for user in self.users]
        )

    @staticmethod
    def from_proto(proto: ProtoOutputPartyBinding) -> "OutputPartyBinding":
        """Constructs an instance from its protobuf representation"""
        return OutputPartyBinding(
            party_name=proto.party_name,
            users=[UserId.from_proto(user) for user in proto.users],
        )


class StoreValuesOperation:
    def __init__(
        self,
        client: "VmClient",
        encrypted_values: Mapping[PartyId, Mapping[str, EncryptedNadaValue]],
        classification: NadaValuesClassification,
        ttl_days: int,
        permissions: Optional["Permissions"] = None,
        update_identifier: Optional[ValuesId] = None,
    ):
        self.client = client
        self.encrypted_values = encrypted_values
        self.classification = classification
        self.ttl_days = ttl_days
        self.permissions = permissions
        self.update_identifier = update_identifier

    def to_payable(self) -> "PayableOperation[ValuesId]":
        return PayableOperation(self)

    async def invoke(self, receipt: SignedReceipt) -> ValuesId:
        """
        Invoke this operation.

        Arguments
        ---------
        receipt
            The receipt that proves the payment was made.

        Returns
        -------
            A unique identifier for the values stored.
        """
        return await self.client.invoke_store_values(
            receipt,
            self.encrypted_values,
            permissions=self.permissions,
            update_identifier=self.update_identifier,
        )


class OverwritePermissionsOperation:
    def __init__(
        self, client: "VmClient", values_id: ValuesId, permissions: "Permissions"
    ):
        self.client = client
        self.values_id = values_id
        self.permissions = permissions

    def to_payable(self) -> "PayableOperation[None]":
        return PayableOperation(self)

    async def invoke(self, receipt: SignedReceipt) -> None:
        """
        Invoke this operation.

        Arguments
        ---------
        receipt
            The receipt that proves the payment was made.
        """
        return await self.client.invoke_overwrite_permissions(receipt, self.permissions)


class UpdatePermissionsOperation:
    def __init__(
        self, client: "VmClient", values_id: ValuesId, delta: "PermissionsDelta"
    ):
        self.client = client
        self.values_id = values_id
        self.delta = delta

    def to_payable(self) -> "PayableOperation[None]":
        return PayableOperation(self)

    async def invoke(self, receipt: SignedReceipt) -> None:
        """
        Invoke this operation.

        Arguments
        ---------
        receipt
            The receipt that proves the payment was made.
        """
        return await self.client.invoke_update_permissions(receipt, self.delta)


class RetrievePermissionsOperation:
    def __init__(self, client: "VmClient", values_id: ValuesId):
        self.client = client
        self.values_id = values_id

    def to_payable(self) -> "PayableOperation[Permissions]":
        return PayableOperation(self)

    async def invoke(self, receipt: SignedReceipt) -> "Permissions":
        """
        Invoke this operation.

        Arguments
        ---------
        receipt
            The receipt that proves the payment was made.

        Returns
        -------
            The permissions for the stored values.
        """
        return await self.client.invoke_retrieve_permissions(receipt)


class RetrieveValuesOperation:
    def __init__(self, client: "VmClient", values_id: ValuesId):
        self.client = client
        self.values_id = values_id

    def to_payable(self) -> "PayableOperation[Dict[str, NadaValue]]":
        return PayableOperation(self)

    async def invoke(self, receipt: SignedReceipt) -> Dict[str, NadaValue]:
        """
        Invoke this operation.

        Arguments
        ---------
        receipt
            The receipt that proves the payment was made.

        Returns
        -------
            The stored values in clear.
        """
        return await self.client.invoke_retrieve_values(receipt)


class DeleteValuesOperation:
    def __init__(self, client: "VmClient", values_id: ValuesId):
        self.client = client
        self.values_id = values_id

    async def invoke(self) -> None:
        """
        Invoke this operation.
        """
        return await self.client.invoke_delete_values(self.values_id)


class StoreProgramOperation:
    def __init__(self, client: "VmClient", program_name: str, program: bytes):
        self.client = client
        self.program_name = program_name
        self.program = program
        if not PROGRAM_NAME_REGEX.match(program_name):
            raise Exception("invalid program name")

    def to_payable(self) -> "PayableOperation[ProgramId]":
        return PayableOperation(self)

    async def invoke(self, receipt: SignedReceipt) -> ProgramId:
        """
        Invoke this operation.

        Arguments
        ---------
        receipt
            The receipt that proves the payment was made.

        Returns
        -------
            A unique identifier for the stored program.
        """
        return await self.client.invoke_store_program(receipt, self.program)


class ComputeOperation:
    def __init__(
        self,
        client: "VmClient",
        program_id: ProgramId,
        input_bindings: List[InputPartyBinding],
        output_bindings: List[OutputPartyBinding],
        encrypted_values: Mapping[PartyId, Mapping[str, EncryptedNadaValue]],
        classification: NadaValuesClassification,
        value_ids: List[ValuesId] | None = None,
    ):
        self.client = client
        self.program_id = program_id
        self.input_bindings = input_bindings
        self.output_bindings = output_bindings
        self.classification = classification
        self.encrypted_values = encrypted_values
        self.value_ids = value_ids

    def to_payable(self) -> "PayableOperation[ComputeId]":
        return PayableOperation(self)

    async def invoke(self, receipt: SignedReceipt) -> ComputeId:
        """
        Invoke this operation.

        Arguments
        ---------
        receipt
            The receipt that proves the payment was made.

        Returns
        -------
            A unique identifier for this compute instance.
        """
        return await self.client.invoke_compute(
            receipt,
            self.input_bindings,
            self.output_bindings,
            self.encrypted_values,
            self.value_ids,
        )


class RetrieveComputeResultsOperation:
    def __init__(self, client: "VmClient", compute_id: ComputeId):
        self.client = client
        self.compute_id = compute_id

    async def invoke(self) -> Dict[str, NadaValue]:
        """
        Invoke this operation.

        Returns
        -------
            The results of the computation.
        """
        return await self.client.invoke_retrieve_compute_results(self.compute_id)


class PoolStatusOperation:
    def __init__(self, client: "VmClient"):
        self.client = client

    def to_payable(self) -> "PayableOperation[List[PreprocessingOffsets]]":
        return PayableOperation(self)

    async def invoke(self, receipt: SignedReceipt) -> List[PreprocessingOffsets]:
        """
        Invoke this operation.

        Arguments
        ---------
        receipt
            The receipt that proves the payment was made.

        Returns
        -------
            The preprocessing pool offsets.
        """
        return await self.client.invoke_pool_status(receipt)


Operation = Union[
    StoreValuesOperation,
    OverwritePermissionsOperation,
    RetrievePermissionsOperation,
    RetrieveValuesOperation,
    DeleteValuesOperation,
    UpdatePermissionsOperation,
    StoreProgramOperation,
    ComputeOperation,
    RetrieveComputeResultsOperation,
    PoolStatusOperation,
]

T = TypeVar("T")


class PayableOperation(Generic[T]):
    def __init__(self, operation: Operation):
        self.operation = operation

    async def quote(self) -> "QuotedOperation[T]":
        """
        Get a price quote for this operation.
        """
        quote = await self.operation.client.request_quote(self.operation)
        return QuotedOperation(self.operation, quote)

    async def invoke(self) -> T:
        """
        Invoke this operation.

        This is the equivalent of calling

        .. code-block:: py3

            quoted_op = await operation.quote()
            paid_op = await quoted_op.pay()
            validated_op = await paid_op.validate()
            result = await validated_op.invoke()
        """
        quoted_op = await self.quote()
        paid_op = await quoted_op.pay()
        validated_op = await paid_op.validate()
        return await validated_op.invoke()


class QuotedOperation(Generic[T]):
    def __init__(self, operation: Operation, quote: SignedQuote):
        self.operation = operation
        self.quote = quote

    async def pay(self, *args, **kwargs) -> "PaidOperation[T]":
        """
        Pay for this operation.

        This will use the configured payer on the client to perform the payment.
        """
        from nillion_client.client import PaymentMode

        payment_mode = kwargs.pop("payment_mode", self.operation.client.payment_mode)
        if payment_mode == PaymentMode.PAY_PER_OPERATION:
            price_quote = PriceQuote()
            price_quote.parse(self.quote.quote)
            tx_hash = await self.operation.client._payer.submit_payment(
                price_quote.fees.tokens, price_quote.nonce, *args, **kwargs
            )
            return PaidOperation(self.operation, self.quote, tx_hash)
        elif payment_mode == PaymentMode.FROM_BALANCE:
            return PaidOperation(self.operation, self.quote, None)
        else:
            raise Exception("invalid payment mode")

    async def pay_and_invoke(self, *args, **kwargs) -> T:
        """
        Pay and invoke the operation.
        """
        paid_op = await self.pay(*args, **kwargs)
        validated_op = await paid_op.validate()
        return await validated_op.invoke()


class PaidOperation(Generic[T]):
    def __init__(self, operation: Operation, quote: SignedQuote, tx_hash: str | None):
        self.operation = operation
        self.quote = quote
        self.tx_hash = tx_hash

    async def validate(self) -> "ValidatedOperation[T]":
        try:
            receipt = await self.operation.client.get_payment_receipt(
                self.quote, self.tx_hash
            )
            return ValidatedOperation(self.operation, self.quote, receipt)
        except PartyError as ex:
            ex = ex.__cause__
            if isinstance(ex, GRPCError) and _is_balance_error(ex):
                from nillion_client.client import PaymentMode

                logging.warning(
                    "Not enough balance in network, making single time payment"
                )
                paid_operation = await QuotedOperation(self.operation, self.quote).pay(
                    payment_mode=PaymentMode.PAY_PER_OPERATION
                )
                return await paid_operation.validate()
            else:
                raise


class ValidatedOperation(Generic[T]):
    def __init__(
        self,
        operation: Operation,
        quote: SignedQuote,
        receipt: SignedReceipt,
    ):
        self.operation = operation
        self.quote = quote
        self.receipt = receipt

    async def invoke(self) -> T:
        """
        Invoke the operation.
        """
        return await self.operation.invoke(self.receipt)  # type: ignore


def _is_balance_error(e: GRPCError) -> bool:
    if e.status != Status.FAILED_PRECONDITION:
        return False
    for detail in e.details or []:
        if isinstance(detail, PreconditionFailure):
            for violation in detail.violations:
                if violation.type == "PAYMENT" and violation.subject == "BALANCE":
                    return True
    return False
