# Duo Low-MFA Users Report

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Duo Admin API](https://img.shields.io/badge/Cisco%20Duo-Admin%20API-brightgreen)

A Python script that lists **all Cisco Duo users who have fewer than 2 MFA devices** (configurable). It uses the official [`duo_client_python`](https://github.com/duosecurity/duo_client_python) library and the Duo **Admin API**.

Use it to find users with a single point of failure in their MFA setup, such as one phone and no backup authenticator.

---

## Table of Contents

- [Features](#features)
- [What Counts as an MFA Device](#what-counts-as-an-mfa-device)
- [Requirements](#requirements)
- [Duo Admin API Setup](#duo-admin-api-setup)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Sample Output](#sample-output)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- Retrieves **all** users from Duo, with pagination handled automatically.
- Counts every enrolled MFA device type per user.
- Identifies each user by their **unique Duo username**. Display names are not unique and may be empty.
- Lists the user's **username, email, status, device count, and device breakdown**.
- Lets you set the minimum device count with `--min-devices` (default: `2`).
- Can export results to **CSV** with `--csv`.
- Accepts credentials as **environment variables** or **command-line arguments**.
- Shows clear error messages for missing credentials, API errors, and connection problems.

---

## What Counts as an MFA Device

| Device type (API field)    | Description                                      |
|----------------------------|--------------------------------------------------|
| `phones`                   | Mobile phones, landlines, tablets                |
| `tokens`                   | Hardware OTP tokens                              |
| `webauthncredentials`      | Security keys, Touch ID, Windows Hello, etc.     |
| `u2ftokens`                | Legacy U2F security keys                         |
| `desktoptokens`            | Legacy Duo Desktop tokens                        |
| `desktop_authenticators`   | Duo Desktop authenticators                       |

> **Note:** Bypass codes are **not** counted as MFA devices.

---

## Requirements

- Python **3.8+**
- [`duo_client`](https://pypi.org/project/duo-client/) Python library
- A Duo **Admin API** application with the **"Grant read resource"** permission

---

## Duo Admin API Setup

1. Log in to the **Duo Admin Panel**.
2. Go to **Applications → Protect an Application**.
3. Search for **Admin API** and click **Protect**.
4. Under **Permissions**, enable **Grant read resource**. Leave all other permissions disabled.
5. Click **Save Changes**.
6. Copy the following values:
   - **Integration key** (`ikey`)
   - **Secret key** (`skey`)
   - **API hostname**, for example `api-xxxxxxxx.duosecurity.com`

> Only an **Owner** role administrator can create an Admin API application.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

# (Recommended) Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**`requirements.txt`**

```text
duo_client
```

---

## Configuration

Set your credentials as environment variables. This is the recommended method.

**Linux / macOS**

```bash
export DUO_IKEY="DIXXXXXXXXXXXXXXXXXX"
export DUO_SKEY="your_secret_key"
export DUO_HOST="api-xxxxxxxx.duosecurity.com"
```

**Windows (PowerShell)**

```powershell
$env:DUO_IKEY = "DIXXXXXXXXXXXXXXXXXX"
$env:DUO_SKEY = "your_secret_key"
$env:DUO_HOST = "api-xxxxxxxx.duosecurity.com"
```

---

## Usage

```bash
# Default: list users with fewer than 2 MFA devices
python3 duo_low_mfa_users.py

# Also export the results to CSV
python3 duo_low_mfa_users.py --csv low_mfa_users.csv

# Custom threshold (e.g. fewer than 3 devices)
python3 duo_low_mfa_users.py --min-devices 3

# Pass credentials as arguments instead of environment variables
python3 duo_low_mfa_users.py --ikey DIXXX --skey xxx --host api-xxxx.duosecurity.com
```

### Command-line Options

| Option            | Description                                   | Default            |
|-------------------|-----------------------------------------------|--------------------|
| `--ikey`          | Admin API integration key                     | `$DUO_IKEY`        |
| `--skey`          | Admin API secret key                          | `$DUO_SKEY`        |
| `--host`          | Admin API hostname (without `https://`)       | `$DUO_HOST`        |
| `--min-devices`   | Minimum required number of MFA devices        | `2`                |
| `--csv FILE`      | Also write the results to a CSV file          | *(disabled)*       |
| `-h`, `--help`    | Show the help message                         |                    |

---

## Sample Output

```text
Total users checked: 152
Users with fewer than 2 MFA device(s): 3

Username                       Email                                    Status       Devices  Details
-----------------------------------------------------------------------------------------------------
jdoe                           john.doe@example.com                     active       0        none
jsmith                         jane.smith@example.com                   active       1        phones=1
pkovacs                        peter.kovacs@example.com                 bypass       1        webauthncredentials=1
```

Results are sorted by device count (ascending), then alphabetically by username.

### CSV Format

```csv
username,email,status,device_count,details
jdoe,john.doe@example.com,active,0,none
jsmith,jane.smith@example.com,active,1,phones=1
pkovacs,peter.kovacs@example.com,bypass,1,webauthncredentials=1
```

> Users of all statuses are included: `active`, `bypass`, `disabled`, and `locked out`. To report only active users, add `if u.get("status") != "active": continue` at the beginning of the user loop.

---

## Troubleshooting

| Error / Symptom                         | Cause / Fix                                                                 |
|-----------------------------------------|-----------------------------------------------------------------------------|
| `duo_client is not installed`           | Run `pip install -r requirements.txt` in the active environment.            |
| `Missing credentials: --ikey ...`       | Set `DUO_IKEY`, `DUO_SKEY`, `DUO_HOST` or pass them as arguments.           |
| `40301 Access forbidden`                | The Admin API app lacks the **"Grant read resource"** permission.           |
| `40101 Invalid signature` / `40103`     | Wrong `ikey`/`skey`, or the system clock is off. Sync time via NTP.         |
| Connection / SSL / DNS error            | Check `DUO_HOST`. Use the hostname only, without `https://`. Check proxy/firewall. |
| `429 Too Many Requests`                 | Rate limit hit. The library retries automatically. Rerun later if needed.   |
| `(no email)` in output                  | The user has no email set in Duo. Update it in the Admin Panel or your directory sync. |
| Long usernames are cut off in console   | The console column is 30 characters wide. The CSV export always contains the full username. |
| Script is slow on large tenants         | This is expected. Every user is fetched through paginated API calls.        |

---

## Security Notes

- **Never commit credentials** to the repository. Use environment variables or a secrets manager.
- Add a `.gitignore` entry for local env files and CSV reports:
  ```gitignore
  .env
  *.csv
  venv/
  ```
- Grant the Admin API application **read-only** permission and nothing more.
- Generated CSV files contain personal data (usernames, emails). Handle them according to your organization's data protection policy, such as GDPR.

---

## Contributing

Contributions are welcome:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push the branch: `git push origin feature/my-feature`
5. Open a Pull Request.

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## Disclaimer

This is an independent project and is not officially supported by Cisco or Duo Security. Use it at your own risk and test it in a non-production environment first.
