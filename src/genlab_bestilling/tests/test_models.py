from genlab_bestilling.models import AnalysisOrder, Marker


def test_analysis_populate_without_order(genlab_setup):
    ao = AnalysisOrder.objects.create(genrequest_id=1, customize_markers=False)
    ao.populate_from_order()
    assert not ao.sample_markers.exists()


def test_analysis_populate_with_order_no_markers(extraction):
    ao = AnalysisOrder.objects.create(
        genrequest_id=1, customize_markers=False, from_order=extraction
    )
    ao.populate_from_order()
    assert not ao.sample_markers.exists()


def test_analysis_populate_with_order_one_marker_one_species(extraction):
    ao = AnalysisOrder.objects.create(
        genrequest_id=1, customize_markers=False, from_order=extraction
    )
    m = Marker.objects.filter(name="Elvemusling A").first()
    ao.markers.add(m)
    ao.populate_from_order()
    assert ao.sample_markers.count() == 2


def test_analysis_populate_with_order_wrong_marker(extraction):
    ao = AnalysisOrder.objects.create(
        genrequest_id=1, customize_markers=False, from_order=extraction
    )
    m = Marker.objects.filter(name="Kjønnstest").first()
    ao.markers.add(m)
    ao.populate_from_order()
    assert not ao.sample_markers.exists()


def test_analysis_populate_with_order_multiple_marker_same_species(extraction):
    ao = AnalysisOrder.objects.create(
        genrequest_id=1, customize_markers=False, from_order=extraction
    )
    m = Marker.objects.filter(name__startswith="Salamander").all()
    ao.markers.add(*m)
    ao.populate_from_order()
    assert ao.sample_markers.count() == 6


def test_analysis_populate_with_order_all_markers(extraction):
    ao = AnalysisOrder.objects.create(
        genrequest_id=1, customize_markers=False, from_order=extraction
    )
    m = ao.genrequest.markers.all()
    ao.markers.add(*m)
    ao.populate_from_order()
    assert ao.sample_markers.count() == 6
