import tornado.web
import tornado.ioloop
import requests
import json

# RootHandler is the default endpoint called and returns a default message
class RootHandler(tornado.web.RequestHandler):
    def get(self):
        body = {'message': 'hello world'}
        self.write(body)

# HealthCheckHandler is an endpoint that returns the status of the server, can be used as a monitoring endpoint
class HealthCheckHandler(tornado.web.RequestHandler):
    def initialize(self, slack_token):
        self.slack_token = slack_token
    def get(self):
        status, message, slack_team = self._checkhealth()
        body = {'status': '%s' % status, 'message': '%s' % message, 'slack_team': '%s' % slack_team}
        self.write(body)
    def _checkhealth(self):
        status = '503'
        message, slack_team = '', ''
        results = requests.get('https://slack.com/api/auth.test?token=%s' % self.slack_token)
        if results.json()['ok']:
            status = '200'
            slack_team = results.json()['team']
            message = "connected and authenticated with slack servers"
        return status, message, slack_team

class SlackMessageHandler(tornado.web.RequestHandler):
    def initialize(self, slack_token, api_key):
        self.slack_token = slack_token
        self.api_key = api_key
    def post(self):
        body = json.loads(self.request.body)
        if body.get('key') == self.api_key:
            payload = {
                'token':self.slack_token,
                'channel':body.get('channel'),
                'text':body.get('text'),
                'as_user':body.get('as_user')
            }  
            response = SlackPost(payload)
            status = '200'
            body = {'status': '%s' % status, 'response': '%s' % response}
        else:
            status = '401'
            body = {'status': '%s' % status}

        self.write(body)

def SlackPost(payload):
        response = requests.post('https://slack.com/api/chat.postMessage', payload)
        return response.json()

def Server(slack_token, api_key):
    routes = [
        (r"/", RootHandler),
        (r"/health", HealthCheckHandler, {'slack_token': slack_token}),
        (r"/slack/message", SlackMessageHandler, {'slack_token': slack_token, 'api_key': api_key}),
        (r"/(.*)", tornado.web.StaticFileHandler, {'path':'static'}) # cruft... TODO: implement a proper method of handling static files
    ]
    return tornado.web.Application(routes)

def Run(port, slack_token, api_key):
    server = Server(slack_token, api_key)
    server.listen(port)
    tornado.ioloop.IOLoop.current().start()