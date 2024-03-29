import pytest

from api.exceptions import AlreadyExistsException, DoesNotExistException
from api.models.mall import Mall


class TestCreate:
    def test_is_id_returned(self, mall_service, mall_data):
        mall = mall_service.create(mall_data)

        assert hasattr(mall, 'id')

    def test_create(self, mall_service, mall_data, session):
        mall = mall_service.create(mall_data)

        with session.begin() as session:
            storage_mall = session.query(
                Mall
            ).get(mall.id)

        assert storage_mall is not None
        assert storage_mall.name == mall_data['name']

    def test_for_duplicated_name(self, mall_service, mall_data):
        mall_service.create(mall_data)

        with pytest.raises(AlreadyExistsException) as exception_info:
            mall_service.create(mall_data)

        assert exception_info.value.message == 'Mall already exists!'


class TestUpdate:
    def test_for_one_field(self, mall_service, session, mall_data):
        mall = mall_service.create(mall_data)

        update_data = {
            'name': 'updated_name'
        }

        mall_service.update(mall.id, update_data)

        with session.begin() as session:
            storage_mall = session.query(
                Mall
            ).get(mall.id)

        assert storage_mall.name == update_data['name']

    def test_for_duplicated_name(self, mall_service, mall_data):
        mall_service.create(mall_data)

        second_mall_data = mall_data.copy()
        second_mall_data.update({'name': 'second_mall_name'})

        second_mall = mall_service.create(second_mall_data)

        update_data = {
            'name': mall_data['name']
        }

        with pytest.raises(AlreadyExistsException) as exception_info:
            mall_service.update(second_mall.id, update_data)

        assert exception_info.value.message == 'Mall already exists!'


class TestDelete:
    def test_delete(self, mall_service, session, mall_data):
        mall = mall_service.create(mall_data)

        is_deleted = mall_service.delete(mall.id)

        assert is_deleted

        with session.begin() as session:
            assert session.query(
                Mall
            ).get(mall.id) is None

    def test_for_nonexistent_mall(self, mall_service):
        is_deleted = mall_service.delete(1000)

        assert not is_deleted


class TestGet:
    def test_get(self, mall_service, session, mall_data):
        mall = mall_service.create(mall_data)

        retrieved_mall = mall_service.get(mall.id)

        with session.begin() as session:
            storage_mall = session.query(
                Mall
            ).get(mall.id)

        assert storage_mall.name == retrieved_mall.name

    def test_for_nonexistent_mall(self, mall_service):
        with pytest.raises(DoesNotExistException) as exception_info:
            mall_service.get(1000)

        assert exception_info.value.message == 'Mall does not exist!'


class TestGetList:
    @pytest.mark.parametrize(
        'count_to_create,page,per_page',
        (
                (10, 1, 5),
                (10, 2, 5),
                (10, 3, 3)
        )
    )
    def test_get_list(self, mall_service, mall_data, count_to_create, page, per_page):
        created_malls = []

        for i in range(count_to_create):
            mall_data = mall_data.copy()
            mall_data.update({'name': f'{mall_data["name"]}{i}'})

            created_malls.append(
                mall_service.create(mall_data)
            )

        retrieved_malls = mall_service.get_list(page, per_page)

        assert count_to_create == retrieved_malls['total']

        created_malls_skip = (page - 1) * per_page
        for i, retrieved_mall in enumerate(retrieved_malls['malls']):
            assert retrieved_mall.id == created_malls[i + created_malls_skip].id
            assert retrieved_mall.name == created_malls[i + created_malls_skip].name


class TestBulkCreate:
    def test_bulk_create(self, mall_service, session, account):
        data = {'malls': [{
            'name': 'first_mall',
            'account_id': account.id
        }, {
            'name': 'second_mall',
            'account_id': account.id
        }]}

        mall_service.bulk_create(data)

        with session.begin() as session:
            assert session.query(
                Mall
            ).filter(
                Mall.name.in_(
                    [mall['name'] for mall in data['malls']]
                )
            ).count() == len(data['malls'])

    def test_bulk_create_with_duplicated_data(self, mall_service, account):
        data = {'malls': [{
            'name': 'first_mall',
            'account_id': account.id
        }, {
            'name': 'second_mall',
            'account_id': account.id
        }]}

        mall_service.bulk_create(data)

        with pytest.raises(AlreadyExistsException) as exception_info:
            mall_service.bulk_create(data)

        assert exception_info.value.message == 'One or more malls already exist!'
