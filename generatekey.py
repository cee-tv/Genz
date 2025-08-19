#!/usr/bin/env python3
import json
import secrets
import argparse
from datetime import datetime, timedelta
import hashlib
import base64


class KeyGenerator:
    def __init__(self):
        self.keys_db = "keys.json"
        
    def generate_key(self, duration, unit):
        """Generate a new authentication key with specified validity period"""
        # Generate a cryptographically secure random key
        key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Calculate days based on unit
        unit_multiplier = {
            'days': 1,
            'weeks': 7,
            'months': 30,
            'years': 365
        }
        
        days = duration * unit_multiplier[unit]
        
        # Calculate expiration date
        expiration = datetime.now() + timedelta(days=days)
            
        key_data = {
            "key": key,
            "created": datetime.now().isoformat(),
            "expires": expiration.isoformat(),
            "duration": duration,
            "unit": unit,
            "valid_days": days,
            "hash": hashlib.sha256(key.encode()).hexdigest()
        }
        
        # Store the key
        self._store_key(key_data)
        
        return key_data
    
    def _store_key(self, key_data):
        """Store the key in a JSON database"""
        try:
            with open(self.keys_db, 'r') as f:
                keys = json.load(f)
        except FileNotFoundError:
            keys = []
            
        keys.append(key_data)
        
        with open(self.keys_db, 'w') as f:
            json.dump(keys, f, indent=2)
    
    def validate_key(self, key):
        """Validate an authentication key"""
        try:
            with open(self.keys_db, 'r') as f:
                keys = json.load(f)
                
            key_hash = hashlib.sha256(key.encode()).hexdigest()
            
            for key_data in keys:
                if key_data['hash'] == key_hash:
                    if datetime.fromisoformat(key_data['expires']) > datetime.now():
                        return True, key_data
                    else:
                        return False, "Key expired"
            return False, "Invalid key"
        except FileNotFoundError:
            return False, "No keys found"


def main():
    parser = argparse.ArgumentParser(description='Generate authentication keys')
    parser.add_argument('--duration', type=int, default=1, help='Duration amount')
    parser.add_argument('--unit', choices=['days', 'weeks', 'months', 'years'], default='years', help='Duration unit')
    
    args = parser.parse_args()
    
    generator = KeyGenerator()
    key_data = generator.generate_key(args.duration, args.unit)
    
    print("Generated Key:")
    print(key_data['key'])
    print(f"Expires: {key_data['expires']} ({args.duration} {args.unit})")


if __name__ == "__main__":
    main()
