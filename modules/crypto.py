#!/usr/bin/env python3
"""
crypto.py

This module provides functions for both symmetric and asymmetric encryption,
using the 'cryptography' package. It is designed to be integrated into a larger
project to implement secure, encrypted communications.

Asymmetric encryption is handled using RSA:
  - Generate RSA key pairs (private and public keys)
  - Serialize and load keys from PEM format
  - Encrypt messages with a public key and decrypt with a private key
  - Optionally, sign messages and verify signatures

Symmetric encryption is handled using Fernet (which uses AES in CBC mode along with HMAC):
  - Generate a symmetric key
  - Encrypt and decrypt messages with the symmetric key

Ensure you have installed the cryptography package:
    pip install cryptography
"""


from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.fernet import Fernet


# ------------------------- Asymmetric Encryption Functions -------------------------

def generate_rsa_keypair(key_size: int = 2048):
    """
    Generate a new RSA private-public key pair.

    :param key_size: Size of the RSA key in bits (default 2048).
    :return: Tuple (private_key, public_key).
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size
    )
    public_key = private_key.public_key()
    return private_key, public_key


def serialize_private_key(private_key, passphrase: bytes = None) -> bytes:
    """
    Serialize an RSA private key to PEM format.

    :param private_key: RSA private key.
    :param passphrase: Optional passphrase for encrypting the private key.
    :return: PEM-formatted private key as bytes.
    """
    encryption_algo = (serialization.BestAvailableEncryption(passphrase)
                       if passphrase else serialization.NoEncryption())
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption_algo
    )
    return pem


def serialize_public_key(public_key) -> bytes:
    """
    Serialize an RSA public key to PEM format.

    :param public_key: RSA public key.
    :return: PEM-formatted public key as bytes.
    """
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem


def load_private_key(pem_data: bytes, passphrase: bytes = None):
    """
    Load an RSA private key from PEM data.

    :param pem_data: PEM-formatted private key.
    :param passphrase: Optional passphrase for decryption.
    :return: RSA private key.
    """
    private_key = serialization.load_pem_private_key(
        pem_data,
        password=passphrase
    )
    return private_key


def load_public_key(pem_data: bytes):
    """
    Load an RSA public key from PEM data.

    :param pem_data: PEM-formatted public key.
    :return: RSA public key.
    """
    public_key = serialization.load_pem_public_key(pem_data)
    return public_key


def asymmetric_encrypt(public_key, message: bytes) -> bytes:
    """
    Encrypt a message using RSA public key.

    :param public_key: RSA public key.
    :param message: Plaintext message as bytes.
    :return: Ciphertext as bytes.
    """
    ciphertext = public_key.encrypt(
        message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return ciphertext


def asymmetric_decrypt(private_key, ciphertext: bytes) -> bytes:
    """
    Decrypt ciphertext using RSA private key.

    :param private_key: RSA private key.
    :param ciphertext: Ciphertext as bytes.
    :return: Decrypted plaintext as bytes.
    """
    plaintext = private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return plaintext


def sign_message(private_key, message: bytes) -> bytes:
    """
    Sign a message using RSA private key.

    :param private_key: RSA private key.
    :param message: Message to sign as bytes.
    :return: Signature as bytes.
    """
    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature


def verify_signature(public_key, message: bytes, signature: bytes) -> bool:
    """
    Verify a message signature using RSA public key.

    :param public_key: RSA public key.
    :param message: Original message as bytes.
    :param signature: Signature as bytes.
    :return: True if valid, raises exception if invalid.
    """
    public_key.verify(
        signature,
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return True


# ------------------------- Symmetric Encryption Functions -------------------------

def generate_symmetric_key() -> bytes:
    """
    Generate a new symmetric key for Fernet encryption.

    :return: Symmetric key as bytes.
    """
    return Fernet.generate_key()


def symmetric_encrypt(key: bytes, message: bytes) -> bytes:
    """
    Encrypt a message using symmetric encryption (Fernet).

    :param key: Symmetric key as bytes.
    :param message: Plaintext message as bytes.
    :return: Ciphertext as bytes.
    """
    fernet = Fernet(key)
    ciphertext = fernet.encrypt(message)
    return ciphertext


def symmetric_decrypt(key: bytes, ciphertext: bytes) -> bytes:
    """
    Decrypt a ciphertext using symmetric encryption (Fernet).

    :param key: Symmetric key as bytes.
    :param ciphertext: Encrypted message as bytes.
    :return: Decrypted plaintext as bytes.
    """
    fernet = Fernet(key)
    plaintext = fernet.decrypt(ciphertext)
    return plaintext


if __name__ == "__main__":
    print("Testing RSA encryption/decryption...")
    private_key, public_key = generate_rsa_keypair()
    original_message = b"Hello, RSA encryption!"
    
    encrypted_message = asymmetric_encrypt(public_key, original_message)
    decrypted_message = asymmetric_decrypt(private_key, encrypted_message)
    assert decrypted_message == original_message
    print("Asymmetric encryption/decryption test passed.")

    print("Testing RSA signature and verification...")
    signature = sign_message(private_key, original_message)
    try:
        valid = verify_signature(public_key, original_message, signature)
        print("Signature verification passed.")
    except Exception as e:
        print("Signature verification failed:", e)

    print("Testing symmetric encryption/decryption...")
    sym_key = generate_symmetric_key()
    original_message_sym = b"Hello, symmetric encryption!"
    
    encrypted_sym = symmetric_encrypt(sym_key, original_message_sym)
    decrypted_sym = symmetric_decrypt(sym_key, encrypted_sym)
    assert decrypted_sym == original_message_sym
    print("Symmetric encryption/decryption test passed.")
