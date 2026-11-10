"""Harmless production read probes; prints success metadata, never email/event contents."""
import asyncio
import importlib.util
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"plugins/bailey_productivity"))

spec=importlib.util.spec_from_file_location('bailey_account_probe',Path(__file__).resolve().parents[1]/'plugins/bailey_productivity/accounts.py')
accounts=importlib.util.module_from_spec(spec)
spec.loader.exec_module(accounts)

def flags(value):
    if isinstance(value,dict):
        for key, child in value.items():
            if key in {'successful','success'} and isinstance(child,bool): yield child
            if key=='error' and child: yield False
            yield from flags(child)
    elif isinstance(value,list):
        for child in value: yield from flags(child)

async def main():
    for action in ('search_email','calendar'):
        result=await accounts.execute(accounts.build_request({'action':action,'limit':1}))
        checks=list(flags(result))
        if not checks or not all(checks):
            raise RuntimeError('Read probe failed; inspect provider status privately')
        print(json.dumps({'action':action,'read_success':True,'contents_logged':False}))

asyncio.run(main())
