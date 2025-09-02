import pytest

from genlab_bestilling.libs.bird_id import bird_id


def test_bird_id():
    """Test bird_id function with various inputs."""
    # Test with None and empty string
    assert bird_id(None) is None
    assert bird_id("") is None

    # Test basic format
    assert bird_id("G24ABC00123") == "ABC123"

    # Test with leading zeros removal
    assert bird_id("G24DEF00001") == "DEF1"

    # Test with replica suffix
    assert bird_id("G24XYZ00456-12") == "XYZ456-12"

    # Test different species code lengths
    assert bird_id("G24A00789") == "A789"
    assert bird_id("G24AB00321") == "AB321"
    assert bird_id("G24ABC00654") == "ABC654"

    # Test different year prefix
    assert bird_id("G23MNO00999") == "MNO999"

    # Test zero running number
    assert bird_id("G24PQR00000") == "PQR0"

    # Test large running number
    assert bird_id("G24STU12345") == "STU12345"

    # Test replica with leading zeros removed
    assert bird_id("G24VWX00042-3") == "VWX42-3"

    # Test multi-digit replica suffix
    assert bird_id("G24YZA00111-123") == "YZA111-123"

    # Test edge case formats
    assert bird_id("G99Z00001") == "Z1"
    assert bird_id("G00AAA99999") == "AAA99999"
    assert bird_id("G50BB00050-1") == "BB50-1"
    assert bird_id("G24C00100-999") == "C100-999"

    # Test invalid formats raise AttributeError
    invalid_genlab_ids = [
        "invalid",
        "ABC123",
        "G24",
        "24ABC123",
        "G2XABC123",  # Wrong year format
    ]

    for invalid_id in invalid_genlab_ids:
        with pytest.raises(AttributeError):
            bird_id(invalid_id)
