from models.config import ConfigProperty
import mailsnake
import mailsnake.exceptions
import logging
import datetime
import os

# This module uses Michael Helmick's version of mailsnake
# https://github.com/michaelhelmick/python-mailsnake

MAILCHIMP_API_KEY = ConfigProperty(
        'mailchimp_api_key', str,
        """The API Key for MailChimp, used for adding
        students to lists, etc.""",
        '')

MAILCHIMP_PRE_REG_LIST_ID = ConfigProperty(
        'mailchimp_pre_reg_list_id', str,
        """The List ID of the MailChimp list that
        contains everyone who has pre-registered.
        Set to None to disable this subscription.""",
        '')

MAILCHIMP_CONFIRMED_LIST_ID = ConfigProperty(
        'mailchimp_confirmed_list_id', str,
        """The List ID of the MailChimp list that
        contains everyone who has confirmed their registration.
        Set to None to disable this subscription.""",
        '')

MAILCHIMP_FOR_CREDIT_LIST_ID = ConfigProperty(
        'mailchimp_for_credit_list_id', str,
        """The List ID of the MailChimp list that
        contains everyone who has indicated they are
        registered for credit.
        Set to None to disable this subscription.""",
        '')

MAILCHIMP_UNENROLLED_LIST_ID = ConfigProperty(
        'mailchimp_unenrolled_list_id', str,
        """The List ID of the MailChimp list that
        contains people who were enrolled but have
        now unenrolled.
        Set to None to disable this subscription.""",
        '')

list_ids = {
        'pre-reg': MAILCHIMP_PRE_REG_LIST_ID,
        'confirmed': MAILCHIMP_CONFIRMED_LIST_ID,
        'for-credit': MAILCHIMP_FOR_CREDIT_LIST_ID,
        'unenrolled': MAILCHIMP_UNENROLLED_LIST_ID,
        }

def subscribe(list_name, email, name):
    try:
        list_id_prop = list_ids.get(list_name, None)
        list_id = None
        if list_id_prop:
            list_id = list_id_prop.value
        if not list_id:
            logging.debug(
                    'MailChimp: No %s list id configured, not subscribing.', list_name)
            return
        success = _do_subscribe(list_id, email, name)
        if not success:
            logging.warning(
                'Failed to subscribe %s to %s mailchimp list', email, list_name)
    except mailsnake.exceptions.MailSnakeException:
        logging.exception(
            'Failed to subscribe %s to %s mailchimp list, ', email, list_name)

# TODO: http://apidocs.mailchimp.com/api/1.3/listunsubscribe.func.php
def unsubscribe(list_name, email):
    try:
        list_id_prop = list_ids.get(list_name, None)
        list_id = None
        if list_id_prop:
            list_id = list_id_prop.value
        if not list_id:
            logging.debug(
                    'MailChimp: No %s list id configured, not unsubscribing.', list_name)
            return
        success = _do_unsubscribe(list_id, email)
        if not success:
            logging.warning(
                'Failed to unsubscribe %s from %s mailchimp list', email, list_name)
    except mailsnake.exceptions.MailSnakeException:
        logging.exception(
            'Failed to unsubscribe %s from %s mailchimp list, ', email, list_name)

def _do_unsubscribe(list_id, email):
    ip = os.environ["REMOTE_ADDR"]
    api_key = MAILCHIMP_API_KEY.value
    if not api_key:
        logging.debug(
                'No MailChimp api key configured, not subscribing.')
        return

    ms = mailsnake.MailSnake(api_key)
    success = ms.listUnsubscribe(
            id=list_id,
            email_address=email,
            send_goodbye=False,
            send_notify=False,
            )
    return success



def _do_subscribe(list_id, email, name):
    ip = os.environ["REMOTE_ADDR"]
    api_key = MAILCHIMP_API_KEY.value
    if not api_key:
        logging.debug(
                'No MailChimp api key configured, not subscribing.')
        return

    ms = mailsnake.MailSnake(api_key)
    success = ms.listSubscribe(
            id=list_id,
            email_address=email,
            double_optin=False,
            update_existing=True,
            merge_vars={
                'FNAME': name,
                'OPTIN_IP': ip,
                'OPTIN_TIME': datetime.datetime.now().isoformat(),
                },
            )
    return success

