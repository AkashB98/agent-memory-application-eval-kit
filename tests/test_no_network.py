"""No-network enforcement: with sockets blocked, generating, building
stores, retrieving, deciding and evaluating must all still work."""

import os
import socket
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class _Blocker:
    def __init__(self, *a, **k):
        raise RuntimeError("network access blocked in hermetic test")


class TestNoNetwork(unittest.TestCase):
    def setUp(self):
        self._real_socket = socket.socket
        socket.socket = _Blocker
        import urllib.request as urlreq
        self._real_urlopen = urlreq.urlopen
        urlreq.urlopen = lambda *a, **k: (_ for _ in ()).throw(
            RuntimeError("network access blocked in hermetic test"))

    def tearDown(self):
        socket.socket = self._real_socket
        import urllib.request as urlreq
        urlreq.urlopen = self._real_urlopen

    def test_full_pipeline_offline(self):
        from corpus import generate_sessions
        from evaluator import evaluate
        from probes import generate_probes
        report = evaluate(generate_sessions(), generate_probes())
        self.assertEqual(report["probe_count"], 22)
        self.assertEqual(len(report["designs"]), 3)

    def test_no_module_opens_sockets_at_import(self):
        for mod in ("corpus", "probes", "retrieval", "memory_designs",
                    "agent", "evaluator", "cli", "demo"):
            sys.modules.pop(mod, None)
        import agent, cli, corpus, demo, evaluator  # noqa: F401
        import memory_designs, probes, retrieval  # noqa: F401
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
