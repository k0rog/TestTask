import pytest
from http import HTTPStatus

from api.models.unit import Unit


class TestCreate:
    URL = '/api/units/'

    def test_is_id_returned(self, client, permanent_unit_data):
        response = client.post(self.URL, json=permanent_unit_data)

        assert response.status_code == HTTPStatus.CREATED
        assert 'id' in response.json

    def test_create(self, client, permanent_session, permanent_unit_data):
        response = client.post(self.URL, json=permanent_unit_data)
        assert response.status_code == HTTPStatus.CREATED

        with permanent_session.begin() as session:
            storage_unit = session.query(
                Unit
            ).get(response.json['id'])

        assert storage_unit is not None
        assert storage_unit.name == permanent_unit_data['name']

    def test_for_duplicated_name(self, client, permanent_unit_data):
        client.post(self.URL, json=permanent_unit_data)
        response = client.post(self.URL, json=permanent_unit_data)

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert 'error' in response.json
        assert response.json['error'] == 'Unit already exists!'

    @pytest.mark.parametrize(
        'field,value',
        (
                ('name', 123),
        ))
    def test_with_invalid_data(self, client, field, value, permanent_unit_data):
        permanent_unit_data[field] = value

        response = client.post(self.URL, json=permanent_unit_data)

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert 'errors' in response.json
        assert response.json['errors']['json'][field] == ['Not a valid string.']


class TestUpdate:
    URL = '/api/units/'

    def test_update(self, client, permanent_session, permanent_unit_data):
        unit_id = client.post(self.URL, json=permanent_unit_data).json['id']

        update_data = {
            'name': 'updated_name',
        }

        response = client.patch(
            self.URL + str(unit_id),
            json=update_data
        )

        with permanent_session.begin() as session:
            storage_unit = session.query(
                Unit
            ).get(unit_id)

        assert response.status_code == HTTPStatus.NO_CONTENT
        assert storage_unit.name == update_data['name']

    def test_for_duplicated_name(self, client, permanent_unit_data):
        client.post(self.URL, json=permanent_unit_data)

        second_unit_data = permanent_unit_data.copy()
        second_unit_data.update({
            'name': 'second_unit_name'
        })
        response = client.post(self.URL, json=second_unit_data)

        update_response = client.patch(
            self.URL + str(response.json['id']),
            json={'name': permanent_unit_data['name']}
        )

        assert update_response.status_code == HTTPStatus.BAD_REQUEST
        assert 'error' in update_response.json
        assert update_response.json['error'] == 'Unit already exists!'

    @pytest.mark.parametrize(
        'field,value',
        (
                ('name', 123),
        ))
    def test_with_invalid_data(self, client, permanent_unit_data, field, value):
        unit_id = client.post(self.URL, json=permanent_unit_data).json['id']

        update_data = {field: value}

        response = client.patch(self.URL + str(unit_id), json=update_data)

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert 'errors' in response.json
        assert response.json['errors']['json'][field] == ['Not a valid string.']


class TestDelete:
    URL = '/api/units/'

    def test_delete(self, client, permanent_session, permanent_unit_data):
        unit_id = client.post(self.URL, json=permanent_unit_data).json['id']

        response = client.delete(self.URL + str(unit_id))

        assert response.status_code == HTTPStatus.NO_CONTENT

        with permanent_session.begin() as session:
            assert session.query(
                Unit.id
            ).filter_by(id=unit_id).first() is None

    def test_delete_nonexistent_customer(self, client):
        response = client.delete(self.URL + str(10000))

        assert response.status_code == HTTPStatus.NO_CONTENT


class TestGet:
    URL = '/api/units/'

    def test_get(self, client, permanent_unit_data):
        unit_id = client.post(self.URL, json=permanent_unit_data).json['id']

        retrieved_unit = client.get(
            self.URL + str(unit_id)
        )

        assert retrieved_unit.status_code == HTTPStatus.OK
        assert retrieved_unit.json['name'] == permanent_unit_data['name']
        assert retrieved_unit.json['id'] == unit_id

    def test_for_nonexistent_unit(self, client):
        response = client.get(
            self.URL + str(1000)
        )

        assert response.status_code == 404
        assert 'error' in response.json
        assert response.json['error'] == 'Unit does not exist!'


class TestGetList:
    URL = '/api/units/'

    def test_with_wrong_page(self, client):
        response = client.get(
            '{}?page={}&per_page={}'.format(self.URL, -1, 10)
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert 'errors' in response.json
        assert response.json['errors']['querystring']['page'] == \
               ['Wrong page value! Try value > 1.']

    @pytest.mark.parametrize('per_page', (100, -1))
    def test_with_wrong_per_page(self, client, per_page):
        response = client.get(
            '{}?page={}&per_page={}'.format(self.URL, 1, per_page)
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert 'errors' in response.json
        assert response.json['errors']['querystring']['per_page'] == \
               ['Must be greater than or equal to 1 and less than or equal to 50.']


class TestBulkCreate:
    URL = '/api/units/bulk'

    def test_bulk_create(self, client, permanent_session, permanent_mall):
        data = {'units': [{
            'name': 'first_unit',
            'mall_id': permanent_mall.id
        }, {
            'name': 'second_unit',
            'mall_id': permanent_mall.id
        }]}

        response = client.post(self.URL, json=data)

        assert response.status_code == HTTPStatus.CREATED

        with permanent_session.begin() as session:
            assert session.query(
                Unit
            ).filter(
                Unit.name.in_(
                    [unit['name'] for unit in data['units']]
                )
            ).count() == len(data['units'])

    def test_bulk_create_with_duplicated_data(self, client, permanent_mall):
        data = {'units': [{
            'name': 'first_unit',
            'mall_id': permanent_mall.id
        }, {
            'name': 'second_unit',
            'mall_id': permanent_mall.id
        }]}

        client.post(self.URL, json=data)

        response = client.post(self.URL, json=data)

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert 'error' in response.json
        assert response.json['error'] == 'One or more units already exist!'
