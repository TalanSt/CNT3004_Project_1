from os.path import isfile

from cryptography.hazmat.primitives import serialization


def main():
    PRIVATE_KEY = None

    if not isfile("private.pem"):
        print("A private key has not been made yet, and/or it is in the wrong location `private.pem`. Exiting.")
        return

    with open("private.pem", "rb") as f:
        key_data = f.read()
        PRIVATE_KEY = serialization.load_pem_private_key(
            key_data,
            password=None
        )


if __name__ == "__main__":
    main()
