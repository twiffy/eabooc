from models.config import ConfigProperty
import mailsnake
import mailsnake.exceptions
import logging

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

def subscribe_to_pre_reg(email, name):
    try:
        api_key = MAILCHIMP_API_KEY.value
        list_id = MAILCHIMP_PRE_REG_LIST_ID.value
        if not api_key:
            logging.debug(
                    'No MailChimp api key configured, not subscribing.')
            return
        if not list_id:
            logging.debug(
                    'MailChimp: No pre-reg list id configured, not subscribing.')
            return

        ms = mailsnake.MailSnake(api_key)
        success = ms.listSubscribe(
                id=list_id,
                email_address=email,
                double_optin=False,
                update_existing=True,
                merge_vars={
                    'FNAME': name,
                    },
                )
        if not success:
            logging.warning(
                'Failed to subscribe %s to mailchimp list', email)
    except mailsnake.exceptions.MailSnakeException:
        logging.exception(
            'Failed to subscribe %s to mailchimp list, ', email)



