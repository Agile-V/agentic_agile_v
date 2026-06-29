    # Impact Map

    ## Change request

    **CR-AUTH-001:** Modify login endpoint to support multi-factor authentication (MFA) alongside password

    ## Affected components

    | File | Symbol | Impact type | Confidence | Reason |
    |---|---|---|---|---|
    | `src/api/auth.py` | `—` | modify | high | Keyword match in name/path/summary for change: 'Modify login endpoint to support multi-factor authentication (MFA) alongside pas'. |
| `src/api/auth.py` | `login` | modify | high | Keyword match in name/path/summary for change: 'Modify login endpoint to support multi-factor authentication (MFA) alongside pas'. |
| `src/db.py` | `—` | modify | high | Keyword match in name/path/summary for change: 'Modify login endpoint to support multi-factor authentication (MFA) alongside pas'. |
| `tests/test_auth.py` | `—` | modify | high | Keyword match in name/path/summary for change: 'Modify login endpoint to support multi-factor authentication (MFA) alongside pas'. |
| `src/main.py` | `—` | modify | high | Keyword match in name/path/summary for change: 'Modify login endpoint to support multi-factor authentication (MFA) alongside pas'. |
| `src/api/status.py` | `—` | review | medium | Indirect dependency on a directly affected component (≤2 hops). |
| `src/services/token.py` | `—` | review | medium | Indirect dependency on a directly affected component (≤2 hops). |
| `src/main.py` | `create_app` | review | medium | Indirect dependency on a directly affected component (≤2 hops). |
| `src/db.py` | `get_session` | review | medium | Indirect dependency on a directly affected component (≤2 hops). |
| `src/api/auth.py` | `refresh_token` | review | medium | Indirect dependency on a directly affected component (≤2 hops). |
| `src/services/token.py` | `TokenStore` | review | medium | Indirect dependency on a directly affected component (≤2 hops). |

    ## Required regression tests

    - tests/test_auth.py
- tests/test_status.py
- tests/test_token.py

    ## Risk register

    | Risk ID | Description | Severity | Mitigation |
    |---|---|---|---|
    | RISK-001 | Security-sensitive components are in the impact scope. | high | Ensure security regression tests are included and reviewed. |

    ## Overall confidence

    **High**
