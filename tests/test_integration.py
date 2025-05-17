import os
import pytest
from werkzeug.datastructures import FileStorage
from app.models import Artefact
from app import db
import io


@pytest.mark.integration
def test_artefact_upload_and_fetch(client, app_fixture):
    """Test the full flow: upload a file, fetch it and then verify content"""

    upload_data = {
        'file': FileStorage(
            stream=io.BytesIO(b'integration test content'),
            filename='integration_test_file.txt',
            content_type='text/plain'
        )
    }
    upload_response = client.post('/artefacts/test_directory', data=upload_data, content_type='multipart/form-data')

    assert upload_response.status_code == 201
    assert upload_response.json['message'] == "File uploaded successfully"
    artefact_id = upload_response.json['id']

    fetch_response = client.get(f'/artefact/test_directory/{artefact_id}')
    assert fetch_response.status_code == 200
    assert fetch_response.data == b'integration test content'


@pytest.mark.integration
def test_artefact_upload_and_delete(client, app_fixture):
    """Test uploading and then deleting an artefact"""

    upload_data = {
        'file': FileStorage(
            stream=io.BytesIO(b'test delete content'),
            filename='artefact_to_delete.txt',
            content_type='text/plain'
        )
    }
    upload_response = client.post('/artefacts/test_directory', data=upload_data, content_type='multipart/form-data')

    assert upload_response.status_code == 201
    assert upload_response.json['message'] == "File uploaded successfully"
    artefact_id = upload_response.json['id']

    artefact_path = os.path.join(app_fixture.config['BASE_UPLOAD_DIR'], 'test_directory', 'artefact_to_delete.txt')
    assert os.path.exists(artefact_path)

    delete_response = client.delete(f'/artefact/test_directory/{artefact_id}')
    assert delete_response.status_code == 202
    assert delete_response.json['message'] == "File deleted successfully"
    assert not os.path.exists(artefact_path)

    with app_fixture.app_context():
        artefact = db.session.get(Artefact, artefact_id)
        assert artefact is None


@pytest.mark.integration
def test_list_artefacts_after_upload(client, app_fixture):
    """Test listing artefacts after uploading multiple files"""

    file_names = ['file1.txt', 'file2.txt']
    for file_name in file_names:
        upload_data = {
            'file': FileStorage(
                stream=io.BytesIO(b'test list content'),
                filename=file_name,
                content_type='text/plain'
            )
        }
        response = client.post('/artefacts/test_directory', data=upload_data, content_type='multipart/form-data')
        assert response.status_code == 201
        assert response.json['message'] == "File uploaded successfully"

    list_response = client.get('/artefacts/test_directory')
    assert list_response.status_code == 200
    uploaded_names = [os.path.basename(artefact) for artefact in list_response.json]
    for file_name in file_names:
        assert file_name in uploaded_names

    directories_response = client.get('/artefacts/')
    assert directories_response.status_code == 200
    assert 'test_directory' in directories_response.json


@pytest.mark.integration
def test_replace_artefact(client, app_fixture):
    """Test replacing an existing artefact"""

    upload_data = {
        'file': FileStorage(
            stream=io.BytesIO(b'original content'),
            filename='replace_test.txt',
            content_type='text/plain'
        )
    }
    upload_response = client.post('/artefacts/test_directory', data=upload_data, content_type='multipart/form-data')
    assert upload_response.status_code == 201
    artefact_id = upload_response.json['id']

    replace_data = {
        'file': FileStorage(
            stream=io.BytesIO(b'replaced content'),
            filename='replace_test.txt',
            content_type='text/plain'
        )
    }
    replace_response = client.put(f'/artefact/test_directory/{artefact_id}', data=replace_data, content_type='multipart/form-data')
    assert replace_response.status_code == 200
    assert replace_response.json['message'] == "Artefact replaced successfully"

    fetch_response = client.get(f'/artefact/test_directory/{artefact_id}')
    assert fetch_response.status_code == 200
    assert fetch_response.data == b'replaced content'
