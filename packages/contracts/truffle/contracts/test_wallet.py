import unittest
from unittest import TestCase, main
from rlp.utils import encode_hex, decode_hex
from ethereum.tools import tester as t
from ethereum.tools.tester import TransactionFailed
from ethereum.tools import keys
import time
from sha3 import keccak_256
from hashlib import sha256
from web3 import Web3

import os

# Command-line flag to skip tests we're not working on
WORKING_ONLY = os.environ.get('WORKING_ONLY', False)

DEPLOY_GAS = 4500000

class TestSplitter(TestCase):

    def setUp(self):

        self.c = t.Chain()

        self.splitter_code = open('SplitterWallet.sol').read()
        # Not sure what the right way is to get pyethereum to import the dependencies
        # Pretty sure it's not this, but it does the job:
        safemath_code_raw = open('RealitioSafeMath256.sol').read()
        owned_code_raw = open('Owned.sol').read()

        self.splitter_code = self.splitter_code.replace("import './Owned.sol';", owned_code_raw);
        self.splitter_code = self.splitter_code.replace("import './RealitioSafeMath256.sol';", safemath_code_raw);

        self.c.mine()
        self.wallet0= self.c.contract(self.splitter_code, language='solidity', sender=t.k0, startgas=DEPLOY_GAS)
        self.c.mine()

    @unittest.skipIf(WORKING_ONLY, "Not under construction")
    def test_split(self):

        self.assertEqual(self.wallet0.balanceOf(t.a1), 0)
        self.assertEqual(self.wallet0.balanceTotal(), 0)
        self.c.tx(t.k0, self.wallet0.address, 100000)
        self.assertEqual(self.c.head_state.get_balance(self.wallet0.address), 100000)
        self.assertEqual(self.wallet0.balanceOf(t.a1), 0)

        self.wallet0.addRecipient(t.a1)
        self.wallet0.allocate()
        self.assertEqual(self.wallet0.balanceOf(t.a1), 100000)
        self.assertEqual(self.c.head_state.get_balance(self.wallet0.address), 100000)

        self.wallet0.withdraw(sender=t.k1)
        self.assertEqual(self.wallet0.balanceOf(t.a1), 0)
        self.assertEqual(self.c.head_state.get_balance(self.wallet0.address), 0)

        with self.assertRaises(TransactionFailed):
            self.wallet0.withdraw(sender=t.k1)
        self.c.mine()

        self.wallet0.addRecipient(t.a2)

        self.assertEqual(self.wallet0.balanceTotal(), 0)
        self.c.tx(t.k0, self.wallet0.address, 100000)
        self.c.tx(t.k0, self.wallet0.address, 50000)
        self.assertEqual(self.c.head_state.get_balance(self.wallet0.address), 150000)
        self.wallet0.allocate()
        self.assertEqual(self.c.head_state.get_balance(self.wallet0.address), 150000)
        self.assertEqual(self.wallet0.balanceTotal(), 150000)

        self.assertEqual(self.wallet0.balanceOf(t.a1), 75000)
        self.assertEqual(self.wallet0.balanceOf(t.a2), 75000)

        self.wallet0.withdraw(sender=t.k1)
        self.assertEqual(self.c.head_state.get_balance(self.wallet0.address), 75000)
        self.assertEqual(self.wallet0.balanceOf(t.a1), 0)
        self.assertEqual(self.wallet0.balanceOf(t.a2), 75000)
        self.assertEqual(self.wallet0.balanceTotal(), 75000)
        self.wallet0.withdraw(sender=t.k2)
        self.assertEqual(self.wallet0.balanceOf(t.a2), 0)
        self.assertEqual(self.wallet0.balanceTotal(), 0)

        self.c.tx(t.k0, self.wallet0.address, 3)
        self.wallet0.allocate()
        self.assertEqual(self.wallet0.balanceTotal(), 2)
        self.assertEqual(self.wallet0.balanceOf(t.a1), 1)
        self.assertEqual(self.wallet0.balanceOf(t.a2), 1)
        self.wallet0.withdraw(sender=t.k1)
        self.wallet0.withdraw(sender=t.k2)
        self.assertEqual(self.wallet0.balanceTotal(), 0)
        self.assertEqual(self.c.head_state.get_balance(self.wallet0.address), 1)
        self.c.tx(t.k0, self.wallet0.address, 5)
        self.wallet0.allocate()
        self.assertEqual(self.wallet0.balanceTotal(), 6)
        self.assertEqual(self.wallet0.balanceOf(t.a1), 3)
        self.assertEqual(self.wallet0.balanceOf(t.a2), 3)
        self.wallet0.withdraw(sender=t.k1)
        self.wallet0.withdraw(sender=t.k2)
        self.assertEqual(self.wallet0.balanceTotal(), 0)
        self.assertEqual(self.c.head_state.get_balance(self.wallet0.address), 0)

if __name__ == '__main__':
    main()
