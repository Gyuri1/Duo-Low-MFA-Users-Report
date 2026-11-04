#!/usr/bin/env python3
"""
List all Cisco Duo users who have fewer than N (default: 2) MFA devices.
Users are identified by their unique Duo username.

Counted device types (from the Admin API user object):
  - phones                 (mobile phones, landlines, tablets)
  - tokens                 (hardware OTP tokens)
  - webauthncredentials    (security keys, Touch ID, Windows Hello, etc.)
  - u2ftokens              (legacy U2F keys)
  - desktoptokens          (legacy Duo Desktop tokens)
  - desktop_authenticators (Duo Desktop authenticators)

Bypass codes are NOT counted as MFA devices.
"""

import argparse
import csv
import os
import sys

try:
    import duo_client
except ImportError:
    sys.exit("ERROR: duo_client is not installed. Run: pip install duo_client")

DEVICE_KEYS = (
    "phones",
    "tokens",
    "webauthncredentials",
    "u2ftokens",
    "desktoptokens",
    "desktop_authenticators",
)

CSV_FIELDS = ["username", "email", "status", "device_count", "details"]


def parse_args():
    p = argparse.ArgumentParser(
        description="List Duo users with fewer than N MFA devices."
    )
    p.add_argument("--ikey", default=os.getenv("DUO_IKEY"), help="Admin API integration key (or env DUO_IKEY)")
    p.add_argument("--skey", default=os.getenv("DUO_SKEY"), help="Admin API secret key (or env DUO_SKEY)")
    p.add_argument("--host", default=os.getenv("DUO_HOST"), help="Admin API hostname (or env DUO_HOST)")
    p.add_argument("--min-devices", type=int, default=2, help="Minimum required devices (default: 2)")
    p.add_argument("--csv", metavar="FILE", help="Optional: also write results to this CSV file")
    args = p.parse_args()

    missing = [n for n in ("ikey", "skey", "host") if not getattr(args, n)]
    if missing:
        p.error("Missing credentials: " + ", ".join("--" + m for m in missing)
                + " (or set DUO_IKEY / DUO_SKEY / DUO_HOST)")
    return args


def device_breakdown(user):
    """Return a dict {device_type: count} for a user."""
    return {key: len(user.get(key) or []) for key in DEVICE_KEYS}


def main():
    args = parse_args()
    admin = duo_client.Admin(ikey=args.ikey, skey=args.skey, host=args.host)

    try:
        # Without a limit, get_users() pages through ALL users automatically.
        users = admin.get_users()
    except RuntimeError as e:
        sys.exit(f"ERROR: Duo API call failed: {e}")
    except Exception as e:  # network / SSL / DNS errors
        sys.exit(f"ERROR: Could not connect to Duo ({args.host}): {e}")

    results = []
    for u in users:
        breakdown = device_breakdown(u)
        total = sum(breakdown.values())
        if total < args.min_devices:
            results.append({
                "username": u.get("username") or "(no username)",
                "email": u.get("email") or "(no email)",
                "status": u.get("status", ""),
                "device_count": total,
                "details": ", ".join(f"{k}={v}" for k, v in breakdown.items() if v) or "none",
            })

    results.sort(key=lambda r: (r["device_count"], r["username"].lower()))

    # Console output
    print(f"Total users checked: {len(users)}")
    print(f"Users with fewer than {args.min_devices} MFA device(s): {len(results)}\n")
    if results:
        header = f"{'Username':<30} {'Email':<40} {'Status':<12} {'Devices':<8} Details"
        print(header)
        print("-" * len(header))
        for r in results:
            print(f"{r['username'][:30]:<30} {r['email'][:40]:<40} "
                  f"{r['status']:<12} {r['device_count']:<8} {r['details']}")

    # Optional CSV output
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(results)
        print(f"\nCSV written to: {args.csv}")


if __name__ == "__main__":
    main()