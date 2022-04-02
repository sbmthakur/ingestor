import pytest
import json
from server import create_app
from unittest.mock import patch, Mock

#@patch('server.Swagger', return_value=True)
#@patch('server.swag_from')
@pytest.fixture
def test_server():
    #with patch.multiple('server', Swagger=Mock(return_value=True), swag_from=Mock(return_value=True)):
    test_app = create_app({ 'TESTING': True })

    with test_app.test_client() as testing_client:
        with test_app.app_context():
            yield testing_client

r_mock = Mock(return_value=["KTLX", "KAMA"])
@patch.multiple('nexradaws.NexradAwsInterface', get_avail_radars=r_mock)
def test_radar(test_server):

    data = {
        'date': '2022-01-01'
    }
    rv = test_server.post('/radars', data=json.dumps(data), content_type='application/json')

    assert {"radars": ["KTLX", "KAMA" ] } == rv.json
    assert r_mock.called == True

save_mock = Mock(return_value="file")
send_mock = Mock(return_value="send")

@patch.multiple('server', save_file=save_mock, send_file=send_mock)
def test_plot(test_server):

    data = {
        'date': '2022-01-01',
        'radar': 'KTLX'
    }
    rv = test_server.post('/plot', data=json.dumps(data), content_type='application/json')

    assert b"send" == rv.data
    assert save_mock.called == True
    assert send_mock.called == True

