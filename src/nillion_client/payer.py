import logging
from abc import ABCMeta, abstractmethod

from cosmpy.aerial.client import LedgerClient, prepare_and_broadcast_basic_transaction
from cosmpy.aerial.config import NetworkConfig
from cosmpy.aerial.tx import Transaction
from cosmpy.aerial.wallet import LocalWallet
from cosmpy.crypto.address import Address
from cosmpy.crypto.keypairs import PrivateKey
from nillion_client_proto.nillion.meta.v1.tx_pb2 import MsgPayFor, Amount

from . import Network

logger = logging.getLogger(__name__)

DEFAULT_QUERY_TIMEOUT_SECONDS = 30
DEFAULT_QUERY_POLL_SECONDS = 1


class Payer(metaclass=ABCMeta):
    """
    An abstraction over the mechanism to perform payments for operations in the Nillion network.
    """

    @abstractmethod
    async def submit_payment(
        self, amount: int, resource: bytes, gas_limit: int | None = None
    ) -> str:
        """
        Submits a payment to the chain.

        This must submit a `MsgPayFor` transaction in nilchain using the given resource as a parameter.

        Arguments
        ---------
        amount
            The amount of unil that needs to be paid.

        resource
            The resource to pay for.

        gas_limit
            The gas limit to set for this operation.
        """
        pass

    @staticmethod
    def prepare_msg(resource: bytes, address: str, amount: int) -> MsgPayFor:
        """
        Create a `MsgPayFor` transaction.

        Arguments
        ---------
        resource
            The resource to pay for.

        address
            The address of the payment sender.

        amount
            The amount of unil that needs to be paid.
        """
        return MsgPayFor(
            resource=resource,
            from_address=address,
            amount=[Amount(denom="unil", amount=str(amount))],
        )


class NilChainPayer(Payer):
    """
    A payer that uses the nilchain to perform payments.
    """

    def __init__(
        self,
        network: Network,
        wallet_private_key: PrivateKey,
        gas_limit: int,
        wallet_prefix: str = "nillion",
        query_timeout_seconds: int = DEFAULT_QUERY_TIMEOUT_SECONDS,
        query_poll_seconds: int = DEFAULT_QUERY_POLL_SECONDS,
    ):
        """
        Construct a new nilchain client.

        This allows making payments on the Nillion chain for all operations on the Nillion network.

        Arguments
        ---------
        network
            The network the payments should be made in.

        wallet_private_key
            The private key for the wallet to be used for payments.

        gas_limit
            The gas limit to apply to all payments.

        wallet_prefix
            The prefix used for addresses in the used chain.

        query_timeout_seconds
            The timeout when waiting for a transaction to be committed.

        query_poll_seconds
            The poll interval while waiting for a transaction to be committed.

        Example
        -------

        .. code-block:: py3

            chain_client = NilChainPayer(
                network,
                wallet_private_key=NilChainPrivateKey(bytes.fromhex(nilchain_private_key)),
                gas_limit=10000000,
            )
        """

        self.network = network
        self.payments_wallet = LocalWallet(wallet_private_key, wallet_prefix)
        self.gas_limit = gas_limit
        payments_config = NetworkConfig(
            chain_id=network.chain_id,
            url=f"grpc+{network.chain_grpc_endpoint}/",
            fee_minimum_gas_price=0,
            fee_denomination="unil",
            staking_denomination="unil",
            faucet_url=None,
        )
        self.payments_client = LedgerClient(
            payments_config,
            query_interval_secs=query_poll_seconds,
            query_timeout_secs=query_timeout_seconds,
        )

    @property
    def wallet_address(self) -> str:
        """
        Get the address associated with the payer's wallet.
        """
        return str(self.payments_wallet.address())

    async def submit_payment(
        self, amount: int, resource: bytes, gas_limit: int | None = None
    ) -> str:
        transaction = Transaction()
        message = NilChainPayer.prepare_msg(
            resource, str(Address(self.payments_wallet.public_key(), "nillion")), amount
        )
        transaction.add_message(message)

        gas_limit = gas_limit if gas_limit else self.gas_limit
        logger.info(
            "Submitting transaction for %s unil, resource %s", amount, resource.hex()
        )
        submitted_transaction = prepare_and_broadcast_basic_transaction(
            self.payments_client, transaction, self.payments_wallet, gas_limit=gas_limit
        )

        tx_hash = submitted_transaction.tx_hash
        logger.info("Waiting for transaction %s to be committed", tx_hash)
        submitted_transaction.wait_to_complete()

        logger.info("Transaction %s was committed", tx_hash)
        return tx_hash


class DummyPayer(Payer):
    """
    A payer that doesn't support paying.

    This can be used when a client is to be instantiated only to be used for operations that
    don't require payments.
    """

    async def submit_payment(
        self, amount: int, resource: bytes, gas_limit: int | None = None
    ) -> str:
        raise Exception("payments not supported")
