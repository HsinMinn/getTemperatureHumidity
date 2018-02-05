import math
import dateutil.parser
import datetime
import time
import os
import logging
import json
import boto3

client = boto3.client('iot-data', region_name='us-east-1')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
temperature = None

""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """

def publish_AWS_IoT(message):
    response = client.publish(
        topic='smart_home',
        qos=1,
        payload=json.dumps(
            message
        )
    )
    
def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')


def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False


def validate_getDHT(DHT, user_answer, volume):
    global temperature
    response = client.get_thing_shadow(
        thingName='zero_w2'
    )
    streamingBody = response["payload"]
    jsonState = json.loads(streamingBody.read())
    print("===============")
    temperature = str(jsonState['state']['reported']['temperature'])
    print(temperature)
    print("===============")
    if DHT == 'temperature' and user_answer is None and volume is None:
        
        
        publish_AWS_IoT('DHT/' + temperature)
        
        return build_validation_result(False,'Answer','The current temperature is ' + temperature + ' Celsius. Would you like to turn on the fan?')
        
    if user_answer == 'yes' and volume is None:
        #return build_validation_result(False,'volume','How\'s the air volume?')
        return build_validation_result(True, None, None)
    elif user_answer == 'no' and volume is None:
        return build_validation_result(True, None, None)
    """ 
    volume_types = ['strength','small','middle'] 
    if volume.lower() not in volume_types:
        return build_validation_result(False,'volume','your volume is not define.')
    """    
    return build_validation_result(True, None, None)


""" --- Functions that control the bot's behavior --- """


def getDHT(intent_request):
    """
    Performs dialog management and fulfillment for ordering flowers.
    Beyond fulfillment, the implementation of this intent demonstrates the use of the elicitSlot dialog action
    in slot validation and re-prompting.
    """
    DHT = get_slots(intent_request)["dht"]
    user_answer = get_slots(intent_request)["Answer"]
    volume = get_slots(intent_request)["volume"]
    source = intent_request['invocationSource']
    slots = get_slots(intent_request)

    if user_answer == 'no':
        return close(intent_request['sessionAttributes'],
            'Fulfilled',
            {
                'contentType': 'PlainText',
                'content': 'okay' 
            }
        )
    if source == 'DialogCodeHook':
        #validation_result = validate_getDHT()
        if DHT == 'temperature':
            validation_result = validate_getDHT(DHT, user_answer, volume)
            if not validation_result['isValid']:
                slots[validation_result['violatedSlot']] = None
                return elicit_slot(intent_request['sessionAttributes'],intent_request['currentIntent']['name'],slots,validation_result['violatedSlot'],validation_result['message'])
            """
            output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
            global temperature
            if (int(temperature)) >= 28:
                output_session_attributes['time'] = '30'        
            elif (int(temperature)) < 28:
                output_session_attributes['time'] = '10'
            return delegate(output_session_attributes, get_slots(intent_request))
            """
            
    publish_AWS_IoT('fan/' + '1')
    return close(intent_request['sessionAttributes'],
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'okay' 
        }
    )
    
        

""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    
    return getDHT(intent_request)
    
    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    return dispatch(event)