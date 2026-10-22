import http.server,json,os,sys,tempfile,threading,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gateway'))
from smart_route import SmartRouter,RouteError
import alice_gateway

class ModelHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def do_POST(self):
        n=int(self.headers.get('Content-Length','0'))
        data=json.loads(self.rfile.read(n))
        if self.server.failure:
            self.send_response(503);self.end_headers();return
        self.server.received.append(data)
        payload=json.dumps({'choices':[{'message':{'content':'Nên đo độ trễ, kiểm tra thiết bị tải lớn.'}}]}).encode()
        self.send_response(200);self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)

class SmartRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fail=http.server.ThreadingHTTPServer(('127.0.0.1',0),ModelHandler)
        cls.fail.failure=True;cls.fail.received=[]
        cls.good=http.server.ThreadingHTTPServer(('127.0.0.1',0),ModelHandler)
        cls.good.failure=False;cls.good.received=[]
        for s in (cls.fail,cls.good):threading.Thread(target=s.serve_forever,daemon=True).start()
    @classmethod
    def tearDownClass(cls):
        cls.fail.shutdown();cls.fail.server_close();cls.good.shutdown();cls.good.server_close()
    def config(self,entries):
        tmp=tempfile.TemporaryDirectory()
        f=Path(tmp.name)/'routes.json'
        f.write_text(json.dumps({'providers':entries,'max_output_tokens':120,'cooldown_seconds':30,'timeout_seconds':2}))
        return tmp,SmartRouter(str(f))
    def item(self,server,name,priority):
        return {'name':name,'model':'mock-network','enabled':True,'priority':priority,
                'url':f'http://127.0.0.1:{server.server_port}/v1/chat/completions'}
    def test_failover_and_circuit_breaker(self):
        self.good.received.clear()
        tmp,router=self.config([self.item(self.fail,'bad',1),self.item(self.good,'good',2)])
        with tmp:
            for _ in range(3):
                result=router.complete('wifi yếu',[{'role':'user','content':'wifi yếu'}])
                self.assertEqual(result['provider'],'good')
            status=router.public_status()
            self.assertEqual(status['providers'][0]['status'],'cooldown')
            self.assertEqual(len(self.good.received),3)
            self.assertEqual(self.good.received[0]['messages'][0]['role'],'system')
            self.assertNotIn('snapshot',str(self.good.received[0]))
    def test_offline_when_none(self):
        tmp,router=self.config([])
        with tmp:
            self.assertIsNone(router.complete('hello'))
            self.assertEqual(router.public_status()['mode'],'offline-rules')
    def test_remote_requires_explicit_tls_allowlist(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'providers.json'
            p.write_text(json.dumps({'providers':[{'name':'a','model':'b','enabled':True,
                         'url':'http://192.168.4.1/v1/chat/completions'}]}))
            router=SmartRouter(p)
            self.assertEqual(router.public_status()['configured_count'],0)
            self.assertTrue(router.public_status()['last_config_error'])
            with self.assertRaises(RouteError):router.reload()
    def test_no_secret_exposure(self):
        tmp,router=self.config([self.item(self.good,'good',1)])
        with tmp:
            os.environ['ALICE_SECRET_KEY']='test-example-secret'
            status=str(router.public_status())
            self.assertNotIn('ALICE_SECRET_KEY',status)
            self.assertNotIn('test-example-secret',status)
    def test_hourly_budget_falls_back(self):
        tmp,router=self.config([self.item(self.good,'good',1)])
        with tmp:
            router.config['hourly_request_limit']=1
            self.assertIsNotNone(router.complete('wifi yếu'))
            self.assertIsNone(router.complete('wifi yếu'))
            self.assertEqual(router.public_status()['hourly_calls_used'],1)
    def test_gateway_response_fallback(self):
        original=alice_gateway.SMART
        try:
            tmp,router=self.config([])
            with tmp:
                alice_gateway.SMART=router
                result=alice_gateway.respond({'message':'wifi yếu'})
                self.assertEqual(result['source'],'offline-rules')
                self.assertFalse(result['router_config_changed'])
        finally:alice_gateway.SMART=original
    def test_gateway_response_model(self):
        original=alice_gateway.SMART
        try:
            tmp,router=self.config([self.item(self.good,'good',1)])
            with tmp:
                alice_gateway.SMART=router
                result=alice_gateway.respond({'message':'mạng nhà bị nghẽn'})
                self.assertEqual(result['source'],'smart-route:good')
                self.assertIn('độ trễ',result['message'])
                self.assertFalse(result['router_config_changed'])
        finally:alice_gateway.SMART=original


    def test_context_history_and_secrets(self):
        self.good.received.clear()
        tmp,router=self.config([self.item(self.good,'good',1)])
        with tmp:
            snapshot=alice_gateway.sanitize_snapshot({'cpu':0,'memory':40,'configuration':{'ppa':34,'password':'secret'},'clients':[{'ip':'192.168.4.13','tx_kbps':100,'rx_kbps':200,'sessions':None}],'token':'secret'})
            answer=router.complete('vậy nên làm gì?',[{'role':'user','content':'wifi mất mạng'},{'role':'assistant','content':'Kiểm tra WAN'}],snapshot)
            self.assertTrue(answer['context_available'])
            payload=str(self.good.received[-1])
            self.assertIn('cpu_percent',payload);self.assertIn('wifi mất mạng',payload)
            self.assertNotIn('192.168.4.13',payload);self.assertNotIn('secret',payload)
    def test_attempt_budget_counts_failed_provider(self):
        tmp,router=self.config([self.item(self.fail,'bad',1),self.item(self.good,'good',2)])
        with tmp:
            router.config['hourly_request_limit']=1
            self.assertIsNone(router.complete('test'))
            self.assertEqual(router.public_status()['hourly_calls_used'],1)
            self.assertEqual(router.public_status()['providers'][1]['attempt_count'],0)
    def test_429_wait_and_total_deadline(self):
        import urllib.error
        from unittest.mock import patch
        clock=[100.0]
        tmp,router=self.config([self.item(self.fail,'bad',1),self.item(self.good,'good',2)])
        with tmp:
            router.clock=lambda:clock[0]
            def fail(provider,*args,**kwargs):
                clock[0]+=1
                if provider['name']=='bad':raise urllib.error.HTTPError(provider['url'],429,'rate',{'Retry-After':'120'},None)
                return 'ok',5
            with patch.object(router,'_request',side_effect=fail):
                self.assertEqual(router.complete('q')['provider'],'good')
                status=router.public_status();self.assertEqual(status['providers'][0]['error_class'],'rate_limit')
                self.assertGreaterEqual(status['providers'][0]['retry_in_seconds'],119)
            router.status_map['bad']['blocked_until']=0;router.config['total_timeout_seconds']=1
            def slow(*args,**kwargs):clock[0]+=2;raise TimeoutError()
            before=router.status_map['good']['attempts']
            with patch.object(router,'_request',side_effect=slow):self.assertIsNone(router.complete('q'))
            self.assertEqual(router.status_map['good']['attempts'],before)
    def test_health_does_not_claim_unverified_model_ready(self):
        tmp,router=self.config([self.item(self.good,'good',1)])
        with tmp:
            self.assertFalse(router.public_status()['inference_verified'])
            router.complete('q')
            self.assertTrue(router.public_status()['inference_verified'])
    def test_stale_snapshot_rejected_and_no_fake_zero(self):
        import datetime
        old=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(minutes=10)).isoformat()
        self.assertIsNone(alice_gateway.sanitize_snapshot({'time':old,'cpu':70}))
        obj=alice_gateway.sanitize_snapshot({'cpu':0,'memory':40})
        self.assertEqual(obj['cpu'],0);self.assertFalse(obj['client_data_present'])
    def test_lan210_cors_and_chat(self):
        import urllib.request,urllib.error
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),alice_gateway.Handler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        base='http://127.0.0.1:'+str(server.server_port)
        try:
            req=urllib.request.Request(base+'/alice-api/health',headers={'Origin':'http://192.168.4.210'})
            with urllib.request.urlopen(req) as response:
                self.assertEqual(response.headers['Access-Control-Allow-Origin'],'http://192.168.4.210')
                self.assertTrue(json.load(response)['ok'])
            req=urllib.request.Request(base+'/alice-api/health',headers={'Origin':'http://untrusted.example'})
            with self.assertRaises(urllib.error.HTTPError) as ctx:urllib.request.urlopen(req)
            self.assertEqual(ctx.exception.code,403)
            with urllib.request.urlopen(base+'/') as response:self.assertIn('ALICE',response.read().decode())
        finally:server.shutdown();server.server_close()

if __name__=='__main__':unittest.main()
