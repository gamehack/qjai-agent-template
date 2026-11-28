import unittest
from scripts.check_naming import registry_image, validate_project, test_container_name


class NamingTests(unittest.TestCase):
    def test_valid(self):
        for name in ("qjai-agent-template", "qjai-agent-producthunt", "qjai-gateway-modal",
                     "qjai-bridge-kilo", "qjai-service-worker-2"):
            self.assertEqual(validate_project(name), name)

    def test_invalid(self):
        for name in ("producthunt", "qjai-Agent-test", "qjai-agent-test_name",
                     "qjai-agent-", "qjai-agent--test", "qjai-other-test",
                     "qjai-agent-test\n", "qjai-agent-test/other"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_project(name)

    def test_agent_type(self):
        with self.assertRaises(ValueError):
            validate_project("qjai-gateway-modal", "agent")

    def test_registry(self):
        self.assertEqual(registry_image("GameHack/qjai-agent-producthunt", "agent"),
                         "ghcr.io/gamehack/qjai-agent-producthunt")
        for name in ("gamehack/qjai-agent-A", "gamehack/a/qjai-agent-test", "/qjai-agent-test"):
            with self.assertRaises(ValueError):
                registry_image(name, "agent")

    def test_container_name(self):
        self.assertEqual(test_container_name("qjai-agent-producthunt", "bench-abc123"),
                         "qjai-agent-producthunt-test-bench-abc123")
        with self.assertRaises(ValueError):
            test_container_name("qjai-agent-producthunt", "bad/id")
