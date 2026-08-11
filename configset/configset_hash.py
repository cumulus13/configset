#!/usr/bin/env python3

# File: getconfig_hash.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2026-08-11
# Description: 
# License: MIT

import os

class Hash:

    @classmethod
    def _compute_file_hash(cls, file_path, algorithm="sha256"):
        import hashlib
        file_path = str(file_path)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found: {file_path}")

        with open(file_path, "rb") as f:
            if hasattr(hashlib, "file_digest"):
                return hashlib.file_digest(f, algorithm).hexdigest().lower()
            else:
                hasher = hashlib.new(algorithm)
                for chunk in iter(lambda: f.read(65536), b""):
                    hasher.update(chunk)
                return hasher.hexdigest().lower()

    @classmethod
    def _resolve_hash_path(cls, file_path, hash_file_path, algorithm):
        file_path = str(file_path)
        if hash_file_path is None:
            return f"{file_path}.{algorithm}"
        return str(hash_file_path)

    @classmethod
    def get_hash(cls, file_path, hash_file_path=None, algorithm="sha256"):
        """GET: Reads stored hash.

        If hash file missing/empty, generates hash, saves file, and returns hash.
        """
        target_hash_path = cls._resolve_hash_path(file_path, hash_file_path, algorithm)

        if os.path.exists(target_hash_path):
            with open(target_hash_path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                if first_line:
                    return first_line.split()[0].lower()

        # File missing or empty: generate hash, write file, and return hash
        actual_hash = cls._compute_file_hash(file_path, algorithm)
        os.makedirs(os.path.dirname(target_hash_path) or ".", exist_ok=True)
        filename = os.path.basename(file_path)
        with open(target_hash_path, "w", encoding="utf-8") as f:
            f.write(f"{actual_hash}  {filename}\n")

        return actual_hash

    @classmethod
    def verify_hash(cls, file_path, update=False, hash_file_path=None, algorithm="sha256"):
        """VERIFY: strictly checks file hash against hash file.

        Does NOT create or write any files.
        """
        target_hash_path = cls._resolve_hash_path(file_path, hash_file_path, algorithm)

        if not os.path.exists(target_hash_path):
            if update: cls.update_hash(file_path, hash_file_path, algorithm, True)
            return False

        with open(target_hash_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            if not first_line:
                if update: cls.update_hash(file_path, hash_file_path, algorithm, True)
                return False
            expected_hash = first_line.split()[0].lower()

        actual_hash = cls._compute_file_hash(file_path, algorithm)
        if update: cls.update_hash(file_path, hash_file_path, algorithm, True)
        return actual_hash == expected_hash

    @classmethod
    def update_hash(cls, file_path, hash_file_path=None, algorithm="sha256", force=False):
        """UPDATE: checks existing hash first.

        If missing or mismatched (or force=True), overwrites/creates hash file.
        Returns True if already up-to-date, False if updated.
        """
        target_hash_path = cls._resolve_hash_path(file_path, hash_file_path, algorithm)

        # Check first unless forced
        if not force and cls.verify_hash(file_path, False, target_hash_path, algorithm):
            return True  # Already valid, no disk write performed

        # Perform update/creation
        actual_hash = cls._compute_file_hash(file_path, algorithm)
        os.makedirs(os.path.dirname(target_hash_path) or ".", exist_ok=True)
        filename = os.path.basename(file_path)
        with open(target_hash_path, "w", encoding="utf-8") as f:
            f.write(f"{actual_hash}  {filename}\n")

        return False  # Updated

