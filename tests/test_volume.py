# (c) Copyright 2020 Hewlett Packard Enterprise Development LP

# @author alokranjan

import pytest
import tests.nimbleclientbase as nimosclientbase
from tests.nimbleclientbase import SKIPTEST, log_to_file as log
from nimbleclient.v1 import exceptions
import time

'''VolumeTestCase tests the volume object functionality '''

# global variables
vol_name1 = nimosclientbase.get_unique_string("volumetc-vol1")
vol_name2 = nimosclientbase.get_unique_string("volumetc-vol2")
vol_name3 = nimosclientbase.get_unique_string("volumetc-vol3")
vol_to_delete = []
delete_volume_counter = 5  # we will try to deletevolume at max 5 times


@pytest.fixture(scope='module')
def before_running_all_testcase(request):
    log("**** Starting Tests for Volume TestCase *****")
    cleanup_old_volumes()

    def after_running_all_testcase():
        log("**** Completed Tests for Volume TestCase *****")
    request.addfinalizer(after_running_all_testcase)


def cleanup_old_volumes():

    # due to bulk_move operation most of the times when abort is issued.
    # the array ignores the request to delete the volume as the operation
    # is already in progress and hence the volumes are left over.hence,
    # every time this test is run ,we will try to remove the old entries
    log("Cleaning up unwanted volumes if any")
    global delete_volume_counter
    vol_resp = nimosclientbase.get_nimos_client().volumes.list()
    for vol_obj in vol_resp:
        while delete_volume_counter != 0:
            try:
                if (str.startswith(vol_obj.attrs.get("name"), "volumetc-vol")
                    or str.startswith(vol_obj.attrs.get("name"),
                                      "clone-volumetc")):

                    vol_name = vol_obj.attrs.get("name")
                    nimosclientbase.get_nimos_client(
                        ).volumes.offline(vol_obj.attrs.get("id"))
                    nimosclientbase.get_nimos_client(
                        ).volumes.delete(vol_obj.attrs.get("id"))
                    log(f"Deleted volume '{vol_name}'")
                    time.sleep(2)
                break  # break from inner while loop
            except exceptions.NimOSAPIError as ex:
                if ("SM_volmv_vol_einprog" in str(ex)
                        or "SM_vol_connection_count_unavailable" in str(ex)):
                    log("'SM_volmv_vol_einprog' in progress.Trying to delete "
                        f"volume '{vol_name}' again after 3 minutes")
                    time.sleep(180)
                    delete_volume_counter = delete_volume_counter - 1
                else:
                    break  # from while loop
            except Exception as ex:
                log(ex)


@pytest.fixture(scope='function')
def setup_teardown_for_each_test(before_running_all_testcase, request):
    global vol_name1, vol_name2, vol_name3
    # setup operations before yield is called
    nimosclientbase.log_header(request.function.__name__)
    yield setup_teardown_for_each_test
    # teardown operations below
    delete_volume()
    # create a new volume names for the next testcase
    vol_name1 = nimosclientbase.get_unique_string("volumetc-vol1")
    vol_name2 = nimosclientbase.get_unique_string("volumetc-vol2")
    vol_name3 = nimosclientbase.get_unique_string("volumetc-vol3")
    nimosclientbase.log_footer(request.function.__name__)


def create_volume(vol_name, size=50, read_only="false"):
    resp = nimosclientbase.get_nimos_client().volumes.create(
        vol_name, size=size, read_only=read_only)
    vol_id = resp.attrs.get("id")
    vol_to_delete.append(vol_id)
    assert resp is not None
    log(f"Created volume with name '{vol_name}' and Id '{vol_id}'")
    return resp


def delete_volume():
    for vol_id in vol_to_delete:
        try:
            # check
            nimosclientbase.get_nimos_client().volumes.offline(vol_id)
            nimosclientbase.get_nimos_client().volumes.delete(vol_id)
            log(f" Deleted volume with id '{vol_id}'")
        except Exception as ex:
            log(ex)
            # raise ex
    vol_to_delete.clear()


@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_create_volume(setup_teardown_for_each_test):
    create_volume(vol_name1)
    # check
    vol1 = nimosclientbase.get_nimos_client().volumes.get(id=None,
                                                          name=vol_name1)
    assert vol1 is not None
    assert vol_name1 == vol1.attrs.get("name")


@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_create_volume_already_exists(setup_teardown_for_each_test):
    create_volume(vol_name1)
    try:
        # now try creating the same volume again
        create_volume(vol_name1)
    except exceptions.NimOSAPIError as ex:
        # covered SM_eexist and SM_http_conflict
        if 'SM_eexist' in str(ex):
            log(f"Failed As Expected")
    except Exception as exgeneral:
        log(exgeneral)


@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_create_volume_bad_params(setup_teardown_for_each_test):
    # , or / is not supported by nimble for creating vol name
    vol_name = vol_name1 + "/,"
    try:
        create_volume(vol_name)
    except exceptions.NimOSAPIError as ex:
        # protocol ex is SM_http_bad_request
        if 'SM_invalid_arg_value' in str(ex):
            log(f"Failed As Expected. Invalid vol_name to create: {vol_name}")


@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_create_volume_unexpected_arg(setup_teardown_for_each_test):
    try:
        # "invalidarg" is not a part of volume argument.
        nimosclientbase.get_nimos_client().volumes.create(
            vol_name1, size=50, invalidarg="testinvalidarg")
    except exceptions.NimOSAPIError as ex:
        # protocol ex is SM_http_bad_request
        if 'SM_unexpected_arg' in str(ex):
            log("Failed As Expected. "
                f"Unexpected arg for vol_name : {vol_name1}")


@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_volume_page_size(setup_teardown_for_each_test):
    resp_vol = []
    # first atleast create few volume
    for i in range(0, 5):
        vol_name = nimosclientbase.get_unique_string("volumetc-vol1-" + str(i))
        resp = create_volume(vol_name)
        resp_vol.append(resp)
    resp = nimosclientbase.get_nimos_client().volumes.list(
        detail=True, pageSize=2)
    assert resp is not None
    assert resp.__len__() == 2


@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_invalid_volume_page_size(setup_teardown_for_each_test):
    # first atleast create few volume
    for i in range(0, 6):
        vol_name = nimosclientbase.get_unique_string("volumetc-vol1-" + str(i))
        create_volume(vol_name)
    try:
        nimosclientbase.get_nimos_client().volumes.list(
                detail=True, pageSize=5000)
    except Exception as ex:
        if"SM_too_large_page_size" in str(ex):
            log("Failed as expected. Invaild pagesize given")
        else:
            log(ex)


@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_create_volume_readonly(setup_teardown_for_each_test):
    # create a read only volume..the volume gets created as write only.
    # which makes sense. why would someone create a volume as read only.. but
    # doc says we can..file a bug.
    create_volume(vol_name1, 50, "true")
    # check
    vol1 = nimosclientbase.get_nimos_client().volumes.get(id=None,
                                                          name=vol_name1)
    assert vol1 is not None
    assert vol1.attrs.get("read_only") is False


@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_volume_with_few_fields(setup_teardown_for_each_test):
    create_volume(vol_name1)
    resp = nimosclientbase.get_nimos_client().volumes.get()
    assert resp is not None
    log(resp)


@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_selected_fields_for_all_volumes(setup_teardown_for_each_test):
    # first atleast create few volume
    vol1 = create_volume(vol_name1)
    create_volume(vol_name2)
    resp = nimosclientbase.get_nimos_client().volumes.list(
        detail=True, fields="name,id,size")
    for obj in resp:
        # first match the volume name. there could be that there were
        # volumes on the array than the ones we created also, we will
        # just check the attrs of one volume. if that works fine it will
        # work for other
        if(vol1.attrs.get("name") == obj.attrs.get("name")):
            assert obj.attrs.get("id") == vol1.attrs.get("id")
            assert obj.attrs.get("size") == vol1.attrs.get("size")
            # now check no other extra attributes were returned from server
            # for this volume
            # try fetching some attribute
            assert obj.attrs.get("read_only") is None


# below function will be implemented when sdk is ready for accepting filters
@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_select_fields_for_filtered_volumes(setup_teardown_for_each_test):

    # first atleast create few volume
    resp = create_volume(vol_name1)
    # get by name
    vol1 = nimosclientbase.get_nimos_client().volumes.get(
        id=None, name=vol_name1, fields="name,id,size")
    assert vol1 is not None
    assert resp.attrs.get("id") == vol1.attrs.get("id")
    assert resp.attrs.get("size") == vol1.attrs.get("size")
    assert resp.attrs.get("name") == vol1.attrs.get("name")
    # now check no other extra attributes were returned from server
    # for this volume
    assert vol1.attrs.get("full_name") is None


@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_non_existent_volumes(setup_teardown_for_each_test):

    resp = nimosclientbase.get_nimos_client().volumes.get(
        name="nonexistentvolume")
    assert resp is None


@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_sortby_asc_volume_name(setup_teardown_for_each_test):

    vol_name1 = nimosclientbase.get_unique_string("volumetc-vol-vol1-z")
    vol_name2 = nimosclientbase.get_unique_string("volumetc-vol-vol1-a")
    create_volume(vol_name1)
    create_volume(vol_name2)
    resp = nimosclientbase.get_nimos_client().volumes.list(
        detail=False, sortBy="name")  # ascending
    # asert that the resp contains only 2 objects. if more than 2 objects
    # that means the array has volumes which are not created by test.
    # in that case just fail
    if resp.__len__() != 2:
        log("Array has volumes which were not created by unit testcase."
            " make sure array has no volume present before running the test")
    else:
        # after sorting, vol_name2 should be the first object and 2nd object
        # should be vol_name1.
        assert vol_name2 == resp[0].attrs.get("name")
        assert vol_name1 == resp[1].attrs.get("name")


# the belwo test actually also covers the message
# "SM_start_row_beyond_total_rows" and "SM_start_row_beyond_end_rows"
@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_volume_startrow_beyond_endrow_volume(setup_teardown_for_each_test):
    create_volume(vol_name1)
    create_volume(vol_name2)
    # try to read from startrow 7. total only 2 rows will be there and
    # hence the resp should be none
    try:
        resp = nimosclientbase.get_nimos_client().volumes.get(startRow=50)
        assert resp is not None
    except exceptions.NimOSAPIError as ex:
        if "SM_start_row_beyond_total_rows" in str(ex):
            pass
        else:
            log(ex)


@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_volume_startrow_equals_endrow_volume(setup_teardown_for_each_test):

    create_volume(vol_name1)
    create_volume(vol_name2)
    try:
        resp = nimosclientbase.get_nimos_client().volumes.get(
            startRow=1, endRow=1)
        assert resp is None
    except exceptions.NimOSAPIError as ex:
        log(ex)

@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_update_volume_size_attribute(setup_teardown_for_each_test):
    # first atleast create few volume
    resp = create_volume(vol_name1)
    # update the size to 100
    resp = nimosclientbase.get_nimos_client().volumes.update(
        id=resp.attrs.get("id"), size=100)
    assert resp is not None
    # check the size is updated correctly
    vol = nimosclientbase.get_nimos_client().volumes.get(
        id=resp.attrs.get("id"), fields="name,id,size")
    assert resp.attrs.get("size") == vol.attrs.get("size")


@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_update_volume_metadata_with_invalid_keypair(
        setup_teardown_for_each_test):
    # first atleast create few volume
    resp_vol1 = create_volume(vol_name1)
    create_volume(vol_name2)
    metadata = {
        "key1": "abcde",
        "key2": "xyz"
    }
    try:
        # update the size to 100
        nimosclientbase.get_nimos_client().volumes.update(
            id=resp_vol1.attrs.get("id"), metadata=metadata)
    except exceptions.NimOSAPIError as ex:
        # covered SM_eexist and SM_http_conflict
        if 'SM_invalid_keyvalue' in str(ex):
            log("Failed as expected")


# as of now the below will always fail as no way to provide correct metadata
@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_update_volume_metadata(setup_teardown_for_each_test):
    # first atleast create few volume
    resp_vol1 = create_volume(vol_name1)
    create_volume(vol_name2)
    metadata = {
        'key1': 'abcde'
    }
    try:
        # update the size to 100
        nimosclientbase.get_nimos_client().volumes.update(
            id=resp_vol1.attrs.get("id"), metadata=metadata)
    except exceptions.NimOSAPIError as ex:
        if 'SM_invalid_keyvalue' in str(ex):
            log("Failed as expected")


@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_update_resize_volume_force(setup_teardown_for_each_test):
    # shrinking an online volume is an operation which will fail
    # unless force=true is specified.this tests the
    # forceupdateobject functionality.

    # first atleast create few volume
    resp = create_volume(vol_name1)
    assert resp is not None
    assert resp.attrs.get("size") == 50
    # assert that the volume is online
    assert resp.attrs.get("online") is True
    try:
        # update the size to 100
        resp = nimosclientbase.get_nimos_client().volumes.update(
            id=resp.attrs.get("id"), size=5)
    except exceptions.NimOSAPIError as ex:
        if 'SM_vol_size_decreased' in str(ex):
            assert "the operation will decrease the size of the volume. "
            "use force option to proceed." in str(ex)
    # try with force option
    resp = nimosclientbase.get_nimos_client().volumes.update(
        id=resp.attrs.get("id"), size=5, force=True)
    assert resp.attrs.get("size") == 5


@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_create_clone_volume(setup_teardown_for_each_test):
    # first atleast create few volume
    clone_vol_name = "test.volumeclone.clone"
    resp_vol = create_volume(vol_name1)
    snap_resp = nimosclientbase.get_nimos_client().snapshots.create(
        name="test.volumeclone.snapshot", vol_id=resp_vol.attrs.get("id"))
    clonevol_resp = nimosclientbase.get_nimos_client().volumes.create(
        name=clone_vol_name,
        base_snap_id=snap_resp.attrs.get("id"),
        clone=True)
    # confirm
    assert clone_vol_name == clonevol_resp.attrs.get("name")
    assert clonevol_resp.attrs.get("size") == resp_vol.attrs.get("size")
    # cleanup
    nimosclientbase.get_nimos_client().volumes.offline(
        clonevol_resp.attrs.get("id"))
    nimosclientbase.get_nimos_client().volumes.delete(
        clonevol_resp.attrs.get("id"))


@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_delete_clone_volume(setup_teardown_for_each_test):

    # first create volume
    clone_vol_name = nimosclientbase.get_unique_string("clone-volumetc")
    resp_vol = create_volume(vol_name1)
    vol_id = resp_vol.attrs.get("id")
    # clone a volume
    snap_resp = nimosclientbase.get_nimos_client().snapshots.create(
        name="test.volumeclone.snapshot", vol_id=vol_id)
    clonevol_resp = nimosclientbase.get_nimos_client().volumes.create(
        name=clone_vol_name,
        base_snap_id=snap_resp.attrs.get("id"),
        clone=True)
    # confirm
    assert clone_vol_name == clonevol_resp.attrs.get("name")
    assert clonevol_resp.attrs.get("size") == resp_vol.attrs.get("size")
    # try deleting parent volume . it should fail with
    # exception "SM_vol_has_clone"
    try:
        nimosclientbase.get_nimos_client().volumes.offline(vol_id)
        nimosclientbase.get_nimos_client().volumes.delete(vol_id)
    except exceptions.NimOSAPIError as ex:
        if "SM_vol_has_clone" in str(ex):
            log("Failed as expected. volume has clone")
            # cleanup
            nimosclientbase.get_nimos_client().volumes.offline(
                clonevol_resp.attrs.get("id"))
            nimosclientbase.get_nimos_client().volumes.delete(
                clonevol_resp.attrs.get("id"))
        else:
            log(ex)


@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_bulk_move_volume(setup_teardown_for_each_test):
    try:
        orig_vol_pool_name = ""
        # first atleast create few volume
        resp = create_volume(vol_name3, size=5)
        orig_vol_pool_name = resp.attrs.get("pool_name")
        # get the dest pool id.
        ppol_resp = nimosclientbase.get_nimos_client().pools.list()
        assert ppol_resp is not None
        # make sure we have 2 pools atleaset
        assert ppol_resp.__len__() >= 2
        # get the pool id where to move the volume
        for poolobj in ppol_resp:
            if poolobj.attrs.get("name") == orig_vol_pool_name:
                continue
            else:
                break
        pool_id = poolobj.attrs.get("id")
        # move the volumes
        moveresp = nimosclientbase.get_nimos_client().volumes.bulk_move(
            dest_pool_id=pool_id, vol_ids=vol_to_delete)
        assert moveresp is not None
        # abort the move now
        for vol_id in vol_to_delete:
            abortresp = nimosclientbase.get_nimos_client().volumes.abort_move(
                vol_id)
            assert abortresp is not None
    except exceptions.NimOSAPIError as ex:
        if ("SM_vol_connection_count_unavailable" in str(ex)
                or "SM_vol_usage_unavailable" in str(ex)):
            log("Failed to abort volume move due to service inavailiability")
        elif "SM_invalid_arg_value" in str(ex):
            log("Failed as expected. Invalid pool id provided")
        else:
            log(ex)


@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_move_volume(setup_teardown_for_each_test):

    try:

        # first atleast create volume
        create_volume(vol_name3, size=5)
        # deliberately pass wrong pool id. move operation takes lot of time
        # hence we will just call the sdk api to make sure it takes all
        # the arguments
        moveresp = nimosclientbase.get_nimos_client().volumes.move(
            dest_pool_id="kasdkashdqwkdhkas28623612000ef", id=vol_to_delete[0])
        assert moveresp is not None
        # abort the move now
        for vol_id in vol_to_delete:
            abortresp = nimosclientbase.get_nimos_client().volumes.abort_move(
                    vol_id)
            assert abortresp is not None
    except exceptions.NimOSAPIError as ex:
        if ("SM_vol_connection_count_unavailable" in str(ex)
                or "SM_vol_usage_unavailable" in str(ex)):
            log("Failed to abort volume move due to service inavailiability")
        elif "SM_invalid_arg_value" in str(ex):
            log("Failed as expected. Invalid pool id provided")
        else:
            log(ex)


@pytest.mark.skipif(SKIPTEST is True,
                    reason="skipped this test as SKIPTEST variable is true")
def test_bulk_set_dedupe(setup_teardown_for_each_test):
    try:
        # first atleast create volume
        create_volume(vol_name3, size=5)
        dedupresp = nimosclientbase.get_nimos_client().volumes.bulk_set_dedupe(
            dedupe_enabled=True, vol_ids=vol_to_delete)
        assert dedupresp is not None
    except exceptions.NimOSAPIError as ex:
        if "SM_pool_dedupe_incapable" in str(ex):
            log("Failed as expected. pool is not"
                "capable of hosting dedup volumes")
        else:
            log(ex)
