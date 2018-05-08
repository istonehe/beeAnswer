

def make_error(status_code, sub_code, message, action):
    resp = {
        'error':{
            'status': status_code,
            'code': sub_code,
            'message': message,
            'action': action
        }
    }
    return resp
