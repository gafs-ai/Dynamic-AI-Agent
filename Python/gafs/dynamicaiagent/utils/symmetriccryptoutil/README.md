# Symmetric Crypto Util Component

This component provides symmetric key encryption utilities that can be used
from other parts of the application.


## Component Structure

- **Folder**
  - `utils/symmetriccryptoutil`

- **Files and Public Classes**
  - `symmetric_crypto_util.py`
    - `SymmetricCryptoUtil`
    - `SymmetricCryptoType`
  - `i_symmetric_crypto_provider.py`
    - `ISymmetricCryptoProvider`
  - `aes_256_crypto_provider.py`
    - `Aes256CryptoProvider`
  - `__init__.py`
    - Exposes public API of this component.


## Public API (Methods / Variables)

- **Class `SymmetricCryptoUtil`**
  - `generate_key(crypto_type: SymmetricCryptoType) -> str`
    - Generate a new key for the specified symmetric crypto type.
  - `encrypt(crypto_type: SymmetricCryptoType, raw: str, key: str) -> str`
    - Encrypt UTF-8 text using the specified crypto type and base64-encoded key.
  - `decrypt(crypto_type: SymmetricCryptoType, encrypted: str, key: str) -> str`
    - Decrypt text that was produced by `encrypt`.

- **Enum `SymmetricCryptoType`**
  - `AES_256_GCM`
    - AES-256-GCM symmetric encryption algorithm.


## Dependencies & Libraries

- **PyCryptodome**
  - **Name**: `pycryptodome`
  - **Website**: `https://pycryptodome.readthedocs.io/`
  - **License**: BSD-2-Clause
  - **License URL**: `https://github.com/Legrandin/pycryptodome/blob/master/LICENSE.rst`

## Nuitka build (extension module / DLL)

- **Build**:
  - `cd Python && python gafs/dynamicaiagent/utils/symmetriccryptoutil/build_nuitka.py`
- **Test compiled output (reuses existing tests)**:
  - `cd Python && pytest gafs/dynamicaiagent/utils/symmetriccryptoutil/test/test_build_symmetric_crypto_util.py -v`
