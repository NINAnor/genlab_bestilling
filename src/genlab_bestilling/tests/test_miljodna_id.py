from genlab_bestilling.libs.miljodna_id import miljodna_id


def test_miljodna_id():
    """Test miljodna_id function with various inputs."""
    # Test with missing required inputs
    assert miljodna_id(None, 2026, "G26ABC01413", "ABC") is None
    assert miljodna_id("", 2026, "G26ABC01413", "ABC") is None
    assert miljodna_id("Melfjord", None, "G26ABC01413", "ABC") is None
    assert miljodna_id("Melfjord", 2026, None, "ABC") is None
    assert miljodna_id("Melfjord", 2026, "", "ABC") is None
    assert miljodna_id("Melfjord", 2026, "G26ABC01413", None) is None
    assert miljodna_id("Melfjord", 2026, "G26ABC01413", "") is None

    # Test basic format from the brief's example (uppercase pop_id as stored)
    assert miljodna_id("MELFJ", 2026, "G26ABC01413", "ABC") == "MELFJ_26_01413"

    # Test pop_id is taken as stored (no case conversion)
    assert miljodna_id("Melfjord", 2026, "G26ABC01413", "ABC") == "Melfj_26_01413"
    assert miljodna_id("melfjord", 2026, "G26ABC01413", "ABC") == "melfj_26_01413"

    # Test pop_id shorter than 5 characters is used as-is (no padding)
    assert miljodna_id("Ab", 2026, "G26ABC01413", "ABC") == "Ab_26_01413"

    # Test replicate suffix is preserved verbatim
    assert miljodna_id("MELFJ", 2026, "G26ABC01413-2", "ABC") == "MELFJ_26_01413-2"

    # Test variable-length species.code (not a fixed-offset slice)
    assert miljodna_id("MELFJ", 2026, "G26A01413", "A") == "MELFJ_26_01413"
    assert miljodna_id("MELFJ", 2026, "G26AB01413", "AB") == "MELFJ_26_01413"
    assert miljodna_id("MELFJ", 2026, "G26ABCD01413", "ABCD") == "MELFJ_26_01413"

    # Test year segment uses last two digits
    assert miljodna_id("MELFJ", 1999, "G99ABC01413", "ABC") == "MELFJ_99_01413"

    # Test genlab_id_segment is kept unmodified (leading zeros preserved)
    assert miljodna_id("MELFJ", 2026, "G26ABC00001", "ABC") == "MELFJ_26_00001"
