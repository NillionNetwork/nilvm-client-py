from dataclasses import dataclass
import yaml
import os


@dataclass
class Network:
    """
    The network class contains network settings for the VmClient.
    """

    chain_id: str
    chain_grpc_endpoint: str
    nilvm_grpc_endpoint: str

    @classmethod
    def devnet(
        cls,
        nilvm_grpc_endpoint: str,
        chain_grpc_endpoint: str,
    ) -> "Network":
        """
        Initializes a network configuration compatible with a Nillion devnet.

        By default the devnet starts without any SSL configuration so all of the `tls_*` parameters are not required.

        Arguments
        ---------
        nilvm_grpc_endpoint
            The Nillion network bootnode endpoint.

        chain_grpc_endpoint
            The nilchain gRPC endpoint.

        Example
        -------

        .. code-block:: py3

            config = Network.devnet(
                nilvm_grpc_endpoint="http://127.0.0.1:37939",
                chain_grpc_endpoint="localhost:26649",
            )

        """
        return cls(
            chain_id="nillion-chain-devnet",
            chain_grpc_endpoint=chain_grpc_endpoint,
            nilvm_grpc_endpoint=nilvm_grpc_endpoint,
        )

    @classmethod
    def from_config(cls, network_name: str) -> "Network":
        """
        Load a network configuration from the filesystem.

        This looks up a network configuration under `~/.config/nillion/networks`. This allows easily loading
        pre-existing network configurations, like the one dumped by `nillion-devnet` when it starts.

        Arguments
        ---------
        network_name
            The name of the network to be loaded.

        Example
        -------

        .. code-block:: py3

            config = Network.from_config("devnet")
        """
        config_home = _config_path_root()
        devnet_path = os.path.join(config_home, f"nillion/networks/{network_name}.yaml")
        try:
            with open(devnet_path) as fd:
                config = yaml.safe_load(fd)
        except Exception as ex:
            raise NetworkConfigLoadError(f"could not load configuration: {ex}")

        payments_config = config["payments"]
        nilvm_grpc_endpoint = config["bootnode"]
        chain_grpc_endpoint = payments_config["nilchain_grpc_endpoint"]
        chain_id = payments_config["nilchain_chain_id"]
        if not chain_grpc_endpoint:
            raise NetworkConfigLoadError("chain gRPC endpoint not set")
        if not chain_id:
            raise NetworkConfigLoadError("chain id")
        return cls(
            chain_id=chain_id,
            nilvm_grpc_endpoint=nilvm_grpc_endpoint,
            chain_grpc_endpoint=chain_grpc_endpoint,
        )


def _config_path_root() -> str:
    config_home = os.getenv("XDG_CONFIG_HOME")
    if not config_home:
        home = os.getenv("HOME")
        if not home:
            raise NetworkConfigLoadError("could not find configurations directory")
        config_home = os.path.join(home, ".config")
    return config_home


class NetworkConfigLoadError(Exception):
    """
    An exception raised when loading a network configuration.
    """

    pass
