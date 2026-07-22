from src.arenapulse.decorators import guard
from src.arenapulse.engine import ArenaEngine

class MockEngine(ArenaEngine):
    def __init__(self):
        super().__init__(name="dummy")
        self.verify_called = False
    
    def verify_and_execute(self, action_type, payload):
        self.verify_called = True
        self.last_payload = payload

def test_guard_intercepts_call():
    engine = MockEngine()
    
    @guard(engine, action_type="test_action", payload_extractor=lambda x: {"val": x})
    def dummy_function(x):
        return x * 2

    res = dummy_function(5)
    
    assert res == 10
    assert engine.verify_called is True
    assert engine.last_payload == {"val": 5}
