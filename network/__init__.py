# -*- coding: utf-8 -*-
"""Ağ modülü - HTTP Polling (basit ve güvenilir)"""

# HTTP Polling istemcisi (yeni, basit sistem)
from network.client_http import HTTPNetworkClient

# Uyumluluk için eski isimlerle export
NetworkClient = HTTPNetworkClient

def get_network_client():
    """Ağ istemcisi oluştur"""
    return HTTPNetworkClient()

__all__ = ['NetworkClient', 'HTTPNetworkClient', 'get_network_client']

