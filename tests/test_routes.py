import os
from pathlib import Path

import pytest
from app import db
from app.models import Artefact
from werkzeug.datastructures import FileStorage
import io


@pytest.mark.unit
def test_upload_artefact(client, app_fixture):
    """Test uploading an artefact file"""

    data = {
        'file': FileStorage(
            stream=io.BytesIO(b'test content'),
            filename='test_file.txt',
            content_type='text/plain'
        )
    }
    response = client.post('/artefacts/unit_test_directory', data=data, content_type='multipart/form-data')

    assert response.status_code == 201
    assert response.json['message'] == "File uploaded successfully"
    assert 'id' in response.json

    file_path = os.path.join(app_fixture.config['BASE_UPLOAD_DIR'], 'unit_test_directory', 'test_file.txt')
    assert os.path.exists(file_path)


@pytest.mark.unit
def test_list_artefacts(client, app_fixture):
    """Test listing all artefacts in a specific directory"""

    with app_fixture.app_context():
        artefact1 = Artefact(name='list_file1.txt', path='list_test_directory/list_file1.txt')
        artefact2 = Artefact(name='list_file2.txt', path='list_test_directory/list_file2.txt')
        db.session.add_all([artefact1, artefact2])
        db.session.commit()

    dir_path = os.path.join(app_fixture.config['BASE_UPLOAD_DIR'], 'list_test_directory')
    os.makedirs(dir_path, exist_ok=True)
    for file_name in ['list_file1.txt', 'list_file2.txt']:
        with open(os.path.join(dir_path, file_name), 'w') as f:
            f.write('list test content')

    response = client.get('/artefacts/list_test_directory')

    assert response.status_code == 200
    uploaded_files = [os.path.basename(artefact) for artefact in response.json]
    assert 'list_file1.txt' in uploaded_files
    assert 'list_file2.txt' in uploaded_files


@pytest.mark.unit
def test_fetch_artefact(client, app_fixture):
    """Test fetching an existing artefact"""

    with app_fixture.app_context():
        artefact = Artefact(name='fetch_test.txt', path='fetch_test_directory/fetch_test.txt')
        db.session.add(artefact)
        db.session.commit()
        artefact_id = artefact.id

    dir_path = os.path.join(app_fixture.config['BASE_UPLOAD_DIR'], 'fetch_test_directory')
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, 'fetch_test.txt')
    with open(file_path, 'w') as f:
        f.write('fetch test content')

    response = client.get(f'/artefact/fetch_test_directory/{artefact_id}')

    assert response.status_code == 200
    assert response.data == b'fetch test content'


@pytest.mark.unit
def test_delete_artefact(client, app_fixture):
    """Test deleting an artefact"""

    with app_fixture.app_context():
        artefact = Artefact(name='delete_test.txt', path='delete_test_directory/delete_test.txt')
        db.session.add(artefact)
        db.session.commit()
        artefact_id = artefact.id

    dir_path = os.path.join(app_fixture.config['BASE_UPLOAD_DIR'], 'delete_test_directory')
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, 'delete_test.txt')
    with open(file_path, 'w') as f:
        f.write('delete test content')

    assert os.path.exists(file_path)

    response = client.delete(f'/artefact/delete_test_directory/{artefact_id}')

    assert response.status_code == 202
    assert response.json['message'] == "File deleted successfully"
    assert not os.path.exists(file_path)

    with app_fixture.app_context():
        artefact = db.session.get(Artefact, artefact_id)
        assert artefact is None


@pytest.mark.unit
def test_list_all_directories(client, app_fixture):
    """Test listing all directories"""

    directories = ['dir1', 'dir2', os.path.join('dir3', 'subdir')]
    for dir_path in directories:
        full_path = os.path.join(app_fixture.config['BASE_UPLOAD_DIR'], dir_path)
        os.makedirs(full_path, exist_ok=True)

    response = client.get('/artefacts/')

    assert response.status_code == 200
    for dir_path in directories:
        normalized_dir_path = os.path.normpath(dir_path)
        normalized_response_paths = [os.path.normpath(path) for path in response.json]
        assert normalized_dir_path in normalized_response_paths


@pytest.mark.unit
def test_fetch_nonexistent_artefact(client, app_fixture):
    """Test fetching an artefact that does not exist"""

    response = client.get('/artefact/nonexistent_directory/999')
    assert response.status_code == 404
    assert response.json['error'] == "Artefact not found in the specified directory"


@pytest.mark.unit
def test_upload_without_file(client, app_fixture):
    """Test uploading without providing a file"""

    upload_response = client.post('/artefacts/no_file_directory', data={}, content_type='multipart/form-data')
    assert upload_response.status_code == 400
    assert upload_response.json['error'] == "No file part in request"


@pytest.mark.unit
def test_upload_with_empty_filename(client, app_fixture):
    """Test uploading with an empty filename"""

    upload_data = {
        'file': FileStorage(
            stream=io.BytesIO(b'empty filename content'),
            filename='',
            content_type='text/plain'
        )
    }
    upload_response = client.post('/artefacts/empty_filename_directory', data=upload_data, content_type='multipart/form-data')
    assert upload_response.status_code == 400
    assert upload_response.json['error'] == "No file selected"


@pytest.mark.unit
def test_replace_nonexistent_artefact(client, app_fixture):
    """Test replacing an artefact that does not exist"""

    replace_data = {
        'file': FileStorage(
            stream=io.BytesIO(b'new content'),
            filename='replace_nonexistent.txt',
            content_type='text/plain'
        )
    }
    replace_response = client.put('/artefact/nonexistent_directory/999', data=replace_data, content_type='multipart/form-data')
    assert replace_response.status_code == 404
    assert replace_response.json['error'] == "Artefact not found in the specified directory"


@pytest.mark.unit
def test_delete_nonexistent_artefact(client, app_fixture):
    """Test deleting an artefact that does not exist"""

    delete_response = client.delete('/artefact/nonexistent_directory/999')
    assert delete_response.status_code == 404
    assert delete_response.json['error'] == "Artefact not found in the specified directory"


@pytest.mark.unit
def test_upload_invalid_directory_path(client, app_fixture):
    """Test uploading to an invalid directory path"""

    upload_data = {
        'file': FileStorage(
            stream=io.BytesIO(b'path traversal content'),
            filename='traversal.txt',
            content_type='text/plain'
        )
    }

    upload_response = client.post('/artefacts/../invalid_directory', data=upload_data, content_type='multipart/form-data')
    assert upload_response.status_code == 400
    assert upload_response.json['error'] == "Invalid directory path"


@pytest.mark.unit
def test_fetch_artefact_wrong_directory(client, app_fixture):
    """Test fetching an artefact with incorrect directory"""

    with app_fixture.app_context():
        artefact = Artefact(name='wrong_dir_test.txt', path='correct_directory/wrong_dir_test.txt')
        db.session.add(artefact)
        db.session.commit()
        artefact_id = artefact.id

    correct_dir_path = os.path.join(app_fixture.config['BASE_UPLOAD_DIR'], 'correct_directory')
    os.makedirs(correct_dir_path, exist_ok=True)
    file_path = os.path.join(correct_dir_path, 'wrong_dir_test.txt')
    with open(file_path, 'w') as f:
        f.write('wrong directory content')

    fetch_response = client.get(f'/artefact/wrong_directory/{artefact_id}')
    assert fetch_response.status_code == 404
    assert fetch_response.json['error'] == "Artefact not found in the specified directory"


@pytest.mark.unit
def test_delete_directory(client, app_fixture):
    """Test deleting an entire directory and its contents"""

    with app_fixture.app_context():
        artefact1 = Artefact(name='delete_file1.txt', path='delete_test_directory/delete_file1.txt')
        artefact2 = Artefact(name='delete_file2.txt', path='delete_test_directory/delete_file2.txt')
        db.session.add_all([artefact1, artefact2])
        db.session.commit()
        artefact1_id = artefact1.id
        artefact2_id = artefact2.id

    base_upload_dir = Path(app_fixture.config['BASE_UPLOAD_DIR']).resolve()
    dir_path = base_upload_dir / 'delete_test_directory'
    dir_path.mkdir(parents=True, exist_ok=True)
    for file_name in ['delete_file1.txt', 'delete_file2.txt']:
        (dir_path / file_name).write_text('delete test content')

    assert (dir_path / 'delete_file1.txt').exists()
    assert (dir_path / 'delete_file2.txt').exists()

    response = client.delete('/artefact/delete_test_directory')
    assert response.status_code == 202
    assert response.json['message'] == "Directory deleted successfully"

    assert not (dir_path / 'delete_file1.txt').exists()
    assert not (dir_path / 'delete_file2.txt').exists()

    assert not dir_path.exists()

    with app_fixture.app_context():
        db.session.expire_all()
        deleted_artefact1 = db.session.get(Artefact, artefact1_id)
        deleted_artefact2 = db.session.get(Artefact, artefact2_id)
        assert deleted_artefact1 is None
        assert deleted_artefact2 is None


@pytest.mark.unit
def test_replace_existing_artefact(client, app_fixture):
    """Test replacing an existing artefact"""

    with app_fixture.app_context():
        artefact = Artefact(name='replace_existing.txt', path='replace_directory/replace_existing.txt')
        db.session.add(artefact)
        db.session.commit()
        artefact_id = artefact.id

    dir_path = os.path.join(app_fixture.config['BASE_UPLOAD_DIR'], 'replace_directory')
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, 'replace_existing.txt')
    with open(file_path, 'w') as f:
        f.write('original content')

    replace_data = {
        'file': FileStorage(
            stream=io.BytesIO(b'new replaced content'),
            filename='replace_existing.txt',
            content_type='text/plain'
        )
    }
    replace_response = client.put(
        f'/artefact/replace_directory/{artefact_id}',
        data=replace_data,
        content_type='multipart/form-data'
    )
    assert replace_response.status_code == 200
    assert replace_response.json['message'] == "Artefact replaced successfully"
    assert os.path.exists(file_path)

    with open(file_path, 'rb') as f:
        content = f.read()
    assert content == b'new replaced content'

    with app_fixture.app_context():
        updated_artefact = db.session.get(Artefact, artefact_id)
        assert updated_artefact is not None
        assert updated_artefact.name == 'replace_existing.txt'

        expected_path = os.path.join('replace_directory', 'replace_existing.txt')
        assert updated_artefact.path == expected_path

