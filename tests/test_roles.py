from tests.conftest import login


def test_registration_is_disabled(client):
    response = client.get("/register")
    assert response.status_code in (404, 405, 302)


def test_unauthenticated_test_recipe_endpoint_removed(client):
    response = client.get("/api/test/recipes/1")
    assert response.status_code == 404


def test_viewer_cannot_open_log_feeding(client, viewer_user):
    login(client, viewer_user)
    response = client.get("/log_feeding")
    assert response.status_code in (403, 302)


def test_researcher_can_open_log_feeding(client, researcher_user):
    login(client, researcher_user)
    response = client.get("/log_feeding")
    assert response.status_code == 200


def test_viewer_cannot_create_ape(client, viewer_user):
    login(client, viewer_user)
    response = client.get("/create_ape")
    assert response.status_code in (403, 302)


def test_admin_can_open_create_ape(client, admin_user):
    login(client, admin_user)
    response = client.get("/create_ape")
    assert response.status_code == 200


def test_viewer_cannot_export_reports(client, viewer_user):
    login(client, viewer_user)
    response = client.get("/reports/download/csv")
    assert response.status_code in (403, 302)
