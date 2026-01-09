# Vibe code - Gemini 3
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# Paths match the volume mounts defined in the proposed compose.yml
PRIVATE_KEY_PATH = Path("/auth_data/worker-private-key.pem")
TEMPLATE_PATH = Path("/templates/plerion.json")
OUTPUT_PATH = Path("/keycloak_import/plerion.json")
PLACEHOLDER = "${WORKER_PUBLIC_KEY_PLACEHOLDER}"


def get_clean_public_key(private_key: rsa.RSAPrivateKey) -> str:
    """Derives the public key from a private key object and formats it for Keycloak (no headers/newlines)."""
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return (
        public_key
        .decode("utf-8")
        .replace("-----BEGIN PUBLIC KEY-----", "")
        .replace("-----END PUBLIC KEY-----", "")
        .replace("\n", "")
    )


def main():
    print("--- Auth Init: Starting Key Generation ---")

    # 1. Acquire the Public Key String
    # --------------------------------
    public_key_str = ""

    if PRIVATE_KEY_PATH.exists():
        print(f"Existing private key found at {PRIVATE_KEY_PATH}. Loading...")
        try:
            private_key_bytes = PRIVATE_KEY_PATH.read_bytes()
            loaded_key = serialization.load_pem_private_key(private_key_bytes, password=None)

            # serialization.load_pem_private_key returns a Union of key types.
            # We must assert it is RSA to satisfy strict typing and ensure safety.
            assert isinstance(loaded_key, rsa.RSAPrivateKey), "Loaded key is not an RSA private key"

            public_key_str = get_clean_public_key(loaded_key)
            print("Public key derived successfully.")
        except Exception as e:
            print(f"Error loading existing key: {e}")
            sys.exit(1)
    else:
        print("No private key found. Generating new RSA key pair...")
        generated_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        # Save Private Key (PKCS8 PEM)
        pem = generated_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        PRIVATE_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
        PRIVATE_KEY_PATH.write_bytes(pem)
        print(f"Private key saved to {PRIVATE_KEY_PATH}")

        public_key_str = get_clean_public_key(generated_key)

    # 2. Process the Keycloak Import Template
    # ---------------------------------------
    if not TEMPLATE_PATH.exists():
        print(f"CRITICAL: Template file not found at {TEMPLATE_PATH}")
        sys.exit(1)

    print(f"Reading realm template from {TEMPLATE_PATH}...")
    template_content = TEMPLATE_PATH.read_text(encoding="utf-8")

    if PLACEHOLDER not in template_content:
        print(f"WARNING: Placeholder '{PLACEHOLDER}' not found in template. Key injection may fail.")
    else:
        print("Injecting public key into template...")

    # We perform a string replacement to preserve other Keycloak env vars (like ${PUBLIC_URL})
    final_content = template_content.replace(PLACEHOLDER, public_key_str)

    # 3. Write the Result
    # -------------------
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(final_content, encoding="utf-8")

    print(f"Success: Keycloak import file written to {OUTPUT_PATH}")
    print("--- Auth Init: Complete ---")


if __name__ == "__main__":
    main()
