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

def subscribe_to_pre_reg(email, name):
    try:
        list_id = MAILCHIMP_PRE_REG_LIST_ID.value
        if not list_id:
            logging.debug(
                    'MailChimp: No pre-reg list id configured, not subscribing.')
            return
        success = _do_subscribe(list_id, email, name)
        if not success:
            logging.warning(
                'Failed to subscribe %s to pre-registration mailchimp list', email)
    except mailsnake.exceptions.MailSnakeException:
        logging.exception(
            'Failed to subscribe %s to pre-registration mailchimp list, ', email)

def subscribe_to_confirmed(email, name):
    try:
        list_id = MAILCHIMP_CONFIRMED_LIST_ID.value
        if not list_id:
            logging.debug(
                    'MailChimp: No confirmed-reg list id configured, not subscribing.')
            return
        success = _do_subscribe(list_id, email, name)
        if not success:
            logging.warning(
                'Failed to subscribe %s to confirmed-reg mailchimp list', email)
    except mailsnake.exceptions.MailSnakeException:
        logging.exception(
            'Failed to subscribe %s to confirmed-reg mailchimp list, ', email)


# TODO: http://apidocs.mailchimp.com/api/1.3/listunsubscribe.func.php
def unsubscribe_all(email):
    pass



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

