"""Tests for Voicehand."""
from src.core import Voicehand
def test_init(): assert Voicehand().get_stats()["ops"] == 0
def test_op(): c = Voicehand(); c.process(x=1); assert c.get_stats()["ops"] == 1
def test_multi(): c = Voicehand(); [c.process() for _ in range(5)]; assert c.get_stats()["ops"] == 5
def test_reset(): c = Voicehand(); c.process(); c.reset(); assert c.get_stats()["ops"] == 0
def test_service_name(): c = Voicehand(); r = c.process(); assert r["service"] == "voicehand"
