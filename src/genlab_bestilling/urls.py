from .views import ProjectsView

appname = "genlab_bestilling"
urlpatterns = [*ProjectsView.get_urls()]
