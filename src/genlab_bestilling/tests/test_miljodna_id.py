from genlab_bestilling.libs.miljodna_id import miljodna_id


def test_miljodna_id():
    """Test miljodna_id function with various inputs."""
    # Test with missing required inputs
    assert miljodna_id(None, "G26ABC01413") is None
    assert miljodna_id("", "G26ABC01413") is None
    assert miljodna_id("MELFJ", None) is None
    assert miljodna_id("MELFJ", "") is None

    # Test basic format from the brief's example
    assert miljodna_id("MELFJ", "G26ABC01413") == "MELFJ_26_01413"

    # Test pop_id is taken as stored (no case conversion)
    assert miljodna_id("Melfjord", "G26ABC01413") == "Melfj_26_01413"
    assert miljodna_id("melfjord", "G26ABC01413") == "melfj_26_01413"

    # Test pop_id shorter than 5 characters is used as-is (no padding)
    assert miljodna_id("Ab", "G26ABC01413") == "Ab_26_01413"

    # Test replicate suffix is preserved verbatim
    assert miljodna_id("MELFJ", "G26ABC01413-2") == "MELFJ_26_01413-2"

    # Test variable-length species code (not a fixed-offset slice)
    assert miljodna_id("MELFJ", "G26A01413") == "MELFJ_26_01413"
    assert miljodna_id("MELFJ", "G26AB01413") == "MELFJ_26_01413"
    assert miljodna_id("MELFJ", "G26ABCD01413") == "MELFJ_26_01413"

    # Test year segment is parsed from genlab_id
    assert miljodna_id("MELFJ", "G99ABC01413") == "MELFJ_99_01413"

    # Test genlab_id_segment is kept unmodified (leading zeros preserved)
    assert miljodna_id("MELFJ", "G26ABC00001") == "MELFJ_26_00001"

    # Test invalid/unparseable genlab_id formats return None
    invalid_genlab_ids = [
        "invalid",
        "ABC123",
        "G26",
        "26ABC01413",  # pragma: allowlist secret
        "G2XABC01413",  # Wrong year format
    ]
    for invalid_id in invalid_genlab_ids:
        assert miljodna_id("MELFJ", invalid_id) is None
