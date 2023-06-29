# -*- coding: utf-8 -*-
"""
Created on Sun Jun 25 18:59:33 2023

@author: haeso
"""


#%% import

import os
import sys
import requests
import time
import hmac
import hashlib
from urllib.parse import urlencode

from account import api_key, secret_key


import time
from typing import Dict
import dateparser


#%% def class

class Request:
    def __init__(self) -> None:
        self.parameters:dict = dict()

    def add_param(self, name, value) -> None:
        self.parameters[name] = value
    
    def add_parameters(self, param_dict: Dict) -> None:
        for name, value in param_dict.items():
            self.parameters[name] = value

    def get_params(self) -> dict:
        empty_params = [key for key, value in self.parameters.items() if value is None]
        for key in empty_params:
            del self.parameters[key]
        return self.parameters


class RequestBuilder:
    def __init__(self) -> None:
        self.request = Request()
    
    def with_symbol(self, symbol: str):
        self.request.add_param('symbol', symbol.upper())
        return self

    def with_start_time(self, time:str):
        self.request.add_param('startTime', self.__parse_time(time))
        return self

    def with_end_time(self, time:str):
        self.request.add_param('endTime', self.__parse_time(time))
        return self

    def with_limit(self, limit:int):
        self.request.add_param('limit', limit)
        return self
    
    def with_from_id(self, from_id:str):
        self.request.add_param('from_id', from_id)
        return self

    def with_interval(self, interval:str):
        self.request.add_param('interval', interval)
        return self

    def with_timestamp(self):
        timestamp = int(round(time.time() * 1000))
        self.request.add_param('timestamp', timestamp)
        return self

    def build(self):
        return self.request

    def __parse_time(self, time:str):
        if time is None or time == "":
            raise Exception("Invalid time format")
        return int(dateparser.parse(time).timestamp() * 1000)


class BaseClient:
    # uri: str = "https://fapi.binance.com/fapi/v1"
    uri: str = "https://testnet.binancefuture.com/fapi/v1"
    
    def __init__(
                self, 
                api_key: str, 
                secret_key: str = None, 
                ) -> None:
        self.headers = {'content-type': 'application/x-www-form-urlencoded'}
        if not api_key is None:
            self.headers['X-MBX-APIKEY'] = api_key
        self.secret_key = secret_key
            
    
    def _get(self, endpoint: str, parameters: dict = dict(), signed=False):
        if signed:
            parameters['signature'] = self.get_signature(parameters)

        query_string = urlencode(parameters)
        location = '{}/{}?{}'.format(BaseClient.uri, endpoint, query_string)
        
        response = requests.get(location, headers=self.headers)
        return response.status_code, response.json()
    
    
    def _post(self, endpoint: str, parameters: dict = dict(), signed=False):
        if signed:
            parameters['signature'] = self.get_signature(parameters)

        query_string = urlencode(parameters)
        location = '{}/{}'.format(BaseClient.uri, endpoint)
        
        response = requests.post(location, headers=self.headers, data=str.encode(query_string))
        return response.status_code, response.json()
    
    
    def _delete(self, endpoint: str, parameters: dict = dict(), signed=False):
        if signed:
            parameters['signature'] = self.get_signature(parameters)
        
        query_string = urlencode(parameters)
        location = '{}/{}'.format(BaseClient.uri, endpoint)
        
        response = requests.delete(location, headers=self.headers, data=str.encode(query_string))
        return response.status_code, response.json()
        
    
    def get_signature(self, parameters):
        request = str.encode(urlencode(parameters))
        if self.secret_key:
            return hmac.new(str.encode(self.secret_key), request, hashlib.sha256).hexdigest()
        else:
            raise Exception("Secret key required")
            
            
class AccountEndpoints(BaseClient):
    def get_account_information(self):
        return self._get('account', 
            RequestBuilder()
                .with_timestamp()
                .build()
                .get_params(),
            True)
    
    def get_balance_information(self):
        return self._get('balance', 
            RequestBuilder()
                .with_timestamp()
                .build()
                .get_params(),
            True)
    
    def get_position_risk(self):
        return self._get('positionRisk', 
            RequestBuilder()
                .with_timestamp()
                .build()
                .get_params(),
            True)

    def _create_order(self, symbol: str, side:str, order_type:str, **parameters):
        request = Request()
        request.add_param('symbol', symbol.upper())
        request.add_param('side', side.upper())
        request.add_param('type', order_type.upper())
        request.add_parameters(parameters)
        timestamp = int(round(time.time() * 1000))
        request.add_param('timestamp', timestamp)
        return request

    def test_order(self, symbol: str, side:str, order_type:str, **parameters):
        request = self._create_order(symbol, side, order_type, **parameters)
        return self._post('order/test', request.get_params(), True)

    def order(self, symbol: str, side:str, order_type:str, **parameters):
        request = self._create_order(symbol, side, order_type, **parameters)
        return self._post('order', request.get_params(), True)

    def get_open_orders(self, symbol: str=''):
        request = Request()
        timestamp = int(round(time.time() * 1000))
        request.add_param('timestamp', timestamp)
        if len(symbol) > 0:
            request.add_param('symbol', symbol)
        return self._get('openOrders', request.get_params(), True)
    
    def cancel_order(self, symbol: str, orig_client_order_id: str):
        request = Request()
        request.add_param('symbol', symbol)
        request.add_param('origClientOrderId', orig_client_order_id)
        timestamp = int(round(time.time() * 1000))
        request.add_param('timestamp', timestamp)
        return self._delete('order', request.get_params(), True)

    def cancel_all_open_orders(self, symbol: str):
        request = Request()
        request.add_param('symbol', symbol)
        timestamp = int(round(time.time() * 1000))
        request.add_param('timestamp', timestamp)
        return self._delete('allOpenOrders', request.get_params(), True)
    
    
#%% test

if __name__ == '__main__':
    ae = AccountEndpoints(api_key=api_key, secret_key=secret_key)
    code, res = ae.get_account_information()
    print(f'code : {code}   res : {res}')
    
        
    for pos in res['positions']:
        if pos.get('symbol') == 'ETHUSDT':
            print(pos)
            
            
    code, res = ae.get_balance_information()
    for r in res:
        if r.get('balance') is not None and float(r['balance']) > 0.0:
            print(r)
    
    
    
    
    
    


































