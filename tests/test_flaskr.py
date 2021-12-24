import os
import pytest
import tempfile

from flaskr import create_app

@pytest.fixture
def client():
    data_file_fd, data_file_name = tempfile.mkstemp()
    app = create_app({'TESTING': True})
    with app.test_client() as client:
        yield client
    os.close(data_file_fd)
    os.unlink(data_file_name)

def test0(client):
    result = client.get('/')
    assert b'Hello' in result.data

