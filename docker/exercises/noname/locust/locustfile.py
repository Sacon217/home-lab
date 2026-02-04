from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def get_home(self):
        self.client.get("/")

locust -f locustfile.py --host=http://kong.nonamesec.org                                                                                                                   
