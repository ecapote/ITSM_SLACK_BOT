#!/usr/bin/env python
# # -*- coding: utf-8 -*-
# # ITSM SLACK API Integration

import ConfigParser
import logging
from slackclient import SlackClient
import json
import time   ## used to sleep for x amnt of seconds before resuming(at end of while loop)...minimize load on slack api
import re ### regex library
import requests
from requests_oauthlib import OAuth2, OAuth2Session
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


## Define INI file
settings = ConfigParser.ConfigParser()
settings.read('./slack_bot_config.ini')


### SETUP THE FUNCTION FOR TO READ THE CONFIG FILE HEADERS
def ConfigSectionMap(section):
    dict1 = {}
    options = settings.options(section)
    for option in options:
        try:
            dict1[option] = settings.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1


def setup_custom_logger(name):
    LOG_FILENAME = './rd_itsm_slack_bot.log'
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.FileHandler(LOG_FILENAME, mode='a')
    handler.setFormatter(formatter)
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger

##POST Slack message wtih ITSM Info
def make_slack_api_call(slack_client, msg, thread, my_channel, payload_attachment):
    api_call = slack_client.api_call("chat.postMessage",
                                     channel=my_channel,
                                     text=msg,
                                     as_user=False,
                                     thread_ts=thread, icon_emoji=':rotating_light:', attachments=json.dumps(payload_attachment))
    return api_call


def get_today_itsm_incidents(ticket_no,username,password):
    try:
        print 'ticket_no', ticket_no
        url = 'https://[SERVICE-NOW URL]/api/now/table/incident?sysparm_display_value=true&number={0}'.format(ticket_no)
        print 'ICM URL', url
        logger.info('API URL: %s' % url)
        headers = {'Content-Type': 'application/json'}
        api_request = requests.get(url, auth=(username, password), headers=headers, verify=False)
        logger.info('get_today_itsm_incidents_status_code: %s' % api_request.status_code)
        api_response = api_request.json()
        print api_request
        return api_response
    except Exception as e:
        return e


def get_today_itsm_svr(ticket_no,username,password):
    try:
        url = 'https://[SERVICE-NOW URL]/api/now/table/u_request?sysparm_limit=1000&sysparm_display_value=true&number={0}'.format(ticket_no)
        logger.info('API URL: %s' % url)
        print 'API URL: %s' % url
        headers = {'Content-Type': 'application/json'}
        api_request = requests.get(url, auth=(username, password), headers=headers, verify=False)
        logger.info('get_today_itsm_svr_api_response_code: %r' % api_request.status_code)
        api_response = api_request.json()
        print 'STATUS_CODE', api_request.status_code
        return api_response
    except Exception as e:
        return e


def process_itsm_info(itsm_tickets):
    data = itsm_tickets
    # print ' process_itsm_data: ', data
    logger.info('itsm_tickets_data: %r' % data)
    itsm_dict = {}
    for incident in data.iteritems():
        for no_of_incidents in xrange(len(incident[1])):
            itsm_dict_info = {}
            itsm_incident_no = incident[1][no_of_incidents]['number']
            itsm_dict_info['opened_at'] = incident[1][no_of_incidents]['opened_at']
            itsm_dict_info['assignment_group'] = incident[1][no_of_incidents]['assignment_group']['display_value']
            itsm_dict_info['state'] = incident[1][no_of_incidents]['state']
            itsm_dict_info['sys_updated_on'] = incident[1][no_of_incidents]['sys_updated_on']
            itsm_dict_info['severity'] = incident[1][no_of_incidents]['severity']
            itsm_dict_info['short_description'] = incident[1][no_of_incidents]['short_description']
            work_notes = incident[1][no_of_incidents]['work_notes']
            # itsm_dict_info['comments'] = (incident[1][no_of_incidents]['comments'])[:500]
            itsm_dict_info['comments'] = work_notes[:1000]
            if incident[1][no_of_incidents]['opened_by']:
                itsm_dict_info['opened_by'] = incident[1][no_of_incidents]['opened_by']['display_value']
            else:
                itsm_dict_info['opened_by'] = 'Nobody'
            itsm_dict[itsm_incident_no] = itsm_dict_info
    logger.info('itsm_dict_RETURNED_PROCESS: %r' % itsm_dict)
    return itsm_dict


def process_itsm_svr_info(itsm_tickets):
    data = itsm_tickets
    # print 'DATA: ',itsm_tickets
    logger.info('process_itsm_svr_info_DATA: %r' % data)
    itsm_dict = {}
    for incident in data.iteritems():
        for no_of_incidents in xrange(len(incident[1])):
            itsm_dict_info = {}
            itsm_incident_no = incident[1][no_of_incidents]['number']
            itsm_dict_info['opened_at'] = incident[1][no_of_incidents]['opened_at']
            itsm_dict_info['assignment_group'] = incident[1][no_of_incidents]['assignment_group']['display_value']
            itsm_dict_info['state'] = incident[1][no_of_incidents]['state']
            itsm_dict_info['sys_updated_on'] = incident[1][no_of_incidents]['sys_updated_on']
            itsm_dict_info['impact'] = incident[1][no_of_incidents]['impact']
            itsm_dict_info['short_description'] = incident[1][no_of_incidents]['short_description']
            itsm_dict_info['comments'] = (incident[1][no_of_incidents]['comments'])[:500]
            itsm_dict_info['opened_by'] = incident[1][no_of_incidents]['opened_by']['display_value']
            itsm_dict[itsm_incident_no] = itsm_dict_info
    logger.info('process_itsm_svr_info_itsm_dict: %r' % itsm_dict)
    return itsm_dict


# def get_slack_tocken(SLACK_TOKEN):
#     try:
#         url = 'https://slack.com/api/rtm.connect'
#         # print url
#         logger.info('slack_token_URL: %s' % url)
#         slack_tocken = ConfigSectionMap('slackbot')['slack_tocken'].strip("'")
#         payload = {'token': '[YOUR TOKEN GOES HERE]'}
#         answer = requests.get(url, params=payload)
#         logger.info('get_slack_tocken_status_code: %s' % answer.status_code)
#         return answer.json()
#     except Exception as e:
#         logger.info('get_slack_tocken_ERROR: %r' % e)
#         return e

## instantiate logger
logger = setup_custom_logger('itsm_slack_integration')

## Slack BOT Auth Token
SLACK_TOKEN = ConfigSectionMap('slackbot')['slack_tocken'].strip("'")


#### GET ONLY THE ICM AND SVR ITSM TICKETS
# case_no_pattern = r'^(get-itsm)[ ](ICM|SVR)(\d{8}|\d{9}|\d{10}|\d{11}|\d{12})'
case_no_pattern = r'^(get-itsm)[ ](ICM|SVR)([0-9]+)$'

#### INSTANTIATE THE SLACK CLIENT
client = SlackClient(SLACK_TOKEN)


usr = ConfigSectionMap('itsm_creds')['username'].strip("'")
pwd = ConfigSectionMap('itsm_creds')['password'].strip("'")


def main():
    if client.rtm_connect():
        ##  WHILE CONNECTED TO SLACK WEBSOCKET
        while True:
            try:
                data_stream = client.rtm_read()
                print
                'SLACK_DATA_STREAM: ', data_stream
                ### CHECK THAT THE CONNECTION EXISTS -->MAYBE REMOVE??5-8-2017
                if data_stream:
                    ## CHECKT TO SEE IF KEY 'text' is in the dict, if so then somebody typed in the \
                    # slack channels that bot is listening
                    if 'text' in data_stream[0].keys():
                        print
                        'TEXT: ', data_stream[0]['text']
                        ### CHECK TXT TYPED IN SLACK CHANNEL AGAINST REGEX PATTERN
                        match = re.findall(case_no_pattern, data_stream[0]['text'])
                        logger.info('MATCH %r' % match)
                        print
                        match
                        ### IF WE GET A MATCH!!!
                        if match:
                            logger.info('DATA_STRM_WITH_MATCH %r' % data_stream)
                            print
                            'MATCH_MSG_KEYS: ', data_stream[0].keys()
                            logger.info('MATCH_MSG_KEYS %r' % data_stream[0].keys())
                            # print 'MATCH_TEXT', data_stream[0]['text']
                            logger.info('MATCH_TEXT %r' % data_stream[0]['text'])
                            # print '_MATCH_USER: ',data_stream[0]['user']
                            logger.info('MATCH_USER %r' % data_stream[0]['user'])
                            ticket_no = str(match[0][1] + match[0][2])
                            print
                            'TICKET_NO', ticket_no
                            # print 'TICKET_NO_MATCH',ticket_no
                            logger.info('TICKET_NO_MATCH %r' % ticket_no)
                            if 'ICM' in ticket_no:
                                thread = data_stream[0]['ts']
                                # print 'ICM_THREAD: ',thread
                                logger.info('ICM_THREAD %r' % thread)
                                my_channel = data_stream[0]['channel']
                                itsm_dict = get_today_itsm_incidents(ticket_no, usr, pwd)
                                print
                                'ITSM_DICT', itsm_dict.keys()
                                logger.info('ITSM_DICT %r' % itsm_dict)
                                if 'result' in itsm_dict.keys():
                                    itsm_info = process_itsm_info(itsm_dict)
                                    logger.info('itsm_info %r' % itsm_info)
                                    main_txt = ''
                                    msg = '''
                                        Date Opened: {0}\nopened_by: {1}\nSeverity: {2}
                                        '''.format(itsm_info[ticket_no]['opened_at'], itsm_info[ticket_no]['opened_by'],
                                                   itsm_info[ticket_no]['severity'])

                                    payload_raw = [{"fallback": ticket_no + itsm_info[ticket_no]['short_description'],
                                                    "pretext": ticket_no, \
                                                    "title": itsm_info[ticket_no]['short_description'], "text": msg,
                                                    "color": "#00e600", "fields": [
                                            {"title": "Assigned To", "value": itsm_info[ticket_no]['assignment_group'],
                                             "short": True}, \
                                            {"title": "Date Updated", "value": itsm_info[ticket_no]['sys_updated_on'],
                                             "short": True}, \
                                            {"title": "Comments", "value": itsm_info[ticket_no]['comments'],
                                             "short": False}], \
                                                    "footer": "2017 Prod Eng RD ITSM Slack Integration"}]
                                    x = make_slack_api_call(client, main_txt, thread, my_channel, payload_raw)
                                    print
                                    x
                                else:
                                    main_txt = ''
                                    msg = '''Could not find ticket Number %s''' % ticket_no
                                    payload_raw = [{"fallback": "No ticket found",
                                                    "pretext": ticket_no, \
                                                    "title": 'no ticket found', "text": msg,
                                                    "color": "#C62828", "fields": [
                                            {"title": "Comments", "value": 'Got nothing back for ' + ticket_no,
                                             "short": False}], "footer": "2017 Prod Eng RD ITSM Slack Integration"}]
                                    x = make_slack_api_call(client, main_txt, thread, my_channel, payload_raw)
                                    print
                                    x
                            elif 'SVR' in ticket_no:
                                logger.info('svr_ticket_no %r' % ticket_no)
                                thread = data_stream[0]['ts']
                                logger.info('SVR_THREAD %r' % thread)
                                my_channel = data_stream[0]['channel']
                                itsm_dict = get_today_itsm_svr(ticket_no, usr, pwd)
                                if 'result' in itsm_dict.keys():
                                    itsm_info = process_itsm_svr_info(itsm_dict)
                                    logger.info('SVR_ITSM_INFO %r' % itsm_info)
                                    main_txt = ''
                                    msg = '''
                                        Date Opened: {0}\nOpened By: {1}\nImpact: {2}
                                        '''.format(itsm_info[ticket_no]['opened_at'], itsm_info[ticket_no]['opened_by'],
                                                   itsm_info[ticket_no]['impact'])
                                    payload_raw = [{"fallback": ticket_no + itsm_info[ticket_no]['short_description'],
                                                    "pretext": ticket_no, \
                                                    "title": itsm_info[ticket_no]['short_description'], "text": msg,
                                                    "color": "#00e600",
                                                    "fields": [{"title": "Assigned To",
                                                                "value": itsm_info[ticket_no]['assignment_group'],
                                                                "short": True}, \
                                                               {"title": "Date Updated",
                                                                "value": itsm_info[ticket_no]['sys_updated_on'],
                                                                "short": True}, \
                                                               {"title": "Comments",
                                                                "value": itsm_info[ticket_no]['comments'], "short": False}], \
                                                    "footer": "2017 Prod Eng RD ITSM Slack Integration"}]
                                    send_slack_msg = make_slack_api_call(client, main_txt, thread, my_channel, payload_raw)
                                    logger.info('send_slack_msg_REPLY %r' % send_slack_msg)
                                else:
                                    main_txt = ''
                                    msg = '''Could not find ticket Number %s''' % ticket_no
                                    payload_raw = [{"fallback": "No ticket found",
                                                    "pretext": ticket_no, \
                                                    "title": 'no ticket found', "text": msg,
                                                    "color": "#C62828", "fields": [
                                            {"title": "Comments", "value": 'Got nothing back for ' + ticket_no,
                                             "short": False}], "footer": "[COPYRIGHT CAUSE WHY NOT]"}]
                                    x = make_slack_api_call(client, main_txt, thread, my_channel, payload_raw)
                                    print x

            except Exception as e:
                print 'Error: !!! %r' % e
                main()

            time.sleep(5)
    else:
        print
        "Connection Failed, invalid token?"
        logger.info('Connection Failed, invalid token? ')



if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        ticket_no = str(e)
        print 'MY ERROR:',e
        main()
