import os

from flask import Blueprint, request, jsonify, send_from_directory, current_app
from datetime import datetime
from werkzeug.utils import secure_filename
from pathlib import Path

from app.extensions import db
from app.models import Artefact

main = Blueprint('main', __name__)


def is_safe_path(basedir: Path, path: Path) -> bool:
    """Check if the path is within the basedir."""

    basedir = basedir.resolve()
    path = path.resolve()
    return basedir in path.parents or basedir == path


@main.route('/artefacts/', methods=['GET'])
def list_all_directories():
    """List all directories."""

    base_upload_dir = Path(current_app.config['BASE_UPLOAD_DIR']).resolve()
    directories = []
    for root, dirs, _ in os.walk(base_upload_dir):
        root_path = Path(root).resolve()
        for dir_name in dirs:
            dir_path = (root_path / dir_name).relative_to(base_upload_dir)
            directories.append(str(dir_path))

    directories = list(set(directories))
    return jsonify(directories), 200


@main.route('/artefacts/<path:directory>', methods=['GET'])
def list_artefacts_in_directory(directory):
    """List all artefacts in a specific directory."""

    base_upload_dir = Path(current_app.config['BASE_UPLOAD_DIR']).resolve()
    safe_directory = (base_upload_dir / directory).resolve()

    if not safe_directory.is_dir():
        return jsonify(error="Directory not found"), 404

    artefacts = [
        str(file.relative_to(base_upload_dir))
        for file in safe_directory.iterdir()
        if file.is_file()
    ]

    return jsonify(artefacts), 200


"""
COMENTARIU PENTRU PROFESOR:

in exercitiu ruta era /artefacts/<path:directory>/<artefact_id> 
dar id-ul il genereaza baza de date, nu clientul, asa ca am schimbat in /artefacts/<path:directory>
"""
@main.route('/artefacts/<path:directory>', methods=['POST'])
def upload_artefact(directory):
    """Upload an artefact file."""

    if 'file' not in request.files:
        return jsonify(error="No file part in request"), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify(error="No file selected"), 400

    base_upload_dir = Path(current_app.config['BASE_UPLOAD_DIR']).resolve()
    safe_directory = (base_upload_dir / directory).resolve()

    if not is_safe_path(base_upload_dir, safe_directory):
        return jsonify(error="Invalid directory path"), 400

    safe_directory.mkdir(parents=True, exist_ok=True)

    filename = secure_filename(file.filename)
    file_path = safe_directory / filename
    file.save(file_path)

    new_artefact = Artefact(
        name=filename,
        path=str(file_path.relative_to(base_upload_dir)),
        uploaded_at=datetime.utcnow(),
    )
    db.session.add(new_artefact)
    db.session.commit()

    return jsonify(message="File uploaded successfully", id=new_artefact.id), 201


@main.route('/artefact/<path:directory>/<int:artefact_id>', methods=['GET'])
def fetch_artefact(directory, artefact_id):
    """Fetch an existing artefact."""

    artefact = Artefact.query.get(artefact_id)
    if not artefact or not artefact.path.startswith(directory):
        return jsonify(error="Artefact not found in the specified directory"), 404

    base_upload_dir = Path(current_app.config['BASE_UPLOAD_DIR']).resolve()
    file_path = (base_upload_dir / artefact.path).resolve()

    directory_path = (base_upload_dir / directory).resolve()
    if not is_safe_path(base_upload_dir, file_path) or file_path.parent != directory_path:
        return jsonify(error="Artefact does not belong to the specified directory"), 400

    return send_from_directory(file_path.parent, file_path.name)


@main.route('/artefact/<path:directory>/<int:artefact_id>', methods=['DELETE'])
def delete_artefact(directory, artefact_id):
    """Delete an artefact."""

    artefact = Artefact.query.get(artefact_id)
    if not artefact or not artefact.path.startswith(directory):
        return jsonify(error="Artefact not found in the specified directory"), 404

    base_upload_dir = Path(current_app.config['BASE_UPLOAD_DIR']).resolve()
    file_path = (base_upload_dir / artefact.path).resolve()

    if file_path.exists():
        file_path.unlink()

    db.session.delete(artefact)
    db.session.commit()
    return jsonify(message="File deleted successfully"), 202


@main.route('/artefact/<path:directory>', methods=['DELETE'])
def delete_directory(directory):
    """Delete a directory and all its contents."""
    base_upload_dir = Path(current_app.config['BASE_UPLOAD_DIR']).resolve()
    safe_directory = (base_upload_dir / directory).resolve()

    if not is_safe_path(base_upload_dir, safe_directory):
        return jsonify(error="Invalid directory path"), 400

    if not safe_directory.is_dir():
        return jsonify(error="Directory not found"), 404

    artifacts_to_delete = []
    for root, dirs, files in os.walk(safe_directory, topdown=False):
        root_path = Path(root).resolve()
        for file in files:
            file_path = root_path / file
            artifacts_to_delete.append(str(file_path.relative_to(base_upload_dir).as_posix()))
            file_path.unlink()
        for dir_name in dirs:
            (root_path / dir_name).rmdir()

    db_artifacts = Artefact.query.filter(Artefact.path.in_(artifacts_to_delete)).all()
    for artifact in db_artifacts:
        db.session.delete(artifact)
    db.session.commit()

    safe_directory.rmdir()

    return jsonify(message="Directory deleted successfully"), 202


@main.route('/artefact/<path:directory>/<int:artefact_id>', methods=['PUT'])
def replace_artefact(directory, artefact_id):
    """Replace an existing artefact."""

    artefact = Artefact.query.get(artefact_id)
    if not artefact or not artefact.path.startswith(directory):
        return jsonify(error="Artefact not found in the specified directory"), 404

    if 'file' not in request.files:
        return jsonify(error="No file part in request"), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify(error="No file selected"), 400

    base_upload_dir = Path(current_app.config['BASE_UPLOAD_DIR']).resolve()
    safe_directory = (base_upload_dir / directory).resolve()

    if not is_safe_path(base_upload_dir, safe_directory):
        return jsonify(error="Invalid directory path"), 400

    filename = secure_filename(file.filename)
    file_path = safe_directory / filename

    old_file_path = (base_upload_dir / artefact.path).resolve()
    if old_file_path.exists():
        old_file_path.unlink()

    file.save(file_path)

    artefact.name = filename
    artefact.path = str(file_path.relative_to(base_upload_dir))
    artefact.uploaded_at = datetime.utcnow()
    db.session.commit()

    return jsonify(message="Artefact replaced successfully"), 200
