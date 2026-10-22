import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gateway'))
from install_lan210 import validate_route
class LANTests(unittest.TestCase):
    def test_direct_lan_accepted(self):
        self.assertEqual(validate_route([{'dev':'wlp3s0','prefsrc':'192.168.4.13'}]),('wlp3s0','192.168.4.13'))
    def test_old_mesh_subnet_refused(self):
        with self.assertRaises(RuntimeError):validate_route([{'dev':'wlp3s0','prefsrc':'192.168.2.210','gateway':'192.168.2.1'}])
    def test_indirect_lan_refused(self):
        with self.assertRaises(RuntimeError):validate_route([{'dev':'wlp3s0','prefsrc':'192.168.4.13','gateway':'192.168.4.2'}])

    def test_failed_install_restores_files_and_added_alias(self):
        import contextlib,io,json,tempfile,types
        from unittest.mock import patch
        import install_lan210 as installer
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);unit=root/'alice-p52.service';unit.write_text('old unit')
            dest=root/'app';dest.mkdir();(dest/'alice_gateway.py').write_text('old source')
            calls=[]
            def fake_run(*args,**kwargs):
                calls.append(args)
                if args[:5]==('ip','-j','-4','route','get'):return json.dumps([{'dev':'wlp3s0','prefsrc':'192.168.4.13'}])
                if args[:4]==('ip','-j','-4','address'):return json.dumps([{'addr_info':[{'local':'192.168.4.13'}]}])
                if args[:3]==('nmcli','-g','GENERAL.CON-UUID'):return 'real-profile-uuid'
                if args[:3]==('nmcli','-g','ipv4.addresses'):return ''
                if args==('ufw','status'):return 'Status: active'
                if args[:2]==('ufw','allow'):return 'Skipping adding existing rule'
                if args[:2]==('systemctl','is-active'):return 'active'
                if args[:2]==('systemctl','is-enabled'):return 'enabled'
                return ''
            def fake_health(url):
                if '127.0.0.1' not in url:raise RuntimeError('health failed')
            with patch.multiple(installer,DEST=dest,UNIT=unit,SITE=root/'nginx.conf',BACKUPS=root/'backup',ROUTES=root/'routes.json'),patch.object(installer,'run',side_effect=fake_run),patch.object(installer.shutil,'which',return_value='/usr/bin/tool'),patch.object(installer.subprocess,'run',return_value=types.SimpleNamespace(returncode=0)),patch.object(installer.os,'geteuid',return_value=0),patch.object(installer.time,'sleep'),patch.object(installer,'health',side_effect=fake_health),patch.object(sys,'argv',['install_lan210.py']),contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(RuntimeError,'health failed'):installer.main()
            self.assertEqual(unit.read_text(),'old unit')
            self.assertEqual((dest/'alice_gateway.py').read_text(),'old source')
            self.assertFalse((dest/'smart_route.py').exists());self.assertFalse((root/'nginx.conf').exists());self.assertFalse((root/'routes.json').exists())
            self.assertIn(('nmcli','connection','modify','uuid','real-profile-uuid','-ipv4.addresses','192.168.4.210/24'),calls)
            self.assertNotIn(('systemctl','stop','alice-gateway'),calls)
            self.assertFalse(any(call[:3]==('ufw','--force','delete') for call in calls),'never remove an existing firewall rule')
