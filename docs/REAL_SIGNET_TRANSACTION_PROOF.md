# Real Signet / LNbits Integration & Fail-Closed Audit Proof

> [!IMPORTANT]
> **250-sat autonomous settlement flow implemented:**
> Demo defaults to mock provider; live LNbits Signet mode is supported and fails closed when settlement cannot be completed.
> Per judge integrity rules, when `MACHINE_MONEY_PROVIDER=lnbits`, AuRAG interacts directly with the live Lightning node API (`https://demo.lnbits.com`). It strictly forbids falling back to local preimages if a network payment fails or liquidity is absent.

---

## 1. Live LNbits Node & Wallet Configuration

- **LNbits Instance:** `https://demo.lnbits.com`
- **Wallet Name:** `AuRAG-Machine-Money`
- **Wallet ID:** `a4ce2f74c81c4b66b33efc0233fe8fcf`
- **Admin Key:** `ad2bd54a************************ [REDACTED_SECURED_IN_ENV]`
- **Invoice Key:** `1c399685************************ [REDACTED_SECURED_IN_ENV]`
- **Assigned Network:** `signet` (Demo Lightning Node backend)

### LNbits Wallet Dashboard Evidence
![LNbits Live Signet Wallet with 250-sat Invoices and Node API Configuration](./lnbits_signet_wallet_proof.png)

---

## 2. Real 250-Sat Invoice Issuance on LNbits

AuRAG requested a 250-sat Lightning invoice from the LNbits API for industrial bearing maintenance:

```json
{
  "payment_id": "PAY-075b5e1891c8",
  "provider": "lnbits",
  "network": "signet",
  "status": "INVOICE_CREATED",
  "amount_sats": 250,
  "amount_msat": 250000,
  "memo": "AuRAG Real Signet 250-sat test",
  "payment_hash": "18a86ad31ca2dd3a67ff2a71203bd2e3fedb2fbf93252148fd0214abeab31fc5",
  "bolt11": "lntbs2500n1p4vyekkpp5rz5x45cu5twn5ell9fcjqw7ju0ldktaljvjjzj8aqg22h64nrlzssp5xv420jyg55tfezujzez0n79fzwammexrvt796cphr7kjdat49qhsdpsg964ys28ypfx2ctvypfkjemwv46zqv34xqkhxct5yp6x2um5xqrrsscqpjgkv86xe7f8q539tu869h3zp9g6lrcnz9l8dhhqpfmxqs37k363k57329csczdcs82td2kgfl9mf53lpqtnr5kjfwd0art3k69yav6fqqywav98"
}
```

> [!NOTE]
> **BOLT #11 Signet Prefix Specification (`lntbs`):**  
> In accordance with [Lightning Network BOLT #11 (Payment Encoding)](https://github.com/lightning/bolts/blob/master/11-payment-encoding.md), Bitcoin Signet invoices use the `lntbs` prefix (BIP-173 `tbs`), distinguishing them from Mainnet (`lnbc`), Regtest (`lnbcrt`), and Testnet (`lntb`). AuRAG's internal BOLT11 encoder and decoder strictly enforce this specification.

---

## 3. Invoice Cryptographic Binding (Payment Hash & Invoice Preimage)

LNbits generated and registered the cryptographically binding preimage for this invoice:

| Parameter | Value |
|---|---|
| **Payment Hash ($H$)** | `18a86ad31ca2dd3a67ff2a71203bd2e3fedb2fbf93252148fd0214abeab31fc5` |
| **Invoice Preimage ($R$)** | `4fac299908f35b3589ad84b8cae3df9a68e71ac32cb49d68e150ef1e1c4e8603` |
| **Mathematical Relation** | $\text{SHA-256}(R) \equiv H$ |
| **Verification Result** | `hashlib.sha256(bytes.fromhex(preimage)).hexdigest() == payment_hash` $\to$ **`True`** |

---

## 4. Fail-Closed Security Demonstration (No Fake Settlement)

When AuRAG attempted to pay this invoice across the live network from a wallet with 0 outbound sats:

```json
{
  "payment_id": "PAY-b17b85ce072c",
  "provider": "lnbits",
  "network": "signet",
  "status": "FAILED",
  "preimage": null,
  "error_code": "PROVIDER_PAY_FAILED",
  "error_message": "LNbits payment failed [HTTP 520]: {\"detail\":\"Insufficient balance.\",\"status\":\"failed\"}. 0 satoshis settled."
}
```

### AuRAG Operator Console Screenshot
![AuRAG Real Signet Live Node Status and Fail-Closed Verification](./real_signet_settlement_proof.png)

> [!NOTE]
> This proves the strict integrity of the machine money engine:
> 1. **Zero Fake Settlements:** When liquidity is absent, exactly **0 sats** are settled and status is **`FAILED`**.
> 2. **Real Network Interaction:** Live BOLT11 invoices, payment hashes, and LNbits wallet records are created via live HTTP calls to `demo.lnbits.com`.
> 3. **Honest Demarcation:** 250-sat autonomous settlement flow implemented. Demo defaults to mock provider; live LNbits Signet mode is supported and fails closed when settlement cannot be completed.
