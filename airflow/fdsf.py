from db.dependencies import get_request_dao


def fetch_init_requests():
    dao = get_request_dao()
    requests = dao.get_all()
    
    return requests
    
    
print(fetch_init_requests())