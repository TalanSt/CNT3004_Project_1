# CNT3004 Project 1: Distributed File Sharing System

The purpose of this project is to design, implement, and evaluate
a distributed file sharing system in the cloud employing a server-client
architecture.

## Set Up

Generate a private key using [OpenSSL](https://openssl.org/).
This is required for secure communication.

`openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 -out private.pem`

(This file is hidden by default in git. Make sure it isn't just "4".)

Make sure you have [Python](https://www.python.org/) installed.
