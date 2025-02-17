What is Nillion Python Client?
===============================

This module defines a Nillion client, that connects to the Nillion network and allows running operations against it.


What can this Nillion Python Client do?
========================================

- Store data on Nillion network with privacy and secrecy.
- Retrieve data from Nillion network, as long as the user has the permissions to do so.
- Delete data from the Nillion network.
- Manage permissions of new or existing secrets or programs on the Nillion network.
- Upload programs to Nillion network.
- Invoke computations with Nillion programs.

What is not supported?
======================

Arbitrary message channels
--------------------------

The Nillion network doesn’t yet have arbitrary message channels, event listeners, or notifications.

This means that sharing user identifiers, notifying a user that a set of values was stored and needs to be used in a computation, and other use cases that require communication between clients is not currently handled by the Nillion client.

Authentication
--------------

Users are in charge of managing their own identity keys.

Secret filtering by tag or label
--------------------------------

The Nillion network does not support tagging or labeling stored values yet, so it is not possible to filter or search for them within the network. Similarly, there is currently no way of listing all the secrets you own or have permissions on.
