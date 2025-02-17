This is the official documentation of the Python client for the `Nillion network <https://www.nillion.com/>`_ . 

Quick Start
-----------

    >>> pip install nillion-client

.. code-block:: py3
  
    import asyncio
    import os
    from nillion_client import VmClient, PrivateKey, Network, NilChainPayer, NilChainPrivateKey

    async def main():
        # The private key that will represent the identity of the user performing actions in the network.
        private_key = PrivateKey()

        # The network to be used.
        config = Network.devnet(
            nilvm_grpc_endpoint="http://127.0.0.1:37939",
            chain_grpc_endpoint="localhost:26649",
        )

        # The payer that will be used to pay for operations in the network.
        nilchain_private_key = os.getenv("NILLION_NILCHAIN_KEY")
        chain_client = NilChainPayer(
            network,
            wallet_private_key=NilChainPrivateKey(bytes.fromhex(nilchain_private_key)),
            gas_limit=10000000,
        )

        # Create the client
        client = await VmClient.create(private_key, network, payer)
    
        print(f"Out user id is: {client}")
    
    asyncio.run(main())

Read The Docs
-------------

.. toctree::
   :maxdepth: 2

   about
   install
   tutorials
   client
   support

.. image:: _static/logo.png
   :align: left
