import unittest

from x_ca_watcher.analyzer import find_addresses


class AnalyzerTest(unittest.TestCase):
    def test_finds_evm_address(self):
        hits = find_addresses("CA: 0x742d35Cc6634C0532925a3b844Bc454e4438f44e")
        self.assertEqual(hits[0].chain_hint, "evm")
        self.assertEqual(hits[0].confidence, "high")

    def test_finds_move_asset(self):
        hits = find_addresses("token 0x2::sui::SUI")
        self.assertEqual(hits[0].chain_hint, "move_asset")

    def test_finds_base58_candidate(self):
        hits = find_addresses("mint EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
        self.assertEqual(hits[0].chain_hint, "solana_or_base58")

    def test_ignores_plain_long_words(self):
        hits = find_addresses("ThisIsProbablyJustALongCamelCaseIdentifier")
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()

