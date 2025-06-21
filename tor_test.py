#!/usr/bin/env python3
"""
Simple Tor connectivity test script
"""
import socket
import requests
import time
import sys

def test_tor_connection():
    """Test if Tor is running and accessible"""
    
    print("🔍 Testing Tor connectivity...")
    
    # Test SOCKS proxy
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 9050))
        sock.close()
        
        if result == 0:
            print("✅ Tor SOCKS proxy is accessible on port 9050")
        else:
            print("❌ Cannot connect to Tor SOCKS proxy on port 9050")
            return False
    except Exception as e:
        print(f"❌ Error testing SOCKS proxy: {e}")
        return False
    
    # Test actual Tor connectivity
    try:
        proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }
        
        response = requests.get('https://check.torproject.org/api/ip', 
                              proxies=proxies, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('IsTor'):
                print(f"✅ Successfully connected through Tor! IP: {data.get('IP')}")
                return True
            else:
                print(f"❌ Connected but not through Tor. IP: {data.get('IP')}")
                return False
        else:
            print(f"❌ HTTP request failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Tor connectivity: {e}")
        return False

def wait_for_tor(max_attempts=30, delay=2):
    """Wait for Tor to become available"""
    
    print(f"⏳ Waiting for Tor to start (max {max_attempts * delay} seconds)...")
    
    for attempt in range(max_attempts):
        if test_tor_connection():
            return True
        
        if attempt < max_attempts - 1:
            print(f"   Attempt {attempt + 1}/{max_attempts} failed, waiting {delay}s...")
            time.sleep(delay)
    
    return False

if __name__ == "__main__":
    if wait_for_tor():
        print("🎉 Tor is ready!")
        sys.exit(0)
    else:
        print("💥 Tor failed to start properly")
        sys.exit(1)
