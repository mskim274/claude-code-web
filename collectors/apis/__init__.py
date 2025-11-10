# API Clients Package
from typing import Optional

# Lazy imports to avoid circular dependencies
_kis_client = None
_dart_client = None


def get_kis_client():
    """Get KIS API client (singleton)"""
    global _kis_client
    if _kis_client is None:
        from .kis import KISAPIClient
        _kis_client = KISAPIClient()
    return _kis_client


def get_dart_client():
    """Get DART API client (singleton)"""
    global _dart_client
    if _dart_client is None:
        from .dart import DARTAPIClient
        _dart_client = DARTAPIClient()
    return _dart_client


__all__ = ['get_kis_client', 'get_dart_client']
