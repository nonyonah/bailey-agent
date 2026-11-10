import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"plugins/bailey_productivity"))
import unittest
import importlib.util
spec = importlib.util.spec_from_file_location("bailey_accounts_test", Path(__file__).resolve().parents[1]/"plugins/bailey_productivity/accounts.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
build_request = module.build_request

class AccountPolicy(unittest.TestCase):
    def test_no_write_or_generic_operation(self):
        for args in ({'action':'send_email'},{'action':'calendar','tool_slug':'GMAIL_SEND_EMAIL'},
                     {'action':'search_email','account':'another account'}):
            with self.assertRaises(ValueError): build_request(args)
    def test_search_is_pinned_read_and_bounded(self):
        result = build_request({'action':'search_email','query':'is:unread','page_token':'opaque'})
        item=result['tools'][0]
        self.assertEqual(item['tool_slug'],'GMAIL_FETCH_EMAILS')
        self.assertEqual(item['account'],'Bailey Gmail')
        self.assertEqual(item['arguments']['user_id'],'me')
        self.assertFalse(result['sync_response_to_workbench'])
        with self.assertRaises(ValueError): build_request({'action':'search_email','limit':500})
    def test_calendar_timezone_range_and_pagination(self):
        args={'action':'calendar','start':'2026-11-10T00:00:00+01:00',
              'end':'2026-11-11T00:00:00+01:00','page_token':'next-page'}
        fields=build_request(args)['tools'][0]['arguments']
        self.assertEqual(fields['calendarId'],'primary')
        self.assertEqual(fields['pageToken'],'next-page')
        self.assertTrue(fields['singleEvents'])
        args['start']='2026-11-10T00:00:00'
        with self.assertRaises(ValueError): build_request(args)
    def test_message_identifier_required(self):
        with self.assertRaises(ValueError): build_request({'action':'read_email','message_id':'invented subject'})
        self.assertEqual(build_request({'action':'read_email','message_id':'19b11732c1b578fd'})['tools'][0]['arguments']['format'],'full')
