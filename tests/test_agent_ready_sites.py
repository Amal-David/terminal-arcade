import unittest

from scripts.validate_agent_ready_sites import validate_all


class AgentReadySiteBundleTests(unittest.TestCase):
    def test_bundles_are_self_contained_and_honest(self):
        validate_all()


if __name__ == "__main__":
    unittest.main()
